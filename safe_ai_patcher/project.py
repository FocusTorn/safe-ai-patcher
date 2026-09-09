"""Project and Git detection for Safe AI Patcher."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


PROJECT_MARKERS = (
    "pyproject.toml",
    "package.json",
    "build.gradle",
    "build.gradle.kts",
    "Cargo.toml",
    "go.mod",
    "Makefile",
)


@dataclass(frozen=True)
class ProjectInfo:
    root: Path
    marker: str | None


@dataclass(frozen=True)
class GitInfo:
    root: Path | None
    branch: str | None
    dirty: bool
    available: bool


def detect_project(start: str | Path = ".") -> ProjectInfo:
    """Find the nearest project root from start."""
    current = Path(start).resolve()

    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        for marker in PROJECT_MARKERS:
            if (directory / marker).is_file():
                return ProjectInfo(directory, marker)

        if (directory / ".git").exists():
            return ProjectInfo(directory, None)

    return ProjectInfo(current, None)


def git_changed_paths(root: str | Path) -> set[str]:
    """Return paths currently changed in the Git worktree."""
    root = Path(root).resolve()

    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return set()

    paths = set()

    for line in result.stdout.splitlines():
        if not line:
            continue

        value = line[3:]

        if " -> " in value:
            value = value.split(" -> ", 1)[1]

        paths.add(value)

    return paths


def detect_git(start: str | Path = ".") -> GitInfo:
    """Inspect Git state without modifying the repository."""
    project = detect_project(start)

    try:
        root_result = subprocess.run(
            ["git", "-C", str(project.root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )

        if root_result.returncode != 0:
            return GitInfo(None, None, False, False)

        git_root = Path(root_result.stdout.strip()).resolve()

        branch_result = subprocess.run(
            ["git", "-C", str(git_root), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=False,
        )

        status_result = subprocess.run(
            ["git", "-C", str(git_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )

        branch = branch_result.stdout.strip() or None

        return GitInfo(
            root=git_root,
            branch=branch,
            dirty=bool(status_result.stdout.strip()),
            available=True,
        )

    except OSError:
        return GitInfo(None, None, False, False)
