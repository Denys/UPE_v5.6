"""Provider-neutral adapter contracts and deterministic test adapter."""

from .base import (
    AdapterIdentity,
    ApprovalRequest,
    ApprovalResponse,
    ProviderAdapter,
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
from .fake import (
    DEFAULT_FAKE_BASE_TIME,
    DEFAULT_FAKE_IDENTITY,
    FakeAdapter,
    FakeEventSpec,
    FakeOperation,
    FakeOperationKind,
    FakeTurnScript,
)

__all__ = [
    "DEFAULT_FAKE_BASE_TIME",
    "DEFAULT_FAKE_IDENTITY",
    "AdapterIdentity",
    "ApprovalRequest",
    "ApprovalResponse",
    "FakeAdapter",
    "FakeEventSpec",
    "FakeOperation",
    "FakeOperationKind",
    "FakeTurnScript",
    "ProviderAdapter",
    "ProviderAdapterError",
    "ProviderErrorCategory",
    "ProviderEvent",
    "ProviderEventKind",
    "ProviderFailure",
    "ProviderTurnOutcome",
    "SessionHandle",
    "TurnHandle",
    "TurnRequest",
]
