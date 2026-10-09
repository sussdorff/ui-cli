"""Tests for the tracked pre-push preflight script (scripts/dev/preflight.sh)."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = REPO_ROOT / "scripts" / "dev" / "preflight.sh"
CHECKER = (
    REPO_ROOT / ".agents" / "standards" / "toolchains" / "scripts" / "check_toolchain_versions.py"
)


def _make_repo(tmp_path: Path, requires_python: str) -> Path:
    """Create a throwaway git repository with the preflight script and checker installed."""
    repo = tmp_path / "repo"
    (repo / "scripts" / "dev").mkdir(parents=True)
    (repo / ".agents" / "standards" / "toolchains" / "scripts").mkdir(parents=True)
    shutil.copy2(PREFLIGHT, repo / "scripts" / "dev" / "preflight.sh")
    shutil.copy2(
        CHECKER,
        repo / ".agents" / "standards" / "toolchains" / "scripts" / "check_toolchain_versions.py",
    )
    (repo / "pyproject.toml").write_text(
        f'[project]\nname = "fixture"\nversion = "0.0.0"\nrequires-python = "{requires_python}"\n'
    )
    (repo / "sub").mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def _run_preflight(
    repo: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    # Run from a subdirectory to prove the script changes to the repository root.
    return subprocess.run(
        ["bash", str(repo / "scripts" / "dev" / "preflight.sh")],
        cwd=repo / "sub",
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
def test_preflight_ignores_inherited_git_environment(tmp_path: Path) -> None:
    # A pre-push hook inherits GIT_DIR (absolute in a linked worktree) and, via
    # `git hook run`, GIT_WORK_TREE=. ; the script must still find the repository root.
    repo = _make_repo(tmp_path, ">=3.14")
    env = {**os.environ, "GIT_DIR": str(repo / ".git"), "GIT_WORK_TREE": "."}

    result = _run_preflight(repo, env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status"' in result.stdout


@pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
def test_preflight_fails_on_outdated_toolchain(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, ">=3.10")

    result = _run_preflight(repo)

    assert result.returncode == 1
    assert "below_minimum" in result.stdout


@pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
def test_preflight_passes_on_current_toolchain(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, ">=3.14")

    result = _run_preflight(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status"' in result.stdout


def test_preflight_script_is_executable() -> None:
    assert PREFLIGHT.stat().st_mode & 0o111
