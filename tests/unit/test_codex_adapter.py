"""C-501 Codex App Server adapter tests with schema-shaped fake transports."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator

from harness.adapters.base import (
    ApprovalResponse,
    ProviderAdapter,
    ProviderAdapterError,
    ProviderErrorCategory,
    ProviderEventKind,
    ProviderTurnOutcome,
    SessionHandle,
    TurnHandle,
    TurnRequest,
)
from harness.adapters.codex_app_server import (
    CLIENT_NAME,
    CLIENT_VERSION,
    EXPECTED_CODEX_CLI_VERSION,
    CodexAppServerAdapter,
    InboundKind,
    InboundMessage,
    SubprocessJsonlTransport,
)
from harness.state import (
    ApprovalStatus,
    BudgetState,
    BudgetValues,
    CompletionVerdict,
    LifecycleState,
    RedactionStatus,
    Run,
    Task,
    TaskStatus,
)

NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)
SCHEMA_DIRECTORY = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "research"
    / "generated-app-server-schema"
    / "codex-cli-0.144.3"
    / "experimental"
    / "json-schema"
    / "v2"
)
STABLE_SCHEMA_DIRECTORY = SCHEMA_DIRECTORY.parents[2] / "stable" / "json-schema"


def budget_state() -> BudgetState:
    return BudgetState(
        limits=BudgetValues(
            iterations=4,
            elapsed_seconds=600.0,
            input_tokens=1000,
            output_tokens=1000,
            total_tokens=2000,
            cost=5.0,
        ),
        consumed=BudgetValues(
            iterations=0,
            elapsed_seconds=0.0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost=0.0,
        ),
    )


def run_record(**changes: object) -> Run:
    values: dict[str, object] = {
        "run_id": "run.c501.001",
        "goal_id": "goal.c501",
        "provider": "codex",
        "model": "gpt-5.6-codex",
        "reasoning_effort": "high",
        "provider_config_ref": None,
        "lifecycle_state": LifecycleState.EXECUTING,
        "started_at": NOW,
        "updated_at": NOW,
        "iteration_count": 1,
        "budget": budget_state(),
        "current_task_id": "C-501",
        "approval_state": None,
        "checkpoint_ref": None,
        "stop_reason": None,
        "completion_verdict": CompletionVerdict.NOT_EVALUATED,
        "completion_evidence_refs": (),
        "event_seq": 7,
        "last_transition_id": "transition.c501.executing",
    }
    values.update(changes)
    return Run(**values)  # type: ignore[arg-type]


def task_record(**changes: object) -> Task:
    values: dict[str, object] = {
        "task_id": "C-501",
        "goal_id": "goal.c501",
        "description": "Implement the Codex App Server adapter.",
        "dependencies": ("C-103", "C-402", "C-406", "C-407"),
        "status": TaskStatus.IN_PROGRESS,
        "attempts": 1,
        "selected_workspace": r"C:\worktrees\c501",
        "allowed_paths": (
            "src/harness/adapters/codex_app_server.py",
            "tests/unit/test_codex_adapter.py",
        ),
        "locked_paths": (),
        "criterion_ids": ("criterion.c501",),
        "validation_commands": ("uv run pytest -q tests/unit/test_codex_adapter.py",),
    }
    values.update(changes)
    return Task(**values)  # type: ignore[arg-type]


def thread(thread_id: str = "thread.c501.001") -> Mapping[str, Any]:
    return {
        "id": thread_id,
        "sessionId": "session.c501",
        "preview": "redacted",
        "modelProvider": "openai",
        "createdAt": 1,
        "updatedAt": 1,
        "status": "running",
        "cwd": r"C:\worktrees\c501",
        "cliVersion": EXPECTED_CODEX_CLI_VERSION,
        "source": "appServer",
        "turns": [],
    }


def turn(turn_id: str = "turn.c501.001", status: str = "inProgress") -> Mapping[str, Any]:
    terminal = status != "inProgress"
    return {
        "id": turn_id,
        "items": [],
        "itemsView": "full",
        "status": status,
        "error": {"message": "failed", "codexErrorInfo": None, "additionalDetails": None}
        if status == "failed"
        else None,
        "startedAt": 1,
        "completedAt": 2 if terminal else None,
        "durationMs": 1000 if terminal else None,
    }


@dataclass(slots=True)
class FakeTransport:
    replies: dict[str, list[Mapping[str, Any]]]
    inbound: list[InboundMessage] = field(default_factory=list)
    is_started: bool = False
    calls: list[tuple[str, str, Mapping[str, Any] | None]] = field(default_factory=list)
    responses: list[tuple[str | int, Mapping[str, Any]]] = field(default_factory=list)

    @property
    def started(self) -> bool:
        return self.is_started

    def start(self) -> None:
        self.is_started = True

    def stop(self) -> None:
        self.is_started = False

    def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append(("request", method, dict(params)))
        queue = self.replies.get(method)
        if not queue:
            raise AssertionError(f"unexpected request {method}")
        return queue.pop(0)

    def notify(self, method: str, params: Mapping[str, Any] | None = None) -> None:
        self.calls.append(("notify", method, params))

    def respond(self, request_id: str | int, result: Mapping[str, Any]) -> None:
        self.responses.append((request_id, dict(result)))

    def iter_messages(self) -> Iterator[InboundMessage]:
        while self.inbound:
            yield self.inbound.pop(0)


@dataclass(slots=True)
class RecordingStdin:
    lines: list[str] = field(default_factory=list)

    def write(self, value: str) -> int:
        self.lines.append(value)
        return len(value)

    def flush(self) -> None:
        return None


@dataclass(slots=True)
class ScriptedStdout:
    lines: Iterator[str]

    def readline(self) -> str:
        return next(self.lines)


class ScriptedProcess:
    def __init__(self, lines: list[str]) -> None:
        self.stdin = RecordingStdin()
        self.stdout = ScriptedStdout(iter(lines))
        self.stderr: None = None
        self.returncode: None = None

    def poll(self) -> None:
        return None


def scripted_transport(
    *lines: str,
) -> tuple[SubprocessJsonlTransport, ScriptedProcess]:
    process = ScriptedProcess(list(lines))
    transport = SubprocessJsonlTransport(("codex", "app-server"))
    transport._process = process  # type: ignore[assignment]
    return transport, process


def ready_replies() -> dict[str, list[Mapping[str, Any]]]:
    return {
        "initialize": [
            {
                "userAgent": f"codex-cli/{EXPECTED_CODEX_CLI_VERSION}",
                "codexHome": r"C:\Users\operator\.codex",
                "platformFamily": "windows",
                "platformOs": "windows",
            }
        ],
        "thread/start": [{"thread": thread(), "model": "gpt-5.6-codex"}],
        "thread/resume": [{"thread": thread(), "model": "gpt-5.6-codex"}],
        "turn/start": [{"turn": turn()}],
        "turn/interrupt": [{"turn": turn(status="interrupted")}],
    }


def note(method: str, params: Mapping[str, Any]) -> InboundMessage:
    return InboundMessage(kind=InboundKind.NOTIFICATION, method=method, params=params)


def turn_note(
    method: str,
    *,
    thread_id: str = "thread.c501.001",
    turn_id: str = "turn.c501.001",
    status: str = "inProgress",
) -> InboundMessage:
    schema_name = {
        "turn/started": "TurnStartedNotification.json",
        "turn/completed": "TurnCompletedNotification.json",
    }[method]
    params = {
        "threadId": thread_id,
        "turn": turn(turn_id=turn_id, status=status),
    }
    schema = json.loads((SCHEMA_DIRECTORY / schema_name).read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    Draft7Validator(schema).validate(params)
    assert "turnId" not in params
    return note(method, params)


def approval_request(
    request_id: str, method: str = "item/commandExecution/requestApproval"
) -> InboundMessage:
    return InboundMessage(
        kind=InboundKind.SERVER_REQUEST,
        request_id=request_id,
        method=method,
        params={
            "threadId": "thread.c501.001",
            "turnId": "turn.c501.001",
            "itemId": "item.approval.001",
            "startedAtMs": 1,
            "reason": "redacted",
        },
    )


def prepared_adapter(
    inbound: list[InboundMessage] | None = None,
) -> tuple[CodexAppServerAdapter, FakeTransport, SessionHandle, TurnHandle]:
    transport = FakeTransport(ready_replies(), inbound or [])
    adapter = CodexAppServerAdapter(transport)
    assert isinstance(adapter, ProviderAdapter)
    adapter.start()
    adapter.preflight()
    session = adapter.create_session(run=run_record())
    handle = adapter.submit_turn(
        session=session,
        request=TurnRequest(
            request_id="request.c501.001",
            run=run_record(),
            task=task_record(),
            instructions="Prompt text must only cross the wire and never return in events.",
        ),
    )
    return adapter, transport, session, handle


def test_initialize_initialized_sequence_and_schema_method_names_are_exact() -> None:
    adapter, transport, session, handle = prepared_adapter()

    assert adapter.started
    assert session.session_id == "thread.c501.001"
    assert handle.turn_id == "turn.c501.001"
    assert [call[1] for call in transport.calls] == [
        "initialize",
        "initialized",
        "thread/start",
        "turn/start",
    ]
    initialize = transport.calls[0][2]
    assert initialize is not None
    assert initialize["clientInfo"] == {"name": CLIENT_NAME, "version": CLIENT_VERSION}
    assert initialize["capabilities"] == {
        "experimentalApi": False,
        "requestAttestation": False,
    }
    turn_start = transport.calls[-1][2]
    assert turn_start is not None
    assert turn_start["threadId"] == "thread.c501.001"
    assert turn_start["clientUserMessageId"] == "request.c501.001"
    assert turn_start["input"] == [
        {
            "type": "text",
            "text": "Prompt text must only cross the wire and never return in events.",
            "text_elements": [],
        }
    ]
    adapter.start()
    adapter.preflight()
    assert [call[1] for call in transport.calls].count("initialize") == 1
    adapter.stop()
    adapter.stop()


def test_no_invented_compatibility_or_thread_cancel_methods_are_sent() -> None:
    adapter, transport, session, _ = prepared_adapter()
    adapter.cancel(session=session, reason="cancel all active turns")
    methods = [call[1] for call in transport.calls]
    assert "server.compatibility" not in methods
    assert "thread.cancel" not in methods
    assert "turn/interrupt" in methods


def test_preflight_fails_closed_when_initialize_schema_pin_mismatches() -> None:
    transport = FakeTransport(
        {
            "initialize": [
                {
                    "userAgent": "codex-cli/0.000.0",
                    "codexHome": r"C:\.codex",
                    "platformFamily": "windows",
                    "platformOs": "windows",
                }
            ]
        }
    )
    adapter = CodexAppServerAdapter(transport)
    adapter.start()
    with pytest.raises(ProviderAdapterError) as error:
        adapter.preflight()
    assert error.value.category is ProviderErrorCategory.COMPATIBILITY

    near_match = FakeTransport(
        {
            "initialize": [
                {
                    "userAgent": f"codex-cli/{EXPECTED_CODEX_CLI_VERSION}0",
                    "codexHome": r"C:\\.codex",
                    "platformFamily": "windows",
                    "platformOs": "windows",
                }
            ]
        }
    )
    adapter = CodexAppServerAdapter(near_match)
    adapter.start()
    with pytest.raises(ProviderAdapterError, match="schema pin"):
        adapter.preflight()


def test_thread_resume_wraps_thread_object_and_rejects_identity_mismatch() -> None:
    adapter, _, session, _ = prepared_adapter()
    assert adapter.resume_session(run=run_record(), session_id=session.session_id) == session

    bad_transport = FakeTransport(
        ready_replies() | {"thread/resume": [{"thread": thread("other")}]}
    )
    bad = CodexAppServerAdapter(bad_transport)
    bad.start()
    bad.preflight()
    with pytest.raises(ProviderAdapterError, match="mismatch"):
        bad.resume_session(run=run_record(), session_id="thread.c501.001")


def test_stream_translates_real_notifications_with_bounded_redacted_output() -> None:
    adapter, _, _, handle = prepared_adapter(
        [
            note("thread/status/changed", {"threadId": "thread.other"}),
            turn_note("turn/started"),
            note(
                "item/started",
                {
                    "threadId": handle_session(),
                    "turnId": "turn.c501.001",
                    "item": {"type": "commandExecution", "id": "item.command.1"},
                    "startedAtMs": 1,
                },
            ),
            note(
                "item/agentMessage/delta",
                {
                    "threadId": handle_session(),
                    "turnId": "turn.c501.001",
                    "itemId": "item.agent.1",
                    "delta": "secret prompt payload",
                },
            ),
            turn_note("turn/completed", status="completed"),
        ]
    )

    events = tuple(adapter.stream_events(turn=handle))
    assert [event.kind for event in events] == [
        ProviderEventKind.TURN_STARTED,
        ProviderEventKind.ACTION,
        ProviderEventKind.OUTPUT,
        ProviderEventKind.TURN_TERMINAL,
    ]
    assert [event.sequence for event in events] == [1, 2, 3, 4]
    assert events[2].redaction_status is RedactionStatus.REDACTED
    assert "secret prompt payload" not in events[2].summary
    assert events[-1].outcome is ProviderTurnOutcome.SUCCEEDED
    assert tuple(adapter.stream_events(turn=handle)) == ()


def handle_session() -> str:
    return "thread.c501.001"


@pytest.mark.parametrize(
    ("notification", "message"),
    [
        (
            turn_note("turn/completed", turn_id="turn.other", status="completed"),
            "turn identifier mismatch",
        ),
        (
            turn_note("turn/completed", thread_id="thread.other", status="completed"),
            "thread/turn mismatch",
        ),
    ],
)
def test_schema_valid_completion_identifier_mismatches_fail_closed(
    notification: InboundMessage, message: str
) -> None:
    adapter, _, _, handle = prepared_adapter([notification])

    with pytest.raises(ProviderAdapterError, match=message):
        tuple(adapter.stream_events(turn=handle))


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"threadId": "thread.c501.001"}, "turn/completed.turn must be an object"),
        (
            {"threadId": "thread.c501.001", "turn": "malformed"},
            "turn/completed.turn must be an object",
        ),
        (
            {
                "threadId": "thread.c501.001",
                "turn": {"items": [], "status": "completed"},
            },
            "turn/completed.turn.id",
        ),
    ],
)
def test_completion_missing_or_malformed_nested_turn_fails_closed(
    params: Mapping[str, Any], message: str
) -> None:
    adapter, _, _, handle = prepared_adapter([note("turn/completed", params)])

    with pytest.raises(ProviderAdapterError, match=message):
        tuple(adapter.stream_events(turn=handle))


@pytest.mark.parametrize(
    "params",
    [
        {
            "threadId": "thread.c501.001",
            "item": {"type": "commandExecution", "id": "item.command.1"},
            "startedAtMs": 1,
        },
        {
            "threadId": "thread.c501.001",
            "turnId": "turn.other",
            "item": {"type": "commandExecution", "id": "item.command.1"},
            "startedAtMs": 1,
        },
    ],
)
def test_top_level_turn_id_notification_missing_or_mismatch_fails_closed(
    params: Mapping[str, Any],
) -> None:
    adapter, _, _, handle = prepared_adapter([note("item/started", params)])

    with pytest.raises(ProviderAdapterError, match="turn identifier"):
        tuple(adapter.stream_events(turn=handle))


def test_unrelated_notification_without_turn_identifier_is_ignored() -> None:
    adapter, _, _, handle = prepared_adapter(
        [
            note("thread/status/changed", {"threadId": "thread.other"}),
            turn_note("turn/completed", status="completed"),
        ]
    )

    events = tuple(adapter.stream_events(turn=handle))
    assert [event.kind for event in events] == [ProviderEventKind.TURN_TERMINAL]
    assert events[0].outcome is ProviderTurnOutcome.SUCCEEDED


@pytest.mark.parametrize(
    "status,outcome",
    [
        ("failed", ProviderTurnOutcome.FAILED),
        ("interrupted", ProviderTurnOutcome.INTERRUPTED),
    ],
)
def test_failure_interrupted_and_cancelled_terminal_statuses_are_normalized(
    status: str, outcome: ProviderTurnOutcome
) -> None:
    adapter, _, _, handle = prepared_adapter(
        [
            turn_note("turn/started"),
            turn_note("turn/completed", status=status),
        ]
    )
    events = tuple(adapter.stream_events(turn=handle))
    assert events[-1].outcome is outcome
    if outcome is ProviderTurnOutcome.FAILED:
        assert events[-1].failure is not None


def test_session_cancel_uses_turn_interrupt_and_normalizes_terminal_as_cancelled() -> None:
    inbound = [turn_note("turn/completed", status="interrupted")]
    adapter, transport, session, handle = prepared_adapter(inbound)
    adapter.cancel(session=session, reason="operator cancelled the session")
    terminal = tuple(adapter.stream_events(turn=handle))[-1]

    assert transport.calls[-1][1] == "turn/interrupt"
    assert terminal.outcome is ProviderTurnOutcome.CANCELLED


def test_approval_allow_and_deny_reply_to_original_server_request_ids() -> None:
    adapter, transport, _, handle = prepared_adapter([approval_request("server.req.1")])
    approval = tuple(adapter.stream_events(turn=handle))[-1].approval
    assert approval is not None
    adapter.respond_to_approval(
        turn=handle,
        response=ApprovalResponse(
            approval_id=approval.approval_id,
            decision=ApprovalStatus.GRANTED,
            reason="allow in test",
        ),
    )

    adapter2, transport2, _, handle2 = prepared_adapter(
        [approval_request("server.req.2", "item/fileChange/requestApproval")]
    )
    approval2 = tuple(adapter2.stream_events(turn=handle2))[-1].approval
    assert approval2 is not None
    adapter2.respond_to_approval(
        turn=handle2,
        response=ApprovalResponse(
            approval_id=approval2.approval_id,
            decision=ApprovalStatus.DENIED,
            reason="deny in test",
        ),
    )
    assert transport.responses == [("server.req.1", {"decision": "accept"})]
    assert transport2.responses == [("server.req.2", {"decision": "decline"})]


@pytest.mark.parametrize(
    "inbound, message",
    [
        (
            [note("future/mandatory", {"threadId": handle_session(), "turnId": "turn.c501.001"})],
            "unknown",
        ),
        (
            [
                turn_note("turn/started"),
                turn_note("turn/started"),
            ],
            "duplicate",
        ),
        (
            [
                InboundMessage(
                    kind=InboundKind.SERVER_REQUEST,
                    method="item/tool/requestUserInput",
                    request_id=3,
                    params={},
                )
            ],
            "unsupported",
        ),
    ],
)
def test_unknown_duplicate_post_terminal_and_unsupported_messages_fail_closed(
    inbound: list[InboundMessage], message: str
) -> None:
    adapter, _, _, handle = prepared_adapter(inbound)
    with pytest.raises(ProviderAdapterError, match=message):
        tuple(adapter.stream_events(turn=handle))


def test_terminal_returns_without_waiting_and_duplicate_terminal_fails_closed() -> None:
    duplicate_terminal = turn_note("turn/completed", status="completed")
    adapter, transport, _, handle = prepared_adapter(
        [
            turn_note("turn/completed", status="completed"),
            duplicate_terminal,
        ]
    )

    assert tuple(adapter.stream_events(turn=handle))[-1].outcome is ProviderTurnOutcome.SUCCEEDED
    assert transport.inbound == [duplicate_terminal]
    state = adapter._turns[handle.turn_id]
    with pytest.raises(ProviderAdapterError, match="post-terminal"):
        adapter._translate_message(state, transport.inbound.pop(0))


def test_error_notification_can_be_nonterminal_or_terminal() -> None:
    adapter, _, _, handle = prepared_adapter(
        [
            note(
                "error",
                {
                    "threadId": handle_session(),
                    "turnId": "turn.c501.001",
                    "willRetry": True,
                    "error": {
                        "message": "retry",
                        "codexErrorInfo": None,
                        "additionalDetails": None,
                    },
                },
            ),
            note(
                "error",
                {
                    "threadId": handle_session(),
                    "turnId": "turn.c501.001",
                    "willRetry": False,
                    "error": {"message": "stop", "codexErrorInfo": None, "additionalDetails": None},
                },
            ),
        ]
    )
    events = tuple(adapter.stream_events(turn=handle))
    assert events[0].kind is ProviderEventKind.ACTION
    assert events[1].outcome is ProviderTurnOutcome.FAILED


def test_retried_error_does_not_poison_a_successful_terminal() -> None:
    adapter, _, _, handle = prepared_adapter(
        [
            note(
                "error",
                {
                    "threadId": handle_session(),
                    "turnId": "turn.c501.001",
                    "willRetry": True,
                    "error": {
                        "message": "retry",
                        "codexErrorInfo": None,
                        "additionalDetails": None,
                    },
                },
            ),
            turn_note("turn/completed", status="completed"),
        ]
    )

    terminal = tuple(adapter.stream_events(turn=handle))[-1]
    assert terminal.outcome is ProviderTurnOutcome.SUCCEEDED
    assert terminal.failure is None


def test_state_guards_reject_duplicate_request_forged_handles_and_bad_approval() -> None:
    adapter, _, session, handle = prepared_adapter([approval_request("server.req.1")])
    with pytest.raises(ProviderAdapterError, match="duplicate request"):
        adapter.submit_turn(
            session=session,
            request=TurnRequest(
                request_id="request.c501.001",
                run=run_record(),
                task=task_record(),
                instructions="duplicate",
            ),
        )
    with pytest.raises(ProviderAdapterError, match="unknown Codex session"):
        adapter.cancel(
            session=SessionHandle(
                session_id="thread.forged", run_id=session.run_id, provider="codex"
            ),
            reason="bad",
        )
    with pytest.raises(ProviderAdapterError, match="unknown Codex turn"):
        tuple(
            adapter.stream_events(
                turn=TurnHandle(
                    turn_id="turn.forged",
                    session_id=session.session_id,
                    request_id=handle.request_id,
                    run_id=handle.run_id,
                    task_id=handle.task_id,
                )
            )
        )
    tuple(adapter.stream_events(turn=handle))
    with pytest.raises(ProviderAdapterError, match="approval id mismatch"):
        adapter.respond_to_approval(
            turn=handle,
            response=ApprovalResponse(
                approval_id="approval.other",
                decision=ApprovalStatus.DENIED,
                reason="deny",
            ),
        )


def test_subprocess_transport_emits_only_schema_shaped_unversioned_envelopes() -> None:
    transport, process = scripted_transport('{"id":1,"result":{"ok":"yes"}}\n')

    assert transport.request("initialize", {"clientInfo": {"name": "test"}}) == {"ok": "yes"}
    transport.notify("initialized")
    transport.notify("client/ready", {"ready": True})
    transport.respond("server.request.1", {"decision": "accept"})

    wire = [json.loads(line) for line in process.stdin.lines]
    assert wire == [
        {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "test"}}},
        {"method": "initialized"},
        {"method": "client/ready", "params": {"ready": True}},
        {"id": "server.request.1", "result": {"decision": "accept"}},
    ]
    assert all("jsonrpc" not in envelope for envelope in wire)


def test_unversioned_success_error_notification_and_server_request_are_distinct() -> None:
    transport, _ = scripted_transport(
        '{"method":"thread/started","params":{"thread":{"id":"thread.1"}}}\n',
        '{"id":"server.request.1","method":"item/tool/requestUserInput","params":{}}\n',
        '{"id":1,"result":{"ok":"yes"},"schemaPermittedExtension":true}\n',
    )

    assert transport.request("initialize", {}) == {"ok": "yes"}
    notification = next(transport.iter_messages())
    server_request = next(transport.iter_messages())
    assert notification.kind is InboundKind.NOTIFICATION
    assert notification.request_id is None
    assert server_request.kind is InboundKind.SERVER_REQUEST
    assert server_request.request_id == "server.request.1"

    failing, _ = scripted_transport('{"id":1,"error":{"code":"bad_request","message":"boom"}}\n')
    with pytest.raises(ProviderAdapterError) as raised:
        failing.request("initialize", {})
    assert raised.value.provider_code == "bad_request"


def test_generated_stable_request_schema_permits_unspecified_extra_members() -> None:
    schema = json.loads(
        (STABLE_SCHEMA_DIRECTORY / "ClientRequest.json").read_text(encoding="utf-8")
    )
    Draft7Validator.check_schema(schema)
    assert all(branch.get("additionalProperties", True) is not False for branch in schema["oneOf"])
    Draft7Validator(schema).validate(
        {
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
                "capabilities": {
                    "experimentalApi": False,
                    "requestAttestation": False,
                },
            },
            "schemaPermittedExtension": True,
        }
    )


@pytest.mark.parametrize(
    "line",
    [
        "{}\n",
        '{"id":1}\n',
        '{"id":1,"result":{},"error":{"code":"bad","message":"boom"}}\n',
        '{"id":true,"result":{}}\n',
        '{"id":true,"method":"event","params":{}}\n',
        '{"method":"event","params":{},"result":{}}\n',
    ],
)
def test_unversioned_malformed_ambiguous_and_boolean_id_envelopes_fail_closed(
    line: str,
) -> None:
    assert parse_failure(line).category is ProviderErrorCategory.PROTOCOL


def test_subprocess_transport_startup_missing_executable_invalid_json_and_response_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = SubprocessJsonlTransport(("missing-codex-binary", "app-server"))

    def raise_oserror(*_args: object, **_kwargs: object) -> object:
        raise FileNotFoundError("missing")

    monkeypatch.setattr("subprocess.Popen", raise_oserror)
    with pytest.raises(ProviderAdapterError, match="failed to start"):
        missing.start()

    assert parse_failure("not-json\n").category is ProviderErrorCategory.PROTOCOL
    assert parse_failure('{"result":{}}\n').category is ProviderErrorCategory.PROTOCOL
    assert (
        parse_failure('{"id":1,"error":{"code":"bad","message":"boom"}}\n').provider_code == "bad"
    )
    assert (
        parse_failure('{"id":1,"result":{},"error":{"code":"bad","message":"boom"}}\n').category
        is ProviderErrorCategory.PROTOCOL
    )
    assert parse_failure('{"id":true,"result":{}}\n').category is ProviderErrorCategory.PROTOCOL


def test_subprocess_transport_preserves_interleaved_notification() -> None:
    class Stdout:
        def __init__(self) -> None:
            self.lines = iter(
                [
                    '{"method":"thread/started","params":{}}\n',
                    '{"id":1,"result":{"ok":"yes"}}\n',
                ]
            )

        def readline(self) -> str:
            return next(self.lines)

    class Stdin:
        def write(self, value: str) -> int:
            return len(value)

        def flush(self) -> None:
            return None

    class Process:
        stdin = Stdin()
        stdout = Stdout()
        stderr = None
        returncode = None

        def poll(self) -> None:
            return None

    transport = SubprocessJsonlTransport(("codex", "app-server"))
    transport._process = Process()  # type: ignore[assignment]

    assert transport.request("initialize", {}) == {"ok": "yes"}
    preserved = next(transport.iter_messages())
    assert preserved.kind is InboundKind.NOTIFICATION
    assert preserved.method == "thread/started"


def test_subprocess_transport_normalizes_process_exit_without_leaking_stderr() -> None:
    class Stderr:
        def read(self, _maximum: int) -> str:
            return "secret-provider-stderr"

    class Process:
        stdin = None
        stdout = None
        stderr = Stderr()
        returncode = 7

        def poll(self) -> int:
            return 7

    transport = SubprocessJsonlTransport(("codex", "app-server"))
    transport._process = Process()  # type: ignore[assignment]

    with pytest.raises(ProviderAdapterError) as raised:
        transport.request("initialize", {})
    assert raised.value.category is ProviderErrorCategory.TRANSIENT
    assert raised.value.provider_code == "process_exit"
    assert "secret-provider-stderr" not in str(raised.value)


def parse_failure(line: str) -> ProviderAdapterError:
    class Stdout:
        def readline(self) -> str:
            return line

    class Stdin:
        def write(self, _value: str) -> int:
            return len(_value)

        def flush(self) -> None:
            return None

    class Process:
        stdin = Stdin()
        stdout = Stdout()
        stderr = None
        returncode = None

        def poll(self) -> None:
            return None

    transport = SubprocessJsonlTransport(("codex", "app-server"))
    transport._process = Process()  # type: ignore[assignment]
    with pytest.raises(ProviderAdapterError) as error:
        transport.request("initialize", {})
    return error.value
