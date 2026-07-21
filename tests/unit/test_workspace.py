"""Deterministic Windows-native tests for C-405 workspace containment."""

from __future__ import annotations

import os
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from harness.workspace import (
    CleanupTarget,
    DirtyWorkspaceError,
    GitStatus,
    GitWorktree,
    UnsafeWorkspacePathError,
    WorkspaceIdentityError,
    WorkspaceManager,
    WorkspaceOwnershipError,
    WorktreeInventoryError,
)

HEAD = "a" * 40
OTHER_HEAD = "b" * 40


class FakeGit:
    def __init__(
        self,
        *,
        records: tuple[GitWorktree, ...],
        statuses: dict[str, GitStatus] | None = None,
    ) -> None:
        self.records = records
        self.statuses = statuses or {}
        self.list_calls: list[Path] = []
        self.status_calls: list[Path] = []

    @staticmethod
    def key(path: Path) -> str:
        return str(path).casefold()

    def list_worktrees(self, repository_root: Path) -> tuple[GitWorktree, ...]:
        self.list_calls.append(repository_root)
        return self.records

    def status(self, workspace: Path) -> GitStatus:
        self.status_calls.append(workspace)
        return self.statuses.get(self.key(workspace), GitStatus())


def _layout(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    repository = tmp_path / "repository"
    worktree_root = tmp_path / "worktrees"
    workspace = worktree_root / "C-405"
    unrelated = worktree_root / "C-408"
    for path in (repository, workspace, unrelated):
        path.mkdir(parents=True)
    return repository.resolve(), worktree_root.resolve(), workspace.resolve(), unrelated.resolve()


def _record(path: Path, *, head: str = HEAD, locked: bool = False) -> GitWorktree:
    return GitWorktree(
        path=path,
        head=head,
        branch=f"refs/heads/{path.name.casefold()}",
        locked=locked,
    )


def _manager(
    repository: Path,
    worktree_root: Path,
    git: FakeGit,
) -> WorkspaceManager:
    return WorkspaceManager(repository_root=repository, worktree_root=worktree_root, git=git)


def _create_junction(link: Path, target: Path) -> None:
    environment = os.environ.copy()
    environment.update({"C405_LINK": str(link), "C405_TARGET": str(target)})
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$null = New-Item -ItemType Junction -Path $env:C405_LINK "
            "-Target $env:C405_TARGET -ErrorAction Stop",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    assert link.stat(follow_symlinks=False).st_file_attributes & 0x400


def _remove_junction(link: Path) -> None:
    assert link.stat(follow_symlinks=False).st_file_attributes & 0x400
    link.rmdir()


def test_one_task_maps_to_one_exact_worktree_and_unrelated_worktree_is_untouched(
    tmp_path: Path,
) -> None:
    repository, root, workspace, unrelated = _layout(tmp_path)
    workspace_sentinel = workspace / "task.txt"
    unrelated_sentinel = unrelated / "keep.txt"
    workspace_sentinel.write_text("task data\n", encoding="utf-8")
    unrelated_sentinel.write_text("unrelated data\n", encoding="utf-8")
    records = (_record(repository), _record(workspace), _record(unrelated))
    git = FakeGit(records=records)
    manager = _manager(repository, root, git)

    assignment = manager.assign(task_id="C-405", workspace=workspace)

    assert assignment.task_id == "C-405"
    assert assignment.workspace == workspace
    assert assignment.git_head == HEAD
    assert assignment.observed_status.clean
    assert manager.assign(task_id="C-405", workspace=workspace) == assignment
    with pytest.raises(WorkspaceOwnershipError, match="another workspace"):
        manager.assign(task_id="C-405", workspace=unrelated)
    with pytest.raises(WorkspaceOwnershipError, match="another task"):
        manager.assign(task_id="C-408", workspace=workspace)

    target = manager.prepare_cleanup(task_id="C-405", workspace=workspace)
    assert manager.verify_cleanup_target(target) == target
    assert workspace_sentinel.read_text(encoding="utf-8") == "task data\n"
    assert unrelated_sentinel.read_text(encoding="utf-8") == "unrelated data\n"
    assert git.records == records


@pytest.mark.parametrize(
    "candidate_factory, expected",
    [
        (lambda root, workspace: Path("relative-workspace"), "absolute drive-local"),
        (lambda root, workspace: root / "C-405" / ".." / "C-408", "traversal"),
        (lambda root, workspace: Path(f"{workspace}:secret"), "alternate data stream"),
        (lambda root, workspace: root / "*", "glob syntax"),
        (lambda root, workspace: root / "%C405_WORKSPACE%", "environment expansion"),
        (lambda root, workspace: root / "CON", "reserved Windows device"),
        (lambda root, workspace: root / "trailing.", "trailing-dot/space"),
        (lambda root, workspace: root / "trailing ", "trailing-dot/space"),
        (lambda root, workspace: Path(r"\\server\share\C-405"), "drive-local"),
        (lambda root, workspace: Path(r"\\?\C:\worktrees\C-405"), "device namespace"),
    ],
)
def test_unsafe_windows_path_classes_fail_closed_before_git_inspection(
    tmp_path: Path,
    candidate_factory: object,
    expected: str,
) -> None:
    repository, root, workspace, _ = _layout(tmp_path)
    git = FakeGit(records=(_record(workspace),))
    manager = _manager(repository, root, git)
    assert callable(candidate_factory)
    candidate = candidate_factory(root, workspace)

    with pytest.raises(UnsafeWorkspacePathError, match=expected):
        manager.assign(task_id="C-405", workspace=candidate)

    assert git.list_calls == []
    assert git.status_calls == []


def test_sibling_prefix_nested_and_root_targets_are_not_cleanup_candidates(tmp_path: Path) -> None:
    repository, root, workspace, _ = _layout(tmp_path)
    sibling_prefix = root.parent / f"{root.name}-unrelated"
    nested = workspace / "nested"
    sibling_prefix.mkdir()
    nested.mkdir()
    git = FakeGit(records=(_record(root), _record(sibling_prefix), _record(nested)))
    manager = _manager(repository, root, git)

    for candidate in (root, sibling_prefix, nested):
        with pytest.raises(UnsafeWorkspacePathError, match="exact direct child"):
            manager.assign(task_id="C-405", workspace=candidate)


def test_case_insensitive_git_identity_matches_the_exact_existing_workspace(tmp_path: Path) -> None:
    repository, root, workspace, unrelated = _layout(tmp_path)
    git = FakeGit(records=(_record(Path(str(workspace).upper())), _record(unrelated)))
    manager = _manager(repository, root, git)

    assignment = manager.assign(task_id="C-405", workspace=workspace)

    assert assignment.workspace == workspace


def test_junction_workspace_and_junction_root_are_rejected(tmp_path: Path) -> None:
    repository = (tmp_path / "repository").resolve()
    root = (tmp_path / "worktrees").resolve()
    external = (tmp_path / "external").resolve()
    repository.mkdir()
    root.mkdir()
    external.mkdir()
    junction = root / "C-405"
    _create_junction(junction, external)
    try:
        git = FakeGit(records=(_record(junction),))
        manager = _manager(repository, root, git)
        with pytest.raises(UnsafeWorkspacePathError, match="reparse point"):
            manager.assign(task_id="C-405", workspace=junction)
        assert git.list_calls == []
    finally:
        _remove_junction(junction)

    root.rmdir()
    root_target = (tmp_path / "worktree-target").resolve()
    root_target.mkdir()
    _create_junction(root, root_target)
    try:
        with pytest.raises(UnsafeWorkspacePathError, match="reparse point"):
            _manager(repository, root, FakeGit(records=()))
    finally:
        _remove_junction(root)


def test_symlink_classification_fails_closed_before_git_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, root, workspace, _ = _layout(tmp_path)
    original_is_symlink = Path.is_symlink

    def classified_as_symlink(path: Path) -> bool:
        return path == workspace or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", classified_as_symlink)
    git = FakeGit(records=(_record(workspace),))
    manager = _manager(repository, root, git)

    with pytest.raises(UnsafeWorkspacePathError, match="reparse point"):
        manager.assign(task_id="C-405", workspace=workspace)
    assert git.list_calls == []


def test_root_filesystem_identity_swap_fails_before_workspace_or_git_use(tmp_path: Path) -> None:
    repository, root, workspace, _ = _layout(tmp_path)
    git = FakeGit(records=(_record(workspace),))
    manager = _manager(repository, root, git)
    backup = root.with_name("worktrees-original")
    root.rename(backup)
    root.mkdir()
    try:
        with pytest.raises(WorkspaceIdentityError, match="worktree_root filesystem identity"):
            manager.assign(task_id="C-405", workspace=workspace)
        assert git.list_calls == []
    finally:
        root.rmdir()
        backup.rename(root)


def test_repository_filesystem_identity_swap_fails_before_workspace_or_git_use(
    tmp_path: Path,
) -> None:
    repository, root, workspace, _ = _layout(tmp_path)
    git = FakeGit(records=(_record(workspace),))
    manager = _manager(repository, root, git)
    backup = repository.with_name("repository-original")
    repository.rename(backup)
    repository.mkdir()
    try:
        with pytest.raises(WorkspaceIdentityError, match="repository_root filesystem identity"):
            manager.assign(task_id="C-405", workspace=workspace)
        assert git.list_calls == []
    finally:
        repository.rmdir()
        backup.rename(repository)


def test_assigned_workspace_identity_swap_is_rejected_before_cleanup(tmp_path: Path) -> None:
    repository, root, workspace, _ = _layout(tmp_path)
    git = FakeGit(records=(_record(workspace),))
    manager = _manager(repository, root, git)
    manager.assign(task_id="C-405", workspace=workspace)
    backup = workspace.with_name("C-405-original")
    workspace.rename(backup)
    workspace.mkdir()
    try:
        with pytest.raises(WorkspaceIdentityError, match="workspace filesystem identity changed"):
            manager.prepare_cleanup(task_id="C-405", workspace=workspace)
    finally:
        workspace.rmdir()
        backup.rename(workspace)


@pytest.mark.parametrize(
    "dirty_status",
    [
        GitStatus(staged=("staged.py",)),
        GitStatus(unstaged=("modified.py",)),
        GitStatus(untracked=("valuable-untracked.txt",)),
        GitStatus(staged=("a",), unstaged=("b",), untracked=("c",)),
    ],
)
def test_dirty_workspace_is_reported_and_cleanup_is_refused_without_data_loss(
    tmp_path: Path, dirty_status: GitStatus
) -> None:
    repository, root, workspace, unrelated = _layout(tmp_path)
    workspace_sentinel = workspace / "valuable-untracked.txt"
    unrelated_sentinel = unrelated / "keep.txt"
    workspace_sentinel.write_text("preserve me\n", encoding="utf-8")
    unrelated_sentinel.write_text("preserve unrelated\n", encoding="utf-8")
    git = FakeGit(
        records=(_record(workspace), _record(unrelated)),
        statuses={FakeGit.key(workspace): dirty_status},
    )
    manager = _manager(repository, root, git)

    assignment = manager.assign(task_id="C-405", workspace=workspace)
    assert assignment.observed_status == dirty_status
    with pytest.raises(DirtyWorkspaceError, match=dirty_status.summary()):
        manager.prepare_cleanup(task_id="C-405", workspace=workspace)

    assert workspace_sentinel.read_text(encoding="utf-8") == "preserve me\n"
    assert unrelated_sentinel.read_text(encoding="utf-8") == "preserve unrelated\n"


@pytest.mark.parametrize(
    "records, expected",
    [
        ((), "not a registered"),
        ((_record(Path(r"C:\duplicate")), _record(Path(r"C:\duplicate"))), "ambiguous"),
    ],
)
def test_missing_or_duplicate_inventory_fails_closed(
    tmp_path: Path, records: tuple[GitWorktree, ...], expected: str
) -> None:
    repository, root, workspace, _ = _layout(tmp_path)
    actual_records = records
    if records:
        actual_records = (_record(workspace), _record(Path(str(workspace).upper())))
    manager = _manager(repository, root, FakeGit(records=actual_records))

    with pytest.raises(WorktreeInventoryError, match=expected):
        manager.assign(task_id="C-405", workspace=workspace)


def test_locked_worktree_is_not_assigned(tmp_path: Path) -> None:
    repository, root, workspace, _ = _layout(tmp_path)
    manager = _manager(repository, root, FakeGit(records=(_record(workspace, locked=True),)))

    with pytest.raises(WorktreeInventoryError, match="locked"):
        manager.assign(task_id="C-405", workspace=workspace)


def test_cleanup_target_is_explicit_and_revalidated_for_status_and_git_identity(
    tmp_path: Path,
) -> None:
    repository, root, workspace, unrelated = _layout(tmp_path)
    git = FakeGit(records=(_record(workspace), _record(unrelated)))
    manager = _manager(repository, root, git)
    assignment = manager.assign(task_id="C-405", workspace=workspace)
    target = manager.prepare_cleanup(task_id="C-405", workspace=workspace)

    assert target.workspace == workspace
    assert target.owner_token == assignment.owner_token
    with pytest.raises(WorkspaceOwnershipError, match="owner token"):
        manager.verify_cleanup_target(replace(target, owner_token="0" * 64))

    git.statuses[FakeGit.key(workspace)] = GitStatus(untracked=("late.txt",))
    with pytest.raises(DirtyWorkspaceError, match="became dirty"):
        manager.verify_cleanup_target(target)

    git.statuses.clear()
    git.records = (_record(workspace, head=OTHER_HEAD), _record(unrelated))
    with pytest.raises(WorktreeInventoryError, match="HEAD changed"):
        manager.verify_cleanup_target(target)


def test_cleanup_target_cannot_be_forged_for_an_unrelated_worktree(tmp_path: Path) -> None:
    repository, root, workspace, unrelated = _layout(tmp_path)
    git = FakeGit(records=(_record(workspace), _record(unrelated)))
    manager = _manager(repository, root, git)
    manager.assign(task_id="C-405", workspace=workspace)
    target = manager.prepare_cleanup(task_id="C-405", workspace=workspace)
    forged = CleanupTarget(
        task_id=target.task_id,
        workspace=unrelated,
        root_identity=target.root_identity,
        workspace_identity=target.workspace_identity,
        git_head=target.git_head,
        git_branch=target.git_branch,
        owner_token=target.owner_token,
        verified_status=target.verified_status,
    )

    with pytest.raises(WorkspaceOwnershipError, match="does not match task assignment"):
        manager.verify_cleanup_target(forged)


def test_invalid_task_identity_cannot_become_a_workspace_owner(tmp_path: Path) -> None:
    repository, root, workspace, _ = _layout(tmp_path)
    git = FakeGit(records=(_record(workspace),))
    manager = _manager(repository, root, git)

    for task_id in ("", ".", "..", "C/405", "C\\405", " C-405"):
        with pytest.raises(WorkspaceOwnershipError, match="path-free"):
            manager.assign(task_id=task_id, workspace=workspace)

    assert git.list_calls == []
