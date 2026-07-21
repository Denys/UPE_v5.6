"""Fail-closed task workspace ownership and cleanup-target verification.

This module deliberately performs no Git creation/removal and no filesystem
deletion.  It validates already-materialized worktrees through an injected,
read-only Git inspector and produces an explicit cleanup target for a separate
approval/policy boundary.
"""

from __future__ import annotations

import os
import re
import stat as stat_module
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from typing import Protocol, runtime_checkable

_TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_OBJECT_ID = re.compile(r"[0-9a-fA-F]{40,64}\Z")
_WINDOWS_DRIVE = re.compile(r"[A-Za-z]:\Z")
_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CLOCK$"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)
_REPARSE_POINT = getattr(stat_module, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class WorkspaceError(RuntimeError):
    """Base class for fail-closed workspace contract failures."""


class UnsafeWorkspacePathError(WorkspaceError):
    """A path is not an exact safe Windows-local target."""


class WorkspaceIdentityError(WorkspaceError):
    """A configured root or assigned workspace changed filesystem identity."""


class WorktreeInventoryError(WorkspaceError):
    """Git worktree inventory is missing, ambiguous, locked, or drifted."""


class WorkspaceOwnershipError(WorkspaceError):
    """Task/workspace ownership is absent, conflicting, or stale."""


class DirtyWorkspaceError(WorkspaceError):
    """Cleanup was refused because tracked or untracked data is present."""


@dataclass(frozen=True, slots=True)
class FilesystemIdentity:
    """Stable identity fields available from a Windows directory handle/stat."""

    device: int
    inode: int

    @classmethod
    def capture(cls, path: Path) -> FilesystemIdentity:
        result = path.stat(follow_symlinks=False)
        return cls(device=result.st_dev, inode=result.st_ino)


@dataclass(frozen=True, slots=True, kw_only=True)
class GitWorktree:
    """One normalized record supplied by a read-only Git inventory adapter."""

    path: Path
    head: str
    branch: str | None = None
    locked: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("GitWorktree.path must be a Path")
        if not _OBJECT_ID.fullmatch(self.head):
            raise ValueError("GitWorktree.head must be a 40-64 character hexadecimal object ID")
        if self.branch is not None and (not self.branch or "\x00" in self.branch):
            raise ValueError("GitWorktree.branch must be a non-empty NUL-free string")


@dataclass(frozen=True, slots=True, kw_only=True)
class GitStatus:
    """Lossless dirty-state categories; paths are reported, never cleaned."""

    staged: tuple[str, ...] = ()
    unstaged: tuple[str, ...] = ()
    untracked: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for category in (self.staged, self.unstaged, self.untracked):
            if not isinstance(category, tuple):
                raise TypeError("GitStatus categories must be tuples")
            if any(not item or "\x00" in item for item in category):
                raise ValueError("GitStatus paths must be non-empty NUL-free strings")

    @property
    def clean(self) -> bool:
        return not (self.staged or self.unstaged or self.untracked)

    def summary(self) -> str:
        return (
            f"staged={len(self.staged)}, unstaged={len(self.unstaged)}, "
            f"untracked={len(self.untracked)}"
        )


@runtime_checkable
class GitWorkspaceInspector(Protocol):
    """Read-only Git boundary; implementations may inspect but never mutate."""

    def list_worktrees(self, repository_root: Path) -> tuple[GitWorktree, ...]: ...

    def status(self, workspace: Path) -> GitStatus: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkspaceAssignment:
    """Exact in-memory ownership of one registered worktree by one task."""

    task_id: str
    workspace: Path
    root_identity: FilesystemIdentity
    workspace_identity: FilesystemIdentity
    git_head: str
    git_branch: str | None
    owner_token: str
    observed_status: GitStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class CleanupTarget:
    """Explicit cleanup candidate, still requiring immediate revalidation."""

    task_id: str
    workspace: Path
    root_identity: FilesystemIdentity
    workspace_identity: FilesystemIdentity
    git_head: str
    git_branch: str | None
    owner_token: str
    verified_status: GitStatus


def _validate_task_id(task_id: str) -> str:
    if not isinstance(task_id, str):
        raise TypeError("task_id must be a string")
    if not _TASK_ID.fullmatch(task_id) or task_id in {".", ".."}:
        raise WorkspaceOwnershipError("task_id must be a stable path-free identifier")
    return task_id


def _windows_lexical_path(path: Path, *, label: str) -> PureWindowsPath:
    if not isinstance(path, Path):
        raise TypeError(f"{label} must be a Path")
    raw = str(path)
    if not raw or "\x00" in raw:
        raise UnsafeWorkspacePathError(f"{label} must be non-empty and NUL-free")
    normalized_separators = raw.replace("/", "\\")
    lowered = normalized_separators.casefold()
    if lowered.startswith(("\\\\?\\", "\\\\.\\", "\\??\\")):
        raise UnsafeWorkspacePathError(f"{label} uses a Windows device namespace")
    pure = PureWindowsPath(normalized_separators)
    if not pure.is_absolute() or not _WINDOWS_DRIVE.fullmatch(pure.drive):
        raise UnsafeWorkspacePathError(f"{label} must be an absolute drive-local Windows path")
    if pure.drive.startswith("\\"):
        raise UnsafeWorkspacePathError(f"{label} must not be a UNC path")
    if any(character in raw for character in "*?[]"):
        raise UnsafeWorkspacePathError(f"{label} must not contain glob syntax")
    if "%" in raw or "$" in raw:
        raise UnsafeWorkspacePathError(f"{label} must not contain environment expansion syntax")
    if ":" in normalized_separators[2:]:
        raise UnsafeWorkspacePathError(f"{label} must not contain an alternate data stream")

    tail = normalized_separators[len(pure.anchor) :]
    segments = tuple(part for part in re.split(r"\\+", tail) if part)
    if any(part in {".", ".."} for part in segments):
        raise UnsafeWorkspacePathError(f"{label} must not contain traversal components")
    for part in segments:
        if part.endswith((" ", ".")):
            raise UnsafeWorkspacePathError(f"{label} contains a trailing-dot/space component")
        stem = part.split(".", maxsplit=1)[0].upper()
        if stem in _RESERVED_NAMES:
            raise UnsafeWorkspacePathError(f"{label} contains a reserved Windows device name")
    return pure


def _path_key(path: Path, *, label: str) -> str:
    pure = _windows_lexical_path(path, label=label)
    return str(pure).casefold().rstrip("\\")


def _existing_components(path: Path) -> tuple[Path, ...]:
    anchor = Path(path.anchor)
    components: list[Path] = [anchor]
    current = anchor
    for part in path.parts[1:]:
        current /= part
        components.append(current)
    return tuple(components)


def _reject_reparse_components(path: Path, *, label: str) -> None:
    for component in _existing_components(path):
        if not os.path.lexists(component):
            raise UnsafeWorkspacePathError(f"{label} has a missing path component: {component}")
        result = component.stat(follow_symlinks=False)
        attributes = getattr(result, "st_file_attributes", 0)
        if component.is_symlink() or attributes & _REPARSE_POINT:
            raise UnsafeWorkspacePathError(f"{label} contains a reparse point: {component}")


def _safe_existing_directory(path: Path, *, label: str) -> tuple[Path, FilesystemIdentity]:
    _windows_lexical_path(path, label=label)
    _reject_reparse_components(path, label=label)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise UnsafeWorkspacePathError(f"{label} cannot be resolved: {exc}") from exc
    if not resolved.is_dir():
        raise UnsafeWorkspacePathError(f"{label} must be an existing directory")
    if _path_key(resolved, label=f"resolved {label}") != _path_key(path, label=label):
        raise UnsafeWorkspacePathError(f"{label} did not resolve to its exact lexical location")
    return resolved, FilesystemIdentity.capture(resolved)


def _is_same_or_descendant(candidate: Path, root: Path) -> bool:
    candidate_key = _path_key(candidate, label="candidate path")
    root_key = _path_key(root, label="root path")
    return candidate_key == root_key or candidate_key.startswith(f"{root_key}\\")


class WorkspaceManager:
    """Own already-created worktrees without exposing cleanup effects."""

    def __init__(
        self,
        *,
        repository_root: Path,
        worktree_root: Path,
        git: GitWorkspaceInspector,
    ) -> None:
        if not isinstance(git, GitWorkspaceInspector):
            raise TypeError("git must implement GitWorkspaceInspector")
        repository, repository_identity = _safe_existing_directory(
            repository_root, label="repository_root"
        )
        worktrees, worktree_identity = _safe_existing_directory(
            worktree_root, label="worktree_root"
        )
        if _is_same_or_descendant(repository, worktrees) or _is_same_or_descendant(
            worktrees, repository
        ):
            raise UnsafeWorkspacePathError("repository_root and worktree_root must not overlap")
        self._repository_root = repository
        self._repository_identity = repository_identity
        self._worktree_root = worktrees
        self._worktree_root_identity = worktree_identity
        self._git = git
        self._assignments: dict[str, WorkspaceAssignment] = {}
        self._task_by_workspace: dict[str, str] = {}

    @property
    def repository_root(self) -> Path:
        return self._repository_root

    @property
    def worktree_root(self) -> Path:
        return self._worktree_root

    def _assert_root_identities(self) -> None:
        repository, repository_identity = _safe_existing_directory(
            self._repository_root, label="repository_root"
        )
        worktrees, worktree_identity = _safe_existing_directory(
            self._worktree_root, label="worktree_root"
        )
        if repository_identity != self._repository_identity:
            raise WorkspaceIdentityError("repository_root filesystem identity changed")
        if worktree_identity != self._worktree_root_identity:
            raise WorkspaceIdentityError("worktree_root filesystem identity changed")
        if repository != self._repository_root or worktrees != self._worktree_root:
            raise WorkspaceIdentityError("configured root canonical path changed")

    def _inspect_workspace(self, workspace: Path) -> tuple[Path, FilesystemIdentity]:
        self._assert_root_identities()
        candidate, identity = _safe_existing_directory(workspace, label="workspace")
        if candidate.parent != self._worktree_root:
            raise UnsafeWorkspacePathError(
                "workspace must be an exact direct child of worktree_root"
            )
        return candidate, identity

    def _registered_worktree(self, workspace: Path) -> GitWorktree:
        records = self._git.list_worktrees(self._repository_root)
        if not isinstance(records, tuple):
            raise TypeError("GitWorkspaceInspector.list_worktrees must return a tuple")
        workspace_key = _path_key(workspace, label="workspace")
        matches: list[GitWorktree] = []
        for record in records:
            if not isinstance(record, GitWorktree):
                raise TypeError("worktree inventory contains a non-GitWorktree record")
            record_key = _path_key(record.path, label="Git worktree path")
            if record_key == workspace_key:
                matches.append(record)
        if not matches:
            raise WorktreeInventoryError("workspace is not a registered Git worktree")
        if len(matches) != 1:
            raise WorktreeInventoryError("workspace has ambiguous duplicate Git worktree records")
        record = matches[0]
        if record.locked:
            raise WorktreeInventoryError("workspace Git worktree is locked")
        return record

    def _owner_token(
        self,
        *,
        task_id: str,
        workspace: Path,
        workspace_identity: FilesystemIdentity,
        worktree: GitWorktree,
    ) -> str:
        fields = (
            task_id,
            _path_key(workspace, label="workspace"),
            str(self._worktree_root_identity.device),
            str(self._worktree_root_identity.inode),
            str(workspace_identity.device),
            str(workspace_identity.inode),
            worktree.head.lower(),
            worktree.branch or "",
        )
        return sha256("\0".join(fields).encode("utf-8")).hexdigest()

    def assign(self, *, task_id: str, workspace: Path) -> WorkspaceAssignment:
        """Bind one task to one exact existing registered worktree."""

        task_id = _validate_task_id(task_id)
        candidate, identity = self._inspect_workspace(workspace)
        candidate_key = _path_key(candidate, label="workspace")
        existing_task = self._task_by_workspace.get(candidate_key)
        if existing_task is not None and existing_task != task_id:
            raise WorkspaceOwnershipError("workspace is already assigned to another task")
        existing_assignment = self._assignments.get(task_id)
        if existing_assignment is not None and existing_assignment.workspace != candidate:
            raise WorkspaceOwnershipError("task is already assigned to another workspace")

        worktree = self._registered_worktree(candidate)
        status = self._git.status(candidate)
        if not isinstance(status, GitStatus):
            raise TypeError("GitWorkspaceInspector.status must return GitStatus")
        owner_token = self._owner_token(
            task_id=task_id,
            workspace=candidate,
            workspace_identity=identity,
            worktree=worktree,
        )
        assignment = WorkspaceAssignment(
            task_id=task_id,
            workspace=candidate,
            root_identity=self._worktree_root_identity,
            workspace_identity=identity,
            git_head=worktree.head.lower(),
            git_branch=worktree.branch,
            owner_token=owner_token,
            observed_status=status,
        )
        if existing_assignment is not None and existing_assignment != assignment:
            raise WorkspaceOwnershipError("existing task assignment drifted")
        self._assignments[task_id] = assignment
        self._task_by_workspace[candidate_key] = task_id
        return assignment

    def _verify_assignment(
        self, *, task_id: str, workspace: Path, owner_token: str
    ) -> tuple[WorkspaceAssignment, GitStatus]:
        task_id = _validate_task_id(task_id)
        assignment = self._assignments.get(task_id)
        if assignment is None:
            raise WorkspaceOwnershipError("task has no workspace assignment")
        candidate, identity = self._inspect_workspace(workspace)
        if candidate != assignment.workspace:
            raise WorkspaceOwnershipError("cleanup workspace does not match task assignment")
        if identity != assignment.workspace_identity:
            raise WorkspaceIdentityError("assigned workspace filesystem identity changed")
        if owner_token != assignment.owner_token:
            raise WorkspaceOwnershipError("cleanup owner token does not match assignment")
        if self._task_by_workspace.get(_path_key(candidate, label="workspace")) != task_id:
            raise WorkspaceOwnershipError("workspace reverse ownership mapping changed")

        worktree = self._registered_worktree(candidate)
        if worktree.head.lower() != assignment.git_head:
            raise WorktreeInventoryError("workspace Git HEAD changed after assignment")
        if worktree.branch != assignment.git_branch:
            raise WorktreeInventoryError("workspace Git branch changed after assignment")
        expected_token = self._owner_token(
            task_id=task_id,
            workspace=candidate,
            workspace_identity=identity,
            worktree=worktree,
        )
        if expected_token != owner_token:
            raise WorkspaceOwnershipError("cleanup ownership identity no longer verifies")
        status = self._git.status(candidate)
        if not isinstance(status, GitStatus):
            raise TypeError("GitWorkspaceInspector.status must return GitStatus")
        return assignment, status

    def prepare_cleanup(self, *, task_id: str, workspace: Path) -> CleanupTarget:
        """Resolve a clean owned target; do not remove or modify anything."""

        assignment = self._assignments.get(task_id)
        if assignment is None:
            raise WorkspaceOwnershipError("task has no workspace assignment")
        verified, status = self._verify_assignment(
            task_id=task_id,
            workspace=workspace,
            owner_token=assignment.owner_token,
        )
        if not status.clean:
            raise DirtyWorkspaceError(f"cleanup refused for dirty workspace ({status.summary()})")
        return CleanupTarget(
            task_id=verified.task_id,
            workspace=verified.workspace,
            root_identity=verified.root_identity,
            workspace_identity=verified.workspace_identity,
            git_head=verified.git_head,
            git_branch=verified.git_branch,
            owner_token=verified.owner_token,
            verified_status=status,
        )

    def verify_cleanup_target(self, target: CleanupTarget) -> CleanupTarget:
        """Immediately revalidate an explicit target before a separate cleanup effect."""

        if not isinstance(target, CleanupTarget):
            raise TypeError("target must be a CleanupTarget")
        assignment, status = self._verify_assignment(
            task_id=target.task_id,
            workspace=target.workspace,
            owner_token=target.owner_token,
        )
        expected = CleanupTarget(
            task_id=assignment.task_id,
            workspace=assignment.workspace,
            root_identity=assignment.root_identity,
            workspace_identity=assignment.workspace_identity,
            git_head=assignment.git_head,
            git_branch=assignment.git_branch,
            owner_token=assignment.owner_token,
            verified_status=target.verified_status,
        )
        if target != expected:
            raise WorkspaceOwnershipError("cleanup target fields do not match the assignment")
        if not status.clean:
            raise DirtyWorkspaceError(
                f"cleanup target became dirty after preparation ({status.summary()})"
            )
        return CleanupTarget(
            task_id=assignment.task_id,
            workspace=assignment.workspace,
            root_identity=assignment.root_identity,
            workspace_identity=assignment.workspace_identity,
            git_head=assignment.git_head,
            git_branch=assignment.git_branch,
            owner_token=assignment.owner_token,
            verified_status=status,
        )
