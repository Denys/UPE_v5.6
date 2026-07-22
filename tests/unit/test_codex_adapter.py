"""C-501 Codex App Server adapter tests using a deterministic fake transport."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

from harness.adapters.base import (
    ApprovalResponse,
    ProviderAdapterError,
    ProviderErrorCategory,
    ProviderEventKind,
    ProviderTurnOutcome,
    SessionHandle,
    TurnHandle,
    TurnRequest,
)
from harness.adapters.codex_app_server import SUPPORTED_PROTOCOL_VERSION, CodexAppServerAdapter
from harness.state import (
    ApprovalStatus,
    BudgetState,
    BudgetValues,
    CompletionVerdict,
    LifecycleState,
    Run,
    Task,
    TaskStatus,
)

NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)


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


@dataclass(slots=True)
class FakeTransport:
    replies: dict[str, list[Mapping[str, Any]]]
    events: dict[str, list[Mapping[str, Any]]] = field(default_factory=dict)
    cursors: dict[str, int] = field(default_factory=dict)
    is_started: bool = False
    calls: list[tuple[str, Mapping[str, Any]]] = field(default_factory=list)

    @property
    def started(self) -> bool:
        return self.is_started

    def start(self) -> None:
        self.is_started = True

    def stop(self) -> None:
        self.is_started = False

    def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append((method, dict(params)))
        queue = self.replies.get(method)
        if not queue:
            raise AssertionError(f"unexpected method {method}")
        return queue.pop(0)

    def iter_events(self, *, turn_id: str) -> Iterator[Mapping[str, Any]]:
        queued = self.events.get(turn_id, [])
        index = self.cursors.get(turn_id, 0)
        while index < len(queued):
            self.cursors[turn_id] = index + 1
            yield queued[index]
            index += 1


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


def ready_replies() -> dict[str, list[Mapping[str, Any]]]:
    return {
        "server.compatibility": [
            {
                "protocol_version": SUPPORTED_PROTOCOL_VERSION,
                "mandatory_capabilities": [
                    "initialize",
                    "thread",
                    "turn",
                    "approval",
                    "cancel",
                    "interrupt",
                    "stream",
                ],
            }
        ],
        "thread.start": [{"thread_id": "thread.c501.001"}],
        "thread.resume": [{"thread_id": "thread.c501.001"}],
        "turn.submit": [{"turn_id": "turn.c501.001"}],
        "approval.respond": [{}],
        "turn.interrupt": [{}],
        "thread.cancel": [{}],
    }


def event(sequence: int, kind: str, **extra: object) -> Mapping[str, Any]:
    raw: dict[str, object] = {
        "event_id": f"event.c501.{sequence}",
        "sequence": sequence,
        "timestamp": f"2026-07-22T12:00:0{sequence}+00:00",
        "turn_id": "turn.c501.001",
        "type": kind,
        "summary": kind,
    }
    raw.update(extra)
    return raw


def prepared_adapter(
    events: list[Mapping[str, Any]] | None = None,
) -> tuple[CodexAppServerAdapter, FakeTransport, SessionHandle, TurnHandle]:
    transport = FakeTransport(ready_replies(), {"turn.c501.001": events or []})
    adapter = CodexAppServerAdapter(transport)
    adapter.start()
    adapter.preflight()
    session = adapter.create_session(run=run_record())
    turn = adapter.submit_turn(
        session=session,
        request=TurnRequest(
            request_id="request.c501.001",
            run=run_record(),
            task=task_record(),
            instructions="Implement C-501 without starting Codex.",
        ),
    )
    return adapter, transport, session, turn


def test_start_stop_preflight_initialize_thread_start_resume_and_turn_submission() -> None:
    adapter, transport, session, turn = prepared_adapter()

    assert adapter.started
    assert adapter.identity.protocol_version == SUPPORTED_PROTOCOL_VERSION
    assert session.session_id == "thread.c501.001"
    assert turn.turn_id == "turn.c501.001"
    resumed = adapter.resume_session(run=run_record(), session_id=session.session_id)
    assert resumed == session
    adapter.stop()
    assert [call[0] for call in transport.calls] == [
        "server.compatibility",
        "thread.start",
        "turn.submit",
        "thread.resume",
    ]


def test_preflight_fails_closed_for_incompatible_or_missing_mandatory_protocol() -> None:
    bad_version = FakeTransport(
        {"server.compatibility": [{"protocol_version": "old", "mandatory_capabilities": []}]}
    )
    adapter = CodexAppServerAdapter(bad_version)
    adapter.start()
    with pytest.raises(ProviderAdapterError) as incompatible:
        adapter.preflight()
    assert incompatible.value.category is ProviderErrorCategory.COMPATIBILITY

    missing = FakeTransport(
        {
            "server.compatibility": [
                {
                    "protocol_version": SUPPORTED_PROTOCOL_VERSION,
                    "mandatory_capabilities": ["initialize"],
                }
            ]
        }
    )
    adapter = CodexAppServerAdapter(missing)
    adapter.start()
    with pytest.raises(ProviderAdapterError, match="missing mandatory"):
        adapter.preflight()


def test_stream_translation_terminal_detection_and_exactly_once_ordering() -> None:
    adapter, _, _, turn = prepared_adapter(
        [
            event(1, "turn.started"),
            event(2, "message.output", output_refs=["provider://output/1"]),
            event(3, "action.started", input_refs=["provider://action/1"]),
            event(4, "turn.completed", evidence_refs=["provider://terminal/1"]),
        ]
    )

    events = tuple(adapter.stream_events(turn=turn))
    assert [item.kind for item in events] == [
        ProviderEventKind.TURN_STARTED,
        ProviderEventKind.OUTPUT,
        ProviderEventKind.ACTION,
        ProviderEventKind.TURN_TERMINAL,
    ]
    assert events[-1].outcome is ProviderTurnOutcome.SUCCEEDED
    assert tuple(adapter.stream_events(turn=turn)) == ()


def test_approval_blocks_segment_and_response_allows_remaining_stream() -> None:
    adapter, transport, _, turn = prepared_adapter(
        [
            event(1, "turn.started"),
            event(
                2,
                "approval.required",
                approval={
                    "approval_id": "approval.c501.001",
                    "action_class": "WRITE",
                    "summary": "write file",
                },
            ),
            event(3, "turn.completed"),
        ]
    )

    first = tuple(adapter.stream_events(turn=turn))
    assert first[-1].kind is ProviderEventKind.APPROVAL_REQUIRED
    adapter.respond_to_approval(
        turn=turn,
        response=ApprovalResponse(
            approval_id="approval.c501.001",
            decision=ApprovalStatus.GRANTED,
            reason="test approval",
        ),
    )
    assert transport.calls[-1][0] == "approval.respond"
    assert tuple(adapter.stream_events(turn=turn))[-1].outcome is ProviderTurnOutcome.SUCCEEDED


def test_interrupt_cancel_and_provider_failure_normalization() -> None:
    adapter, transport, session, turn = prepared_adapter(
        [
            event(1, "turn.started"),
            event(
                2,
                "turn.failed",
                failure={
                    "category": "transient",
                    "message": "provider failed",
                    "retryable": True,
                    "code": "E_TEMP",
                },
            ),
        ]
    )

    adapter.interrupt(turn=turn, reason="operator interrupt")
    adapter.cancel(session=session, reason="operator cancel")
    events = tuple(adapter.stream_events(turn=turn))
    assert [call[0] for call in transport.calls][-2:] == ["turn.interrupt", "thread.cancel"]
    assert events[-1].outcome is ProviderTurnOutcome.FAILED
    assert events[-1].failure is not None
    assert events[-1].failure.category is ProviderErrorCategory.TRANSIENT
    assert events[-1].failure.retryable


@pytest.mark.parametrize(
    "bad_events, message",
    [
        ([event(1, "future.required")], "unknown mandatory"),
        ([event(2, "turn.started")], "sequence gap"),
        ([event(1, "turn.started"), event(1, "message.output")], "duplicate"),
        (
            [event(1, "turn.started", unknown_mandatory=["field.x"])],
            "unknown mandatory protocol field",
        ),
        ([{"event_id": "event.c501.bad", "sequence": 1, "type": "turn.started"}], "timestamp"),
    ],
)
def test_malformed_unknown_mandatory_and_out_of_order_stream_fail_closed(
    bad_events: list[Mapping[str, Any]], message: str
) -> None:
    adapter, _, _, turn = prepared_adapter(bad_events)

    with pytest.raises(ProviderAdapterError, match=message) as error:
        tuple(adapter.stream_events(turn=turn))
    assert error.value.category is ProviderErrorCategory.PROTOCOL


def test_state_guards_reject_duplicate_requests_forged_handles_and_bad_approvals() -> None:
    adapter, _, session, turn = prepared_adapter(
        [
            event(
                1,
                "approval.required",
                approval={
                    "approval_id": "approval.c501.001",
                    "action_class": "WRITE",
                    "summary": "write",
                },
            )
        ]
    )

    with pytest.raises(ProviderAdapterError, match="duplicate request id"):
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
                    request_id=turn.request_id,
                    run_id=turn.run_id,
                    task_id=turn.task_id,
                )
            )
        )

    tuple(adapter.stream_events(turn=turn))
    with pytest.raises(ProviderAdapterError, match="approval id mismatch"):
        adapter.respond_to_approval(
            turn=turn,
            response=ApprovalResponse(
                approval_id="approval.other", decision=ApprovalStatus.DENIED, reason="no"
            ),
        )
