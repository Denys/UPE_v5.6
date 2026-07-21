"""Durable append-only JSONL mirror for committed SQLite outbox events."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from harness.state import Event
from harness.state_store import OutboxRecord, SQLiteStateStore, canonical_event_json

EventKey = tuple[str, int]
DeliveryClock = Callable[[], datetime]


class EventMirrorError(RuntimeError):
    """Base class for JSONL mirror failures."""


class EventMirrorCorruptionError(EventMirrorError):
    """The append-only mirror contains invalid, partial, or conflicting data."""


class EventMirrorChangedError(EventMirrorError):
    """The mirror changed after inspection and cannot be appended safely."""


@dataclass(frozen=True, slots=True)
class DeliverySummary:
    """Result of one pending-outbox delivery pass."""

    inspected: int
    appended: int
    acknowledged: int


def _utc_now() -> datetime:
    return datetime.now(UTC)


class JsonlEventMirror:
    """Append and replay complete canonical Event records without inventing state."""

    def __init__(self, path: Path, *, clock: DeliveryClock = _utc_now) -> None:
        if not isinstance(path, Path):
            raise TypeError("path must be a pathlib.Path")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._path = path.resolve(strict=False)
        self._clock = clock
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def read_events(self) -> tuple[Event, ...]:
        """Read and validate the complete append-only mirror in file order."""

        records, _, events = self._scan()
        if len(records) != len(events):
            raise EventMirrorCorruptionError("the JSONL mirror contains duplicate event keys")
        return tuple(events)

    def deliver_pending(
        self,
        store: SQLiteStateStore,
        *,
        limit: int | None = None,
    ) -> DeliverySummary:
        """Durably append pending rows, then acknowledge the exact SQLite rows."""

        if type(store) is not SQLiteStateStore:
            raise TypeError("store must be a SQLiteStateStore")
        pending = store.pending_outbox(limit=limit)
        if not pending:
            return DeliverySummary(inspected=0, appended=0, acknowledged=0)

        existing, expected_size, _ = self._scan()
        appended = 0
        acknowledged = 0
        for record in pending:
            key = (record.run_id, record.event_seq)
            existing_json = existing.get(key)
            if existing_json is not None:
                if existing_json != record.event_json:
                    raise EventMirrorCorruptionError(
                        f"JSONL event {key!r} conflicts with authoritative SQLite outbox"
                    )
            else:
                actual_size = self._path.stat().st_size if self._path.exists() else 0
                if actual_size != expected_size:
                    raise EventMirrorChangedError(
                        "JSONL mirror changed after inspection; exclusive run ownership is required"
                    )
                encoded = (record.event_json + "\n").encode("utf-8")
                with self._path.open("ab", buffering=0) as stream:
                    written = stream.write(encoded)
                    if written != len(encoded):
                        raise EventMirrorError(
                            f"short JSONL write: expected {len(encoded)}, wrote {written}"
                        )
                    stream.flush()
                    os.fsync(stream.fileno())
                expected_size += len(encoded)
                existing[key] = record.event_json
                appended += 1
                self._after_durable_append(record)

            if store.mark_delivered(record, delivered_at=self._clock()):
                acknowledged += 1

        return DeliverySummary(
            inspected=len(pending),
            appended=appended,
            acknowledged=acknowledged,
        )

    def _after_durable_append(self, record: OutboxRecord) -> None:
        """Deterministic interruption seam after fsync and before acknowledgement."""

    def _scan(self) -> tuple[dict[EventKey, str], int, list[Event]]:
        if not self._path.exists():
            return {}, 0, []
        records: dict[EventKey, str] = {}
        events: list[Event] = []
        total_size = 0
        with self._path.open("rb") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                total_size += len(raw_line)
                if not raw_line.endswith(b"\n"):
                    raise EventMirrorCorruptionError(
                        f"JSONL line {line_number} is partial and cannot be replayed"
                    )
                encoded = raw_line[:-1]
                if not encoded:
                    raise EventMirrorCorruptionError(f"JSONL line {line_number} must not be empty")
                try:
                    text = encoded.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise EventMirrorCorruptionError(
                        f"JSONL line {line_number} is not UTF-8"
                    ) from exc
                try:
                    value = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise EventMirrorCorruptionError(
                        f"JSONL line {line_number} contains invalid JSON"
                    ) from exc
                if type(value) is not dict or any(type(key) is not str for key in value):
                    raise EventMirrorCorruptionError(
                        f"JSONL line {line_number} must contain one JSON object"
                    )
                try:
                    event = Event.from_dict(cast(dict[str, object], value))
                except (TypeError, ValueError) as exc:
                    raise EventMirrorCorruptionError(
                        f"JSONL line {line_number} violates the Event contract"
                    ) from exc
                canonical = canonical_event_json(event)
                if text != canonical:
                    raise EventMirrorCorruptionError(f"JSONL line {line_number} is not canonical")
                key = (event.run_id, event.event_seq)
                if key in records:
                    raise EventMirrorCorruptionError(
                        f"JSONL line {line_number} duplicates event {key!r}"
                    )
                records[key] = canonical
                events.append(event)
        return records, total_size, events


__all__ = [
    "DeliverySummary",
    "EventMirrorChangedError",
    "EventMirrorCorruptionError",
    "EventMirrorError",
    "JsonlEventMirror",
]
