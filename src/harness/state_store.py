"""Authoritative SQLite Run/Event persistence with a transactional outbox.

The store implements the C-403 ``LifecycleCommitter`` structural protocol.  A
complete immutable ``Run`` snapshot and its matching ``Event`` are validated and
committed with one outbox row before ``commit`` returns.  JSONL delivery is kept
separate so SQLite remains authoritative across delivery interruption.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from harness.state import Event, Run

STORE_SCHEMA_VERSION = "1"
MAX_RUN_JSON_BYTES = 256 * 1024
MAX_EVENT_JSON_BYTES = 64 * 1024


class StateStoreError(RuntimeError):
    """Base class for durable-state failures."""


class StateConflictError(StateStoreError):
    """A write is stale, out of sequence, or conflicts with committed state."""


class StateStoreCorruptionError(StateStoreError):
    """Persisted bytes cannot be decoded as the accepted typed contracts."""


class InlinePayloadTooLargeError(StateStoreError):
    """A typed payload is too large and must be stored as a referenced file."""


@dataclass(frozen=True, slots=True)
class OutboxRecord:
    """One complete committed event awaiting or recording JSONL delivery."""

    outbox_id: int
    run_id: str
    event_seq: int
    transition_id: str | None
    state_sha256: str
    event_sha256: str
    event_json: str
    event: Event
    delivered_at: datetime | None


def canonical_json(value: dict[str, object]) -> str:
    """Return the single canonical UTF-8 JSON representation used durably."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_event_json(event: Event) -> str:
    """Serialize one accepted Event without embedding non-contract data."""

    if type(event) is not Event:
        raise TypeError("event must be an Event")
    return canonical_json(event.to_dict())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _format_timestamp(value: datetime) -> str:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise TypeError("timestamp must be a timezone-aware datetime")
    normalized = value.astimezone(UTC)
    timespec = "microseconds" if normalized.microsecond else "seconds"
    return normalized.isoformat(timespec=timespec).replace("+00:00", "Z")


def _parse_timestamp(value: object, *, location: str) -> datetime:
    if type(value) is not str:
        raise StateStoreCorruptionError(f"{location} must be an RFC 3339 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StateStoreCorruptionError(f"{location} is not a valid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise StateStoreCorruptionError(f"{location} must include a timezone offset")
    return parsed.astimezone(UTC)


def _decode_object(value: object, *, location: str) -> dict[str, object]:
    if type(value) is not str:
        raise StateStoreCorruptionError(f"{location} must be stored as text")
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise StateStoreCorruptionError(f"{location} contains invalid JSON") from exc
    if type(decoded) is not dict or any(type(key) is not str for key in decoded):
        raise StateStoreCorruptionError(f"{location} must contain a JSON object")
    return cast(dict[str, object], decoded)


class SQLiteStateStore:
    """SQLite-authoritative state and outbox implementation for C-406."""

    def __init__(self, database_path: Path, *, timeout_seconds: float = 5.0) -> None:
        if not isinstance(database_path, Path):
            raise TypeError("database_path must be a pathlib.Path")
        if type(timeout_seconds) not in (int, float) or isinstance(timeout_seconds, bool):
            raise TypeError("timeout_seconds must be a number")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._database_path = database_path.resolve(strict=False)
        self._timeout_seconds = float(timeout_seconds)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @property
    def database_path(self) -> Path:
        return self._database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path,
            timeout=self._timeout_seconds,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {int(self._timeout_seconds * 1000)}")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS runs (
                        run_id TEXT PRIMARY KEY,
                        event_seq INTEGER NOT NULL CHECK (event_seq >= 1),
                        lifecycle_state TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        state_json TEXT NOT NULL,
                        state_sha256 TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS outbox (
                        outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id TEXT NOT NULL,
                        event_seq INTEGER NOT NULL CHECK (event_seq >= 1),
                        transition_id TEXT,
                        state_sha256 TEXT NOT NULL,
                        event_json TEXT NOT NULL,
                        event_sha256 TEXT NOT NULL,
                        delivered_at TEXT,
                        FOREIGN KEY (run_id) REFERENCES runs(run_id),
                        UNIQUE (run_id, event_seq),
                        UNIQUE (transition_id)
                    );
                    CREATE INDEX IF NOT EXISTS outbox_pending_order
                    ON outbox(delivered_at, outbox_id);
                    """
                )
                existing = connection.execute(
                    "SELECT value FROM metadata WHERE key = 'schema_version'"
                ).fetchone()
                if existing is None:
                    connection.execute(
                        "INSERT INTO metadata(key, value) VALUES('schema_version', ?)",
                        (STORE_SCHEMA_VERSION,),
                    )
                elif existing["value"] != STORE_SCHEMA_VERSION:
                    raise StateStoreError(
                        "unsupported state-store schema version "
                        f"{existing['value']!r}; expected {STORE_SCHEMA_VERSION!r}"
                    )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    def commit(self, *, run: Run, event: Event) -> None:
        """Atomically persist one matching Run/Event pair and complete outbox row."""

        self._validate_pair(run=run, event=event)
        state_json = canonical_json(run.to_dict())
        event_json = canonical_event_json(event)
        state_bytes = len(state_json.encode("utf-8"))
        event_bytes = len(event_json.encode("utf-8"))
        if state_bytes > MAX_RUN_JSON_BYTES:
            raise InlinePayloadTooLargeError(
                f"Run JSON is {state_bytes} bytes; store large values as referenced files"
            )
        if event_bytes > MAX_EVENT_JSON_BYTES:
            raise InlinePayloadTooLargeError(
                f"Event JSON is {event_bytes} bytes; store large values as referenced files"
            )
        state_sha256 = _sha256_text(state_json)
        event_sha256 = _sha256_text(event_json)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                duplicate = connection.execute(
                    """
                    SELECT state_sha256, event_sha256
                    FROM outbox WHERE run_id = ? AND event_seq = ?
                    """,
                    (run.run_id, run.event_seq),
                ).fetchone()
                if duplicate is not None:
                    if (
                        duplicate["state_sha256"] == state_sha256
                        and duplicate["event_sha256"] == event_sha256
                    ):
                        current_hash = connection.execute(
                            "SELECT state_sha256 FROM runs WHERE run_id = ?",
                            (run.run_id,),
                        ).fetchone()
                        if current_hash is None or current_hash["state_sha256"] != state_sha256:
                            raise StateConflictError(
                                "the exact event is committed but authoritative Run state "
                                "has already advanced"
                            )
                        connection.commit()
                        return
                    raise StateConflictError(
                        f"run {run.run_id!r} event_seq {run.event_seq} conflicts with outbox"
                    )

                if event.transition_id is not None:
                    transition = connection.execute(
                        """
                        SELECT run_id, event_seq, event_sha256
                        FROM outbox WHERE transition_id = ?
                        """,
                        (event.transition_id,),
                    ).fetchone()
                    if transition is not None:
                        raise StateConflictError(
                            f"transition_id {event.transition_id!r} is already committed to "
                            f"run {transition['run_id']!r} event_seq {transition['event_seq']}"
                        )

                current_row = connection.execute(
                    "SELECT state_json, state_sha256 FROM runs WHERE run_id = ?", (run.run_id,)
                ).fetchone()
                if current_row is None:
                    if run.event_seq != 1:
                        raise StateConflictError(
                            "a new run must begin with event_seq 1; earlier authoritative "
                            "state cannot be invented"
                        )
                else:
                    current = self._run_from_json(
                        current_row["state_json"],
                        expected_sha256=current_row["state_sha256"],
                    )
                    self._validate_successor(current=current, run=run, event=event)

                connection.execute(
                    """
                    INSERT INTO runs(
                        run_id, event_seq, lifecycle_state, updated_at,
                        state_json, state_sha256
                    ) VALUES(?, ?, ?, ?, ?, ?)
                    ON CONFLICT(run_id) DO UPDATE SET
                        event_seq = excluded.event_seq,
                        lifecycle_state = excluded.lifecycle_state,
                        updated_at = excluded.updated_at,
                        state_json = excluded.state_json,
                        state_sha256 = excluded.state_sha256
                    """,
                    (
                        run.run_id,
                        run.event_seq,
                        run.lifecycle_state.value,
                        _format_timestamp(run.updated_at),
                        state_json,
                        state_sha256,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO outbox(
                        run_id, event_seq, transition_id, state_sha256,
                        event_json, event_sha256, delivered_at
                    ) VALUES(?, ?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        run.run_id,
                        run.event_seq,
                        event.transition_id,
                        state_sha256,
                        event_json,
                        event_sha256,
                    ),
                )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    @staticmethod
    def _validate_pair(*, run: Run, event: Event) -> None:
        if type(run) is not Run:
            raise TypeError("run must be a Run")
        if type(event) is not Event:
            raise TypeError("event must be an Event")
        if event.run_id != run.run_id:
            raise StateConflictError("Run/Event run_id values must match")
        if event.event_seq != run.event_seq:
            raise StateConflictError("Run/Event event_seq values must match")
        if event.timestamp != run.updated_at:
            raise StateConflictError("Event.timestamp must equal Run.updated_at")
        if event.task_id != run.current_task_id:
            raise StateConflictError("Event.task_id must equal Run.current_task_id")
        if event.transition_id is None:
            if event.next_state is not None:
                raise StateConflictError("a non-transition Event cannot set next_state")
        else:
            if run.last_transition_id != event.transition_id:
                raise StateConflictError("Run.last_transition_id must equal Event.transition_id")
            if event.next_state is not run.lifecycle_state:
                raise StateConflictError("Event.next_state must equal Run.lifecycle_state")

    @staticmethod
    def _validate_successor(*, current: Run, run: Run, event: Event) -> None:
        if run.event_seq != current.event_seq + 1:
            raise StateConflictError(
                f"expected event_seq {current.event_seq + 1}, received {run.event_seq}"
            )
        stable_fields = (
            "run_id",
            "goal_id",
            "provider",
            "model",
            "reasoning_effort",
            "provider_config_ref",
            "started_at",
        )
        changed = [name for name in stable_fields if getattr(current, name) != getattr(run, name)]
        if changed:
            raise StateConflictError(f"immutable Run identity changed: {changed!r}")
        if run.updated_at < current.updated_at:
            raise StateConflictError("Run.updated_at cannot move backwards")
        if event.transition_id is None:
            if run.lifecycle_state is not current.lifecycle_state:
                raise StateConflictError("a non-transition Event cannot change lifecycle state")
            if run.last_transition_id != current.last_transition_id:
                raise StateConflictError("a non-transition Event cannot change last_transition_id")
        elif event.prior_state is not current.lifecycle_state:
            raise StateConflictError(
                "Event.prior_state does not match authoritative lifecycle state"
            )

    @staticmethod
    def _run_from_json(value: object, *, expected_sha256: object) -> Run:
        if type(value) is not str or type(expected_sha256) is not str:
            raise StateStoreCorruptionError("runs state JSON/hash columns must be text")
        if _sha256_text(value) != expected_sha256:
            raise StateStoreCorruptionError("runs.state_json does not match state_sha256")
        try:
            return Run.from_dict(_decode_object(value, location="runs.state_json"))
        except (TypeError, ValueError) as exc:
            raise StateStoreCorruptionError("runs.state_json violates the Run contract") from exc

    @staticmethod
    def _event_from_json(value: object, *, expected_sha256: object) -> Event:
        if type(value) is not str or type(expected_sha256) is not str:
            raise StateStoreCorruptionError("outbox event JSON/hash columns must be text")
        if _sha256_text(value) != expected_sha256:
            raise StateStoreCorruptionError("outbox.event_json does not match event_sha256")
        try:
            return Event.from_dict(_decode_object(value, location="outbox.event_json"))
        except (TypeError, ValueError) as exc:
            raise StateStoreCorruptionError(
                "outbox.event_json violates the Event contract"
            ) from exc

    def load_run(self, run_id: str) -> Run | None:
        if type(run_id) is not str or not run_id:
            raise TypeError("run_id must be a non-empty string")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json, state_sha256 FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        return (
            None
            if row is None
            else self._run_from_json(row["state_json"], expected_sha256=row["state_sha256"])
        )

    def load_event(self, run_id: str, event_seq: int) -> Event | None:
        if type(run_id) is not str or not run_id:
            raise TypeError("run_id must be a non-empty string")
        if type(event_seq) is not int or event_seq < 1:
            raise TypeError("event_seq must be a positive integer")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT event_json, event_sha256, transition_id
                FROM outbox WHERE run_id = ? AND event_seq = ?
                """,
                (run_id, event_seq),
            ).fetchone()
        if row is None:
            return None
        event = self._event_from_json(row["event_json"], expected_sha256=row["event_sha256"])
        if event.run_id != run_id or event.event_seq != event_seq:
            raise StateStoreCorruptionError("outbox Event identity does not match its row key")
        if event.transition_id != row["transition_id"]:
            raise StateStoreCorruptionError(
                "outbox Event transition_id does not match its indexed column"
            )
        return event

    def pending_outbox(self, *, limit: int | None = None) -> tuple[OutboxRecord, ...]:
        if limit is not None and (type(limit) is not int or limit < 1):
            raise TypeError("limit must be a positive integer or null")
        sql = """
            SELECT outbox_id, run_id, event_seq, transition_id, state_sha256,
                   event_json, event_sha256, delivered_at
            FROM outbox
            WHERE delivered_at IS NULL
            ORDER BY outbox_id
        """
        parameters: tuple[int, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            parameters = (limit,)
        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return tuple(self._outbox_record(row) for row in rows)

    def all_outbox(self) -> tuple[OutboxRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT outbox_id, run_id, event_seq, transition_id, state_sha256,
                       event_json, event_sha256, delivered_at
                FROM outbox ORDER BY outbox_id
                """
            ).fetchall()
        return tuple(self._outbox_record(row) for row in rows)

    def _outbox_record(self, row: sqlite3.Row) -> OutboxRecord:
        delivered = (
            None
            if row["delivered_at"] is None
            else _parse_timestamp(row["delivered_at"], location="outbox.delivered_at")
        )
        event = self._event_from_json(row["event_json"], expected_sha256=row["event_sha256"])
        if event.run_id != row["run_id"] or event.event_seq != row["event_seq"]:
            raise StateStoreCorruptionError("outbox Event identity does not match its row key")
        if event.transition_id != row["transition_id"]:
            raise StateStoreCorruptionError(
                "outbox Event transition_id does not match its indexed column"
            )
        return OutboxRecord(
            outbox_id=cast(int, row["outbox_id"]),
            run_id=cast(str, row["run_id"]),
            event_seq=cast(int, row["event_seq"]),
            transition_id=cast(str | None, row["transition_id"]),
            state_sha256=cast(str, row["state_sha256"]),
            event_sha256=cast(str, row["event_sha256"]),
            event_json=cast(str, row["event_json"]),
            event=event,
            delivered_at=delivered,
        )

    def mark_delivered(self, record: OutboxRecord, *, delivered_at: datetime) -> bool:
        """Mark an exact outbox row delivered; return false if already marked."""

        if type(record) is not OutboxRecord:
            raise TypeError("record must be an OutboxRecord")
        timestamp = _format_timestamp(delivered_at)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    """
                    SELECT run_id, event_seq, state_sha256, event_sha256, delivered_at
                    FROM outbox WHERE outbox_id = ?
                    """,
                    (record.outbox_id,),
                ).fetchone()
                if row is None:
                    raise StateConflictError(f"outbox row {record.outbox_id} no longer exists")
                actual = (
                    row["run_id"],
                    row["event_seq"],
                    row["state_sha256"],
                    row["event_sha256"],
                )
                expected = (
                    record.run_id,
                    record.event_seq,
                    record.state_sha256,
                    record.event_sha256,
                )
                if actual != expected:
                    raise StateConflictError(
                        f"outbox row {record.outbox_id} changed before delivery acknowledgement"
                    )
                if row["delivered_at"] is not None:
                    connection.commit()
                    return False
                connection.execute(
                    "UPDATE outbox SET delivered_at = ? WHERE outbox_id = ?",
                    (timestamp, record.outbox_id),
                )
                connection.commit()
                return True
            except BaseException:
                connection.rollback()
                raise


__all__ = [
    "InlinePayloadTooLargeError",
    "MAX_EVENT_JSON_BYTES",
    "MAX_RUN_JSON_BYTES",
    "OutboxRecord",
    "SQLiteStateStore",
    "StateConflictError",
    "StateStoreCorruptionError",
    "StateStoreError",
    "canonical_event_json",
    "canonical_json",
]
