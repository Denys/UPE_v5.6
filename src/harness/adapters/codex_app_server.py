"""Codex App Server adapter bound to the generated JSON-RPC schema.

Raw App Server request, response, notification, and server-request envelopes are
confined to this module.  The harness-facing surface remains the provider-neutral
``harness.adapters.base`` contract.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import deque
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
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
from harness.state import ActionClass, ApprovalStatus, RedactionStatus

EXPECTED_CODEX_CLI_VERSION = "0.144.3"
APP_SERVER_PROTOCOL_VERSION = "codex-app-server-jsonrpc-v2"
SCHEMA_REF = "docs/research/generated-app-server-schema/codex-cli-0.144.3/stable"
CLIENT_NAME = "upe-harness-c501"
CLIENT_VERSION = "0.1.0"

JSON = Mapping[str, Any]
RpcId = str | int
_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class InboundKind(StrEnum):
    RESPONSE = "response"
    NOTIFICATION = "notification"
    SERVER_REQUEST = "server_request"


@dataclass(frozen=True, slots=True)
class InboundMessage:
    """Parsed JSON-RPC message from the App Server."""

    kind: InboundKind
    method: str | None = None
    params: JSON | None = None
    request_id: RpcId | None = None
    result: JSON | None = None
    error: JSON | None = None


class CodexAppServerTransport(Protocol):
    """Injectable synchronous JSON-RPC/JSONL transport."""

    @property
    def started(self) -> bool: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def request(self, method: str, params: JSON) -> JSON: ...

    def notify(self, method: str, params: JSON | None = None) -> None: ...

    def respond(self, request_id: RpcId, result: JSON) -> None: ...

    def iter_messages(self) -> Iterator[InboundMessage]: ...


class SubprocessJsonRpcTransport:
    """Strict standard-library JSONL JSON-RPC transport for Codex App Server."""

    def __init__(self, command: Sequence[str]) -> None:
        if not command:
            raise ValueError("command must not be empty")
        self._command = tuple(command)
        self._process: subprocess.Popen[str] | None = None
        self._next_id = 0
        self._pending: deque[InboundMessage] = deque()

    @property
    def started(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self) -> None:
        if self.started:
            return
        try:
            self._process = subprocess.Popen(  # noqa: S603 - caller supplies pinned binary.
                self._command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except OSError as exc:
            raise _error(
                f"failed to start Codex App Server: {exc}",
                ProviderErrorCategory.PERMANENT,
                retryable=False,
                provider_code="startup_failure",
            ) from exc

    def stop(self) -> None:
        process = self._process
        self._process = None
        self._pending.clear()
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    def request(self, method: str, params: JSON) -> JSON:
        self._next_id += 1
        request_id = self._next_id
        self._write({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        while True:
            message = self._read_message()
            if message.kind is not InboundKind.RESPONSE or message.request_id != request_id:
                self._pending.append(message)
                continue
            if message.error is not None:
                raise _rpc_error(message.error)
            if message.result is None:
                raise _error("JSON-RPC response missing result", ProviderErrorCategory.PROTOCOL)
            return message.result

    def notify(self, method: str, params: JSON | None = None) -> None:
        envelope: dict[str, object] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            envelope["params"] = params
        self._write(envelope)

    def respond(self, request_id: RpcId, result: JSON) -> None:
        self._write({"jsonrpc": "2.0", "id": request_id, "result": result})

    def iter_messages(self) -> Iterator[InboundMessage]:
        while True:
            if self._pending:
                yield self._pending.popleft()
            else:
                yield self._read_message()

    def _write(self, envelope: JSON) -> None:
        process = self._require_process()
        if process.poll() is not None:
            raise self._process_exit_error(process)
        stdin = cast(TextIO, process.stdin)
        stdin.write(json.dumps(envelope, separators=(",", ":")) + "\n")
        stdin.flush()

    def _read_message(self) -> InboundMessage:
        process = self._require_process()
        if process.poll() is not None:
            raise self._process_exit_error(process)
        stdout = cast(TextIO, process.stdout)
        line = stdout.readline()
        if line == "":
            raise _error("Codex App Server stdout closed", ProviderErrorCategory.TRANSIENT)
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise _error("invalid JSON-RPC JSON", ProviderErrorCategory.PROTOCOL) from exc
        return _parse_inbound(raw)

    def _require_process(self) -> subprocess.Popen[str]:
        if self._process is None:
            raise _error("transport is not started", ProviderErrorCategory.STATE, retryable=False)
        return self._process

    @staticmethod
    def _process_exit_error(process: subprocess.Popen[str]) -> ProviderAdapterError:
        stderr = ""
        if process.stderr is not None:
            stderr = process.stderr.read(4096)
        return _error(
            f"Codex App Server exited with code {process.returncode}",
            ProviderErrorCategory.TRANSIENT,
            retryable=True,
            provider_code="process_exit",
            details=stderr,
        )


@dataclass(slots=True)
class _TurnState:
    handle: TurnHandle
    terminal: bool = False
    sequence: int = 0
    seen_real_ids: set[str] = field(default_factory=set)
    pending_approvals: dict[str, RpcId] = field(default_factory=dict)
    redacted: bool = False
    cancellation_requested: bool = False


class CodexAppServerAdapter:
    """Synchronous ProviderAdapter for the generated Codex App Server schema."""

    def __init__(
        self,
        transport: CodexAppServerTransport,
        *,
        expected_cli_version: str = EXPECTED_CODEX_CLI_VERSION,
        schema_ref: str = SCHEMA_REF,
    ) -> None:
        if not expected_cli_version or expected_cli_version != expected_cli_version.strip():
            raise ValueError("expected_cli_version must be a normalized non-empty string")
        if schema_ref != SCHEMA_REF:
            raise ValueError("schema_ref must match the accepted C-501 schema pin")
        self._transport = transport
        self._expected_cli_version = expected_cli_version
        self._identity = AdapterIdentity(
            adapter="codex_app_server",
            provider="codex",
            implementation_version="c501-schema-bound",
            protocol_version=APP_SERVER_PROTOCOL_VERSION,
            schema_ref=schema_ref,
        )
        self._initialized = False
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
        self._initialized = False
        self._sessions.clear()
        self._turns.clear()
        self._request_ids.clear()

    def preflight(self) -> AdapterIdentity:
        self._require_started()
        if self._initialized:
            return self._identity
        result = self._transport.request(
            "initialize",
            {
                "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
                "capabilities": {
                    "experimentalApi": False,
                    "requestAttestation": False,
                },
            },
        )
        user_agent = _string(result.get("userAgent"), "initialize.userAgent")
        _string(result.get("codexHome"), "initialize.codexHome")
        _string(result.get("platformFamily"), "initialize.platformFamily")
        _string(result.get("platformOs"), "initialize.platformOs")
        version_pattern = rf"(?<![\d.]){re.escape(self._expected_cli_version)}(?![\d.])"
        if re.search(version_pattern, user_agent) is None:
            raise _error(
                "initialize response did not match the expected Codex CLI/schema pin",
                ProviderErrorCategory.COMPATIBILITY,
                retryable=False,
                provider_code="schema_pin_mismatch",
            )
        self._transport.notify("initialized")
        self._initialized = True
        return self._identity

    def create_session(self, *, run: Any) -> SessionHandle:
        self._require_ready_run(run)
        result = self._transport.request(
            "thread/start",
            {
                "model": run.model,
                "cwd": _selected_workspace(run),
                "baseInstructions": None,
                "developerInstructions": None,
                "approvalPolicy": None,
                "approvalsReviewer": None,
                "sandbox": None,
            },
        )
        thread = _object(result.get("thread"), "thread/start.thread")
        session = SessionHandle(
            session_id=_stable_id(thread.get("id"), "thread.id"),
            run_id=run.run_id,
            provider="codex",
        )
        existing = self._sessions.get(session.session_id)
        if existing is not None and existing != session:
            raise _error("provider thread identity collision", ProviderErrorCategory.PROTOCOL)
        self._sessions[session.session_id] = session
        return session

    def resume_session(self, *, run: Any, session_id: str) -> SessionHandle:
        self._require_ready_run(run)
        result = self._transport.request(
            "thread/resume", {"threadId": session_id, "model": run.model}
        )
        thread = _object(result.get("thread"), "thread/resume.thread")
        returned = _stable_id(thread.get("id"), "thread.id")
        if returned != session_id:
            raise _error("resumed thread identity mismatch", ProviderErrorCategory.PROTOCOL)
        session = SessionHandle(session_id=session_id, run_id=run.run_id, provider="codex")
        existing = self._sessions.get(session.session_id)
        if existing is not None and existing != session:
            raise _error("provider thread identity collision", ProviderErrorCategory.PROTOCOL)
        self._sessions[session.session_id] = session
        return session

    def submit_turn(self, *, session: SessionHandle, request: TurnRequest) -> TurnHandle:
        self._require_session(session)
        if session.run_id != request.run.run_id or request.run.provider != "codex":
            raise _error("session/run mismatch", ProviderErrorCategory.STATE, retryable=False)
        if request.request_id in self._request_ids:
            raise _error("duplicate request id", ProviderErrorCategory.STATE, retryable=False)
        result = self._transport.request(
            "turn/start",
            {
                "threadId": session.session_id,
                "clientUserMessageId": request.request_id,
                "input": [{"type": "text", "text": request.instructions, "text_elements": []}],
                "cwd": request.task.selected_workspace,
                "model": request.run.model,
                "effort": request.run.reasoning_effort,
            },
        )
        turn = _object(result.get("turn"), "turn/start.turn")
        handle = TurnHandle(
            turn_id=_stable_id(turn.get("id"), "turn.id"),
            session_id=session.session_id,
            request_id=request.request_id,
            run_id=request.run.run_id,
            task_id=request.task.task_id,
        )
        if handle.turn_id in self._turns:
            raise _error("duplicate provider turn id", ProviderErrorCategory.PROTOCOL)
        self._request_ids.add(request.request_id)
        self._turns[handle.turn_id] = _TurnState(handle=handle)
        return handle

    def stream_events(self, *, turn: TurnHandle) -> Iterator[ProviderEvent]:
        state = self._require_turn(turn)
        if state.terminal:
            return iter(())
        return self._stream(state)

    def respond_to_approval(self, *, turn: TurnHandle, response: ApprovalResponse) -> None:
        state = self._require_turn(turn)
        if state.terminal:
            raise _error("turn is terminal", ProviderErrorCategory.STATE, retryable=False)
        request_id = state.pending_approvals.get(response.approval_id)
        if request_id is None:
            raise _error("approval id mismatch", ProviderErrorCategory.STATE, retryable=False)
        decision = "accept" if response.decision is ApprovalStatus.GRANTED else "decline"
        self._transport.respond(request_id, {"decision": decision})
        del state.pending_approvals[response.approval_id]

    def interrupt(self, *, turn: TurnHandle, reason: str) -> None:
        state = self._require_turn(turn)
        _string(reason, "interrupt.reason")
        if state.terminal:
            raise _error("turn is terminal", ProviderErrorCategory.STATE, retryable=False)
        self._transport.request(
            "turn/interrupt", {"threadId": turn.session_id, "turnId": turn.turn_id}
        )

    def cancel(self, *, session: SessionHandle, reason: str) -> None:
        self._require_session(session)
        _string(reason, "cancel.reason")
        for state in self._turns.values():
            if state.handle.session_id == session.session_id and not state.terminal:
                self.interrupt(turn=state.handle, reason=reason)
                state.cancellation_requested = True

    def _stream(self, state: _TurnState) -> Iterator[ProviderEvent]:
        for message in self._transport.iter_messages():
            event = self._translate_message(state, message)
            if event is None:
                continue
            yield event
            if event.kind in {
                ProviderEventKind.APPROVAL_REQUIRED,
                ProviderEventKind.TURN_TERMINAL,
            }:
                break

    def _translate_message(
        self, state: _TurnState, message: InboundMessage
    ) -> ProviderEvent | None:
        if state.terminal:
            raise _error("post-terminal provider message", ProviderErrorCategory.PROTOCOL)
        if message.kind is InboundKind.RESPONSE:
            raise _error("unexpected interleaved response", ProviderErrorCategory.PROTOCOL)
        if message.kind is InboundKind.SERVER_REQUEST:
            return self._translate_server_request(state, message)
        if message.method is None or message.params is None:
            raise _error("malformed notification", ProviderErrorCategory.PROTOCOL)
        if message.method == "error":
            return self._translate_error(state, message.params)
        method = message.method
        params = message.params
        if "turnId" not in params:
            return None
        if _string(params.get("turnId"), f"{method}.turnId") != state.handle.turn_id:
            return None
        if _string(params.get("threadId"), f"{method}.threadId") != state.handle.session_id:
            raise _error("thread/turn mismatch", ProviderErrorCategory.PROTOCOL)
        if method == "turn/started":
            turn = _object(params.get("turn"), "turn/started.turn")
            self._dedupe(state, "turn", _stable_id(turn.get("id"), "turn.id"))
            return self._event(state, ProviderEventKind.TURN_STARTED, "Codex turn started")
        if method == "item/started":
            item = _object(params.get("item"), "item/started.item")
            item_id = _stable_id(item.get("id"), "item.id")
            self._dedupe(state, "item-started", item_id)
            return self._event(
                state, ProviderEventKind.ACTION, _bounded_item_summary(item, "started")
            )
        if method == "item/completed":
            item = _object(params.get("item"), "item/completed.item")
            item_id = _stable_id(item.get("id"), "item.id")
            self._dedupe(state, "item-completed", item_id)
            return self._event(
                state, ProviderEventKind.ACTION, _bounded_item_summary(item, "completed")
            )
        if method == "item/agentMessage/delta":
            item_id = _stable_id(params.get("itemId"), "agentMessage.itemId")
            self._dedupe(state, "agent-delta", f"{item_id}:{state.sequence + 1}")
            state.redacted = True
            return self._event(
                state,
                ProviderEventKind.OUTPUT,
                "Codex agent message delta redacted",
                redaction_status=RedactionStatus.REDACTED,
            )
        if method == "turn/completed":
            turn = _object(params.get("turn"), "turn/completed.turn")
            outcome, failure = _turn_outcome(
                turn, cancellation_requested=state.cancellation_requested
            )
            state.terminal = True
            return self._event(
                state,
                ProviderEventKind.TURN_TERMINAL,
                "Codex turn terminal",
                outcome=outcome,
                failure=failure,
            )
        raise _error(f"unknown mandatory notification {method!r}", ProviderErrorCategory.PROTOCOL)

    def _translate_server_request(
        self, state: _TurnState, message: InboundMessage
    ) -> ProviderEvent | None:
        if message.method not in {
            "item/commandExecution/requestApproval",
            "item/fileChange/requestApproval",
        }:
            raise _error(
                f"unsupported server request {message.method!r}", ProviderErrorCategory.PROTOCOL
            )
        params = _object(message.params, "serverRequest.params")
        if _string(params.get("turnId"), "approval.turnId") != state.handle.turn_id:
            return None
        if _string(params.get("threadId"), "approval.threadId") != state.handle.session_id:
            raise _error("approval thread/turn mismatch", ProviderErrorCategory.PROTOCOL)
        request_id = _rpc_id(message.request_id, "approval request id")
        item_id = _stable_id(params.get("itemId"), "approval.itemId")
        approval_id = str(params.get("approvalId") or item_id)
        self._dedupe(state, "server-request", f"{message.method}:{request_id}")
        action_class = (
            ActionClass.WRITE
            if message.method == "item/fileChange/requestApproval"
            else ActionClass.OTHER_EXTERNAL_WRITE
        )
        approval = ApprovalRequest(
            approval_id=approval_id,
            action_class=action_class,
            summary="Codex approval request",
            input_refs=(f"provider://codex/{state.handle.turn_id}/{item_id}",),
        )
        state.pending_approvals[approval.approval_id] = request_id
        return self._event(
            state,
            ProviderEventKind.APPROVAL_REQUIRED,
            "Codex approval request",
            approval=approval,
        )

    def _translate_error(self, state: _TurnState, params: JSON) -> ProviderEvent | None:
        if _string(params.get("turnId"), "error.turnId") != state.handle.turn_id:
            return None
        if _string(params.get("threadId"), "error.threadId") != state.handle.session_id:
            raise _error("error thread/turn mismatch", ProviderErrorCategory.PROTOCOL)
        will_retry = params.get("willRetry")
        if type(will_retry) is not bool:
            raise _error("error.willRetry must be a boolean", ProviderErrorCategory.PROTOCOL)
        failure = _failure(
            _object(params.get("error"), "error.error"),
            state.handle.turn_id,
            retryable=will_retry,
        )
        if will_retry:
            return self._event(
                state, ProviderEventKind.ACTION, "Codex transient error notification"
            )
        state.terminal = True
        return self._event(
            state,
            ProviderEventKind.TURN_TERMINAL,
            "Codex error terminal",
            outcome=ProviderTurnOutcome.FAILED,
            failure=failure,
        )

    def _event(
        self,
        state: _TurnState,
        kind: ProviderEventKind,
        summary: str,
        *,
        redaction_status: RedactionStatus = RedactionStatus.NOT_REQUIRED,
        approval: ApprovalRequest | None = None,
        outcome: ProviderTurnOutcome | None = None,
        failure: ProviderFailure | None = None,
    ) -> ProviderEvent:
        state.sequence += 1
        return ProviderEvent(
            event_id=f"codex.{state.handle.turn_id}.{state.sequence}",
            sequence=state.sequence,
            timestamp=datetime.now(UTC),
            session_id=state.handle.session_id,
            turn_id=state.handle.turn_id,
            kind=kind,
            summary=summary,
            evidence_refs=(f"provider://codex/{state.handle.turn_id}/{state.sequence}",),
            redaction_status=redaction_status,
            approval=approval,
            outcome=outcome,
            failure=failure,
        )

    def _dedupe(self, state: _TurnState, kind: str, real_id: str) -> None:
        key = f"{kind}:{real_id}"
        if key in state.seen_real_ids:
            raise _error("duplicate provider identity", ProviderErrorCategory.PROTOCOL)
        state.seen_real_ids.add(key)

    def _require_started(self) -> None:
        if not self.started:
            raise _error("adapter is not started", ProviderErrorCategory.STATE, retryable=False)

    def _require_ready_run(self, run: Any) -> None:
        self._require_started()
        if not self._initialized:
            raise _error(
                "initialize preflight is required", ProviderErrorCategory.STATE, retryable=False
            )
        if getattr(run, "provider", None) != "codex":
            raise _error("run provider must be codex", ProviderErrorCategory.STATE, retryable=False)

    def _require_session(self, session: SessionHandle) -> None:
        self._require_started()
        if session.provider != "codex" or self._sessions.get(session.session_id) != session:
            raise _error("unknown Codex session", ProviderErrorCategory.STATE, retryable=False)

    def _require_turn(self, turn: TurnHandle) -> _TurnState:
        self._require_started()
        state = self._turns.get(turn.turn_id)
        if state is None or state.handle != turn:
            raise _error("unknown Codex turn", ProviderErrorCategory.STATE, retryable=False)
        return state


def _parse_inbound(raw: Any) -> InboundMessage:
    envelope = _object(raw, "json-rpc envelope")
    if envelope.get("jsonrpc") != "2.0":
        raise _error("JSON-RPC envelope must declare version 2.0", ProviderErrorCategory.PROTOCOL)
    has_id = "id" in envelope
    has_method = "method" in envelope
    if has_method:
        if "result" in envelope or "error" in envelope:
            raise _error(
                "JSON-RPC method message cannot contain result or error",
                ProviderErrorCategory.PROTOCOL,
            )
        method = _string(envelope.get("method"), "json-rpc method")
        params = _object(envelope.get("params", {}), "json-rpc params")
        if has_id:
            return InboundMessage(
                kind=InboundKind.SERVER_REQUEST,
                method=method,
                params=params,
                request_id=_rpc_id(envelope.get("id"), "json-rpc id"),
            )
        return InboundMessage(kind=InboundKind.NOTIFICATION, method=method, params=params)
    if has_id:
        request_id = _rpc_id(envelope.get("id"), "json-rpc id")
        has_error = "error" in envelope
        has_result = "result" in envelope
        if has_error == has_result:
            raise _error(
                "JSON-RPC response must contain exactly one of result or error",
                ProviderErrorCategory.PROTOCOL,
            )
        if has_error:
            return InboundMessage(
                kind=InboundKind.RESPONSE,
                request_id=request_id,
                error=_object(envelope.get("error"), "json-rpc error"),
            )
        return InboundMessage(
            kind=InboundKind.RESPONSE,
            request_id=request_id,
            result=_object(envelope.get("result"), "json-rpc result"),
        )
    raise _error(
        "JSON-RPC envelope is neither response nor method message", ProviderErrorCategory.PROTOCOL
    )


def _rpc_error(error: JSON) -> ProviderAdapterError:
    code = str(error.get("code", "json_rpc_error"))
    message = _string(error.get("message"), "json-rpc error.message")
    return _error(message, ProviderErrorCategory.PROTOCOL, retryable=False, provider_code=code)


def _turn_outcome(
    turn: JSON, *, cancellation_requested: bool
) -> tuple[ProviderTurnOutcome, ProviderFailure | None]:
    status = _string(turn.get("status"), "turn.status")
    if status == "completed":
        return ProviderTurnOutcome.SUCCEEDED, None
    if status == "interrupted":
        outcome = (
            ProviderTurnOutcome.CANCELLED
            if cancellation_requested
            else ProviderTurnOutcome.INTERRUPTED
        )
        return outcome, None
    if status == "failed":
        failure = _failure(
            _object(turn.get("error"), "turn.error"),
            _string(turn.get("id"), "turn.id"),
            retryable=False,
        )
        return ProviderTurnOutcome.FAILED, failure
    raise _error(f"unknown terminal turn status {status!r}", ProviderErrorCategory.PROTOCOL)


def _failure(raw: JSON, correlation_id: str, *, retryable: bool) -> ProviderFailure:
    return ProviderFailure(
        category=(
            ProviderErrorCategory.TRANSIENT if retryable else ProviderErrorCategory.PERMANENT
        ),
        message=_string(raw.get("message"), "turn.error.message"),
        retryable=retryable,
        provider_code="codex_turn_error",
        correlation_id=correlation_id,
    )


def _bounded_item_summary(item: JSON, phase: str) -> str:
    item_type = _string(item.get("type"), "item.type")
    return f"Codex item {phase}: {item_type}"


def _selected_workspace(run: Any) -> str | None:
    _ = run
    return None


def _object(value: Any, location: str) -> JSON:
    if not isinstance(value, Mapping):
        raise _error(f"{location} must be an object", ProviderErrorCategory.PROTOCOL)
    return value


def _string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _error(
            f"{location} must be a normalized non-empty string", ProviderErrorCategory.PROTOCOL
        )
    return value


def _stable_id(value: Any, location: str) -> str:
    normalized = _string(value, location)
    if _STABLE_ID_RE.fullmatch(normalized) is None:
        raise _error(f"{location} must be a stable identifier", ProviderErrorCategory.PROTOCOL)
    return normalized


def _rpc_id(value: Any, location: str) -> RpcId:
    if type(value) is str and value != "":
        return value
    if type(value) is int:
        return value
    raise _error(
        f"{location} must be a JSON-RPC string or integer id", ProviderErrorCategory.PROTOCOL
    )


def _error(
    message: str,
    category: ProviderErrorCategory,
    *,
    retryable: bool = False,
    provider_code: str | None = None,
    details: str = "",
) -> ProviderAdapterError:
    safe = message if not details else f"{message}; provider stderr omitted ({len(details)} bytes)"
    return ProviderAdapterError(
        safe,
        category=category,
        retryable=retryable,
        provider_code=provider_code,
    )


__all__ = [
    "APP_SERVER_PROTOCOL_VERSION",
    "CLIENT_NAME",
    "CLIENT_VERSION",
    "CodexAppServerAdapter",
    "CodexAppServerTransport",
    "InboundKind",
    "InboundMessage",
    "SCHEMA_REF",
    "SubprocessJsonRpcTransport",
]

assert issubclass(CodexAppServerAdapter, object)
