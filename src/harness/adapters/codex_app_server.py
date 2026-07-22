"""Synchronous Codex App Server adapter with an injectable JSON-RPC transport.

The raw App Server JSON-RPC/JSONL protocol is intentionally confined to this
module.  Callers receive only provider-neutral adapter contracts from
``harness.adapters.base``.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, TextIO, cast

from harness.adapters.base import (
    AdapterIdentity,
    ApprovalRequest,
    ApprovalResponse,
    ProviderAdapterError,
    ProviderErrorCategory,
    ProviderEvent,
    ProviderEventKind,
    ProviderFailure,
    ProviderTurnOutcome,
    SessionHandle,
    TurnHandle,
    TurnRequest,
)
from harness.state import ActionClass

SUPPORTED_PROTOCOL_VERSION = "app-server-v2"
SCHEMA_REF = "docs/research/generated-app-server-schema/codex-cli-0.144.3/stable"

JSON = Mapping[str, Any]


class CodexAppServerTransport(Protocol):
    """Minimal synchronous JSON-RPC transport used by the adapter."""

    @property
    def started(self) -> bool:
        """Return whether the transport is running."""

    def start(self) -> None:
        """Start the underlying transport."""

    def stop(self) -> None:
        """Stop the underlying transport."""

    def request(self, method: str, params: JSON) -> JSON:
        """Send one JSON-RPC request and return its result object."""

    def iter_events(self, *, turn_id: str) -> Iterator[JSON]:
        """Yield raw provider events for one turn until a terminal/blocked segment."""


class SubprocessJsonRpcTransport:
    """Standard-library subprocess/JSONL JSON-RPC transport.

    This transport is deliberately small and injectable.  Unit tests pass a fake
    transport, so constructing this class is the only place that can start the
    real Codex App Server process.
    """

    def __init__(self, command: Sequence[str]) -> None:
        if not command:
            raise ValueError("command must not be empty")
        self._command = tuple(command)
        self._process: subprocess.Popen[str] | None = None
        self._next_id = 0

    @property
    def started(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self) -> None:
        if self.started:
            return
        self._process = subprocess.Popen(  # noqa: S603 - caller supplies pinned command.
            self._command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

    def stop(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def request(self, method: str, params: JSON) -> JSON:
        process = self._require_process()
        stdin = cast(TextIO, process.stdin)
        stdout = cast(TextIO, process.stdout)
        self._next_id += 1
        request_id = self._next_id
        stdin.write(
            json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
            + "\n"
        )
        stdin.flush()
        while True:
            line = stdout.readline()
            if line == "":
                raise _adapter_error(
                    "transport closed", ProviderErrorCategory.TRANSIENT, retryable=True
                )
            message = _object(json.loads(line), "json-rpc response")
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = _object(message["error"], "json-rpc error")
                raise _adapter_error(
                    _string(error.get("message"), "json-rpc error.message"),
                    _category_from_code(error.get("code")),
                    retryable=False,
                    provider_code=str(error.get("code", "json_rpc_error")),
                )
            return _object(message.get("result"), "json-rpc result")

    def iter_events(self, *, turn_id: str) -> Iterator[JSON]:
        process = self._require_process()
        stdout = cast(TextIO, process.stdout)
        while True:
            line = stdout.readline()
            if line == "":
                raise _adapter_error(
                    "transport closed",
                    ProviderErrorCategory.TRANSIENT,
                    retryable=True,
                    correlation_id=turn_id,
                )
            message = _object(json.loads(line), "stream message")
            if message.get("turn_id") == turn_id:
                yield message

    def _require_process(self) -> subprocess.Popen[str]:
        if not self.started or self._process is None:
            raise _adapter_error(
                "transport is not started", ProviderErrorCategory.STATE, retryable=False
            )
        return self._process


@dataclass(slots=True)
class _TurnState:
    handle: TurnHandle
    terminal: bool = False
    waiting_approval: str | None = None
    next_sequence: int = 1
    emitted_ids: set[str] = field(default_factory=set)


class CodexAppServerAdapter:
    """ProviderAdapter implementation for the Codex App Server protocol."""

    def __init__(self, transport: CodexAppServerTransport) -> None:
        self._transport = transport
        self._identity = AdapterIdentity(
            adapter="codex_app_server",
            provider="codex",
            implementation_version="c501-local",
            protocol_version=SUPPORTED_PROTOCOL_VERSION,
            schema_ref=SCHEMA_REF,
        )
        self._preflighted = False
        self._sessions: dict[str, SessionHandle] = {}
        self._turns: dict[str, _TurnState] = {}
        self._request_ids: set[str] = set()

    @property
    def identity(self) -> AdapterIdentity:
        return self._identity

    @property
    def started(self) -> bool:
        return self._transport.started

    def start(self) -> AdapterIdentity:
        self._transport.start()
        return self._identity

    def stop(self) -> None:
        self._transport.stop()
        self._preflighted = False

    def preflight(self) -> AdapterIdentity:
        self._require_started()
        result = self._request(
            "server.compatibility", {"required_protocol": SUPPORTED_PROTOCOL_VERSION}
        )
        protocol = _string(result.get("protocol_version"), "compatibility.protocol_version")
        if protocol != SUPPORTED_PROTOCOL_VERSION:
            raise _adapter_error(
                f"incompatible Codex App Server protocol {protocol!r}",
                ProviderErrorCategory.COMPATIBILITY,
                retryable=False,
                provider_code="incompatible_protocol",
            )
        mandatory = result.get("mandatory_capabilities", ())
        if not isinstance(mandatory, list) or not all(isinstance(item, str) for item in mandatory):
            raise _adapter_error(
                "malformed mandatory capabilities", ProviderErrorCategory.PROTOCOL, retryable=False
            )
        required = {"initialize", "thread", "turn", "approval", "cancel", "interrupt", "stream"}
        missing = required.difference(mandatory)
        if missing:
            raise _adapter_error(
                f"missing mandatory capabilities: {', '.join(sorted(missing))}",
                ProviderErrorCategory.COMPATIBILITY,
                retryable=False,
                provider_code="missing_capability",
            )
        self._preflighted = True
        return self._identity

    def create_session(self, *, run: Any) -> SessionHandle:
        self._require_ready_run(run)
        result = self._request("thread.start", {"run_id": run.run_id, "model": run.model})
        session = SessionHandle(
            session_id=_stable_id(result.get("thread_id"), "thread.thread_id"),
            run_id=run.run_id,
            provider="codex",
        )
        self._sessions[session.session_id] = session
        return session

    def resume_session(self, *, run: Any, session_id: str) -> SessionHandle:
        self._require_ready_run(run)
        result = self._request("thread.resume", {"run_id": run.run_id, "thread_id": session_id})
        returned = _stable_id(result.get("thread_id"), "thread.thread_id")
        if returned != session_id:
            raise _adapter_error(
                "resumed thread identity mismatch", ProviderErrorCategory.PROTOCOL, retryable=False
            )
        session = SessionHandle(session_id=session_id, run_id=run.run_id, provider="codex")
        self._sessions[session.session_id] = session
        return session

    def submit_turn(self, *, session: SessionHandle, request: TurnRequest) -> TurnHandle:
        self._require_session(session)
        if request.run.provider != "codex":
            raise _adapter_error(
                "run provider must be codex", ProviderErrorCategory.STATE, retryable=False
            )
        if session.run_id != request.run.run_id:
            raise _adapter_error(
                "session/run mismatch", ProviderErrorCategory.STATE, retryable=False
            )
        if request.request_id in self._request_ids:
            raise _adapter_error(
                "duplicate request id", ProviderErrorCategory.STATE, retryable=False
            )
        result = self._request(
            "turn.submit",
            {
                "thread_id": session.session_id,
                "request_id": request.request_id,
                "instructions": request.instructions,
                "input_refs": list(request.input_refs),
            },
        )
        turn = TurnHandle(
            turn_id=_stable_id(result.get("turn_id"), "turn.turn_id"),
            session_id=session.session_id,
            request_id=request.request_id,
            run_id=request.run.run_id,
            task_id=request.task.task_id,
        )
        self._request_ids.add(request.request_id)
        self._turns[turn.turn_id] = _TurnState(handle=turn)
        return turn

    def stream_events(self, *, turn: TurnHandle) -> Iterator[ProviderEvent]:
        state = self._require_turn(turn)
        if state.terminal:
            return iter(())
        return self._stream(state)

    def respond_to_approval(self, *, turn: TurnHandle, response: ApprovalResponse) -> None:
        state = self._require_turn(turn)
        if state.terminal:
            raise _adapter_error("turn is terminal", ProviderErrorCategory.STATE, retryable=False)
        if state.waiting_approval != response.approval_id:
            raise _adapter_error(
                "approval id mismatch", ProviderErrorCategory.STATE, retryable=False
            )
        self._request(
            "approval.respond",
            {
                "turn_id": turn.turn_id,
                "approval_id": response.approval_id,
                "decision": response.decision.value,
                "reason": response.reason,
                "evidence_refs": list(response.evidence_refs),
            },
        )
        state.waiting_approval = None

    def interrupt(self, *, turn: TurnHandle, reason: str) -> None:
        state = self._require_turn(turn)
        if state.terminal:
            raise _adapter_error("turn is terminal", ProviderErrorCategory.STATE, retryable=False)
        self._request(
            "turn.interrupt", {"turn_id": turn.turn_id, "reason": _non_empty(reason, "reason")}
        )

    def cancel(self, *, session: SessionHandle, reason: str) -> None:
        self._require_session(session)
        self._request(
            "thread.cancel",
            {"thread_id": session.session_id, "reason": _non_empty(reason, "reason")},
        )

    def _stream(self, state: _TurnState) -> Iterator[ProviderEvent]:
        for raw in self._transport.iter_events(turn_id=state.handle.turn_id):
            event = self._translate_event(state, raw)
            yield event
            if (
                event.kind is ProviderEventKind.APPROVAL_REQUIRED
                or event.kind is ProviderEventKind.TURN_TERMINAL
            ):
                break

    def _translate_event(self, state: _TurnState, raw: JSON) -> ProviderEvent:
        self._reject_unknown_mandatory(raw)
        event_id = _stable_id(raw.get("event_id"), "event.event_id")
        if event_id in state.emitted_ids:
            raise _adapter_error(
                "duplicate provider event id",
                ProviderErrorCategory.PROTOCOL,
                retryable=False,
                correlation_id=state.handle.turn_id,
            )
        sequence = _int(raw.get("sequence"), "event.sequence")
        if sequence != state.next_sequence:
            raise _adapter_error(
                "provider event sequence gap",
                ProviderErrorCategory.PROTOCOL,
                retryable=False,
                correlation_id=state.handle.turn_id,
            )
        timestamp = _timestamp(raw.get("timestamp"))
        kind_value = _string(raw.get("type"), "event.type")
        state.emitted_ids.add(event_id)
        state.next_sequence += 1
        summary = _non_empty(str(raw.get("summary", kind_value)), "event.summary")
        input_refs = _tuple(raw.get("input_refs", ()), "event.input_refs")
        output_refs = _tuple(raw.get("output_refs", ()), "event.output_refs")
        evidence_refs = _tuple(raw.get("evidence_refs", ()), "event.evidence_refs")
        correlation_id_value = raw.get("correlation_id")
        correlation_id = (
            None
            if correlation_id_value is None
            else _stable_id(correlation_id_value, "event.correlation_id")
        )

        def normalized_event(
            kind: ProviderEventKind,
            *,
            approval: ApprovalRequest | None = None,
            outcome: ProviderTurnOutcome | None = None,
            failure: ProviderFailure | None = None,
        ) -> ProviderEvent:
            return ProviderEvent(
                event_id=event_id,
                sequence=sequence,
                timestamp=timestamp,
                session_id=state.handle.session_id,
                turn_id=state.handle.turn_id,
                kind=kind,
                summary=summary,
                input_refs=input_refs,
                output_refs=output_refs,
                evidence_refs=evidence_refs,
                correlation_id=correlation_id,
                approval=approval,
                outcome=outcome,
                failure=failure,
            )

        if kind_value == "turn.started":
            return normalized_event(ProviderEventKind.TURN_STARTED)
        if kind_value == "message.output":
            return normalized_event(ProviderEventKind.OUTPUT)
        if kind_value == "action.started":
            return normalized_event(ProviderEventKind.ACTION)
        if kind_value == "approval.required":
            approval = _object(raw.get("approval"), "event.approval")
            approval_request = ApprovalRequest(
                approval_id=_stable_id(approval.get("approval_id"), "approval.approval_id"),
                action_class=_action_class(
                    _string(approval.get("action_class"), "approval.action_class")
                ),
                summary=_string(approval.get("summary"), "approval.summary"),
                input_refs=_tuple(approval.get("input_refs", ()), "approval.input_refs"),
            )
            state.waiting_approval = approval_request.approval_id
            return normalized_event(ProviderEventKind.APPROVAL_REQUIRED, approval=approval_request)
        if kind_value == "turn.completed":
            state.terminal = True
            return normalized_event(
                ProviderEventKind.TURN_TERMINAL, outcome=ProviderTurnOutcome.SUCCEEDED
            )
        if kind_value in {"turn.failed", "turn.cancelled", "turn.interrupted"}:
            state.terminal = True
            if kind_value == "turn.cancelled":
                return normalized_event(
                    ProviderEventKind.TURN_TERMINAL, outcome=ProviderTurnOutcome.CANCELLED
                )
            if kind_value == "turn.interrupted":
                return normalized_event(
                    ProviderEventKind.TURN_TERMINAL, outcome=ProviderTurnOutcome.INTERRUPTED
                )
            failure = _failure(raw.get("failure"), state.handle.turn_id)
            return normalized_event(
                ProviderEventKind.TURN_TERMINAL,
                outcome=ProviderTurnOutcome.FAILED,
                failure=failure,
            )
        raise _adapter_error(
            f"unknown mandatory provider event type {kind_value!r}",
            ProviderErrorCategory.PROTOCOL,
            retryable=False,
            correlation_id=state.handle.turn_id,
        )

    def _request(self, method: str, params: JSON) -> JSON:
        self._require_started()
        try:
            result = self._transport.request(method, params)
        except ProviderAdapterError:
            raise
        except Exception as exc:
            raise _adapter_error(str(exc), ProviderErrorCategory.TRANSIENT, retryable=True) from exc
        self._reject_unknown_mandatory(result)
        return result

    def _require_started(self) -> None:
        if not self.started:
            raise _adapter_error(
                "adapter is not started", ProviderErrorCategory.STATE, retryable=False
            )

    def _require_ready_run(self, run: Any) -> None:
        self._require_started()
        if not self._preflighted:
            raise _adapter_error(
                "preflight is required", ProviderErrorCategory.STATE, retryable=False
            )
        if getattr(run, "provider", None) != "codex":
            raise _adapter_error(
                "run provider must be codex", ProviderErrorCategory.STATE, retryable=False
            )

    def _require_session(self, session: SessionHandle) -> None:
        self._require_started()
        if session.provider != "codex" or self._sessions.get(session.session_id) != session:
            raise _adapter_error(
                "unknown Codex session", ProviderErrorCategory.STATE, retryable=False
            )

    def _require_turn(self, turn: TurnHandle) -> _TurnState:
        self._require_started()
        state = self._turns.get(turn.turn_id)
        if state is None or state.handle != turn:
            raise _adapter_error("unknown Codex turn", ProviderErrorCategory.STATE, retryable=False)
        return state

    def _reject_unknown_mandatory(self, raw: JSON) -> None:
        unknown = raw.get("unknown_mandatory")
        if unknown not in (None, [], ()):  # forward-compatible optional fields are allowed.
            raise _adapter_error(
                "unknown mandatory protocol field", ProviderErrorCategory.PROTOCOL, retryable=False
            )


def _adapter_error(
    message: str,
    category: ProviderErrorCategory,
    *,
    retryable: bool,
    provider_code: str | None = None,
    correlation_id: str | None = None,
) -> ProviderAdapterError:
    return ProviderAdapterError(
        message,
        category=category,
        retryable=retryable,
        provider_code=provider_code,
        correlation_id=correlation_id,
    )


def _object(value: Any, location: str) -> JSON:
    if not isinstance(value, Mapping):
        raise _adapter_error(
            f"{location} must be an object", ProviderErrorCategory.PROTOCOL, retryable=False
        )
    return value


def _string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _adapter_error(
            f"{location} must be a normalized non-empty string",
            ProviderErrorCategory.PROTOCOL,
            retryable=False,
        )
    return value


def _stable_id(value: Any, location: str) -> str:
    return _string(value, location)


def _non_empty(value: str, location: str) -> str:
    return _string(value, location)


def _int(value: Any, location: str) -> int:
    if not isinstance(value, int) or value < 1:
        raise _adapter_error(
            f"{location} must be a positive integer",
            ProviderErrorCategory.PROTOCOL,
            retryable=False,
        )
    return value


def _timestamp(value: Any) -> datetime:
    if value is None:
        raise _adapter_error(
            "event.timestamp is required", ProviderErrorCategory.PROTOCOL, retryable=False
        )
    try:
        parsed = datetime.fromisoformat(_string(value, "event.timestamp"))
    except ValueError as exc:
        raise _adapter_error(
            "event.timestamp must be ISO-8601", ProviderErrorCategory.PROTOCOL, retryable=False
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _adapter_error(
            "event.timestamp must be timezone-aware",
            ProviderErrorCategory.PROTOCOL,
            retryable=False,
        )
    return parsed.astimezone(UTC)


def _tuple(value: Any, location: str) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        raise _adapter_error(
            f"{location} must be a list", ProviderErrorCategory.PROTOCOL, retryable=False
        )
    items: list[str] = []
    for index, item in enumerate(value):
        items.append(_string(item, f"{location}[{index}]"))
    return tuple(items)


def _action_class(value: str) -> ActionClass:
    try:
        return ActionClass(value)
    except ValueError as exc:
        raise _adapter_error(
            "unknown approval action class", ProviderErrorCategory.PROTOCOL, retryable=False
        ) from exc


def _failure(value: Any, turn_id: str) -> ProviderFailure:
    raw = _object(value, "failure")
    category = _category_from_code(raw.get("category"))
    if category is ProviderErrorCategory.STATE:
        category = ProviderErrorCategory.PROTOCOL
    return ProviderFailure(
        category=category,
        message=_string(raw.get("message"), "failure.message"),
        retryable=bool(raw.get("retryable", False)),
        provider_code=str(raw.get("code", "provider_failure")),
        correlation_id=turn_id,
    )


def _category_from_code(value: Any) -> ProviderErrorCategory:
    if value == "compatibility":
        return ProviderErrorCategory.COMPATIBILITY
    if value == "protocol":
        return ProviderErrorCategory.PROTOCOL
    if value == "transient":
        return ProviderErrorCategory.TRANSIENT
    if value == "permanent":
        return ProviderErrorCategory.PERMANENT
    if value == "state":
        return ProviderErrorCategory.STATE
    return ProviderErrorCategory.PERMANENT


__all__ = [
    "CodexAppServerAdapter",
    "CodexAppServerTransport",
    "SubprocessJsonRpcTransport",
    "SCHEMA_REF",
    "SUPPORTED_PROTOCOL_VERSION",
]
