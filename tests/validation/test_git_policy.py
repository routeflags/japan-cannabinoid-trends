"""Git tracking policy tests (P4-7).

A temporary git repository is created for behaviour tests; one read-only
smoke test runs against the real repository to demonstrate that no false
positives/negatives occur on its actual state.
"""

import subprocess
from pathlib import Path

import pytest

from validation.storage_policy import (
    check_git_tracking,
    git_ignored,
    git_tracked,
    select_policy,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "tests@example.invalid")
    _git(root, "config", "user.name", "Contract Tests")
    (root / ".gitignore").write_text("ignored-dir/\n", encoding="utf-8")
    (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    ignored = root / "ignored-dir"
    ignored.mkdir()
    (ignored / "secret.raw").write_text("raw\n", encoding="utf-8")
    untracked = root / "loose.txt"
    untracked.write_text("loose\n", encoding="utf-8")
    _git(root, "add", ".gitignore", "tracked.txt")
    _git(root, "commit", "-q", "-m", "init")
    return root


def test_git_tracked_and_ignored_helpers(_repo):
    assert git_tracked(_repo, "tracked.txt") is True
    assert git_tracked(_repo, "ignored-dir/secret.raw") is False
    assert git_ignored(_repo, "ignored-dir/secret.raw") is True
    assert git_ignored(_repo, "loose.txt") is False


def test_gitignore_alone_is_not_trusted(_repo):
    """f.md §8: an already-tracked file keeps being tracked even if a later
    .gitignore rule matches it."""
    tracked = _repo / "now-ignored.txt"
    tracked.write_text("x\n", encoding="utf-8")
    _git(_repo, "add", "now-ignored.txt")
    _git(_repo, "commit", "-q", "-m", "add")
    (_repo / ".gitignore").write_text("ignored-dir/\nnow-ignored.txt\n", encoding="utf-8")
    _git(_repo, "add", ".gitignore")
    _git(_repo, "commit", "-q", "-m", "ignore it")

    assert git_ignored(_repo, "now-ignored.txt") is True
    assert git_tracked(_repo, "now-ignored.txt") is True


def test_policy_ignored_but_tracked_fails(_repo):
    issues = check_git_tracking(
        _repo, [{"path": "ignored-dir/secret.raw", "expected": "ignored"}]
    )
    assert [issue.code for issue in issues] == []

    # now track it on purpose -> policy violation
    _git(_repo, "add", "-f", "ignored-dir/secret.raw")
    _git(_repo, "commit", "-q", "-m", "track raw")
    issues = check_git_tracking(
        _repo, [{"path": "ignored-dir/secret.raw", "expected": "ignored"}]
    )
    assert [issue.code for issue in issues] == ["GIT_POLICY_TRACKED_WHEN_IGNORED"]


def test_policy_tracked_but_untracked_fails(_repo):
    issues = check_git_tracking(
        _repo, [{"path": "loose.txt", "expected": "tracked"}]
    )
    codes = [issue.code for issue in issues]
    assert "GIT_POLICY_UNTRACKED_WHEN_TRACKED" in codes


def test_untracked_and_unignored_warns_g6_t06(_repo):
    issues = check_git_tracking(
        _repo, [{"path": "loose.txt", "expected": "conditional"}]
    )
    by_code = {issue.code: issue for issue in issues}
    assert by_code["GIT_POLICY_UNIGNORED_UNTRACKED"].severity == "warning"


def test_conditional_tracked_requires_review(_repo):
    issues = check_git_tracking(
        _repo, [{"path": "tracked.txt", "expected": "conditional"}]
    )
    assert [issue.code for issue in issues] == ["GIT_POLICY_CONDITIONAL_REVIEW"]
    assert issues[0].severity == "warning"


def test_policy_id_lookup():
    """The expected git_tracking value can come from a policy registry."""
    policies = {
        "raw-social-default": "ignored",
        "public-methodology": "tracked",
    }
    # pyproject.toml is tracked in the repository: a policy that demands
    # "ignored" must fail, which proves the policy_id lookup is used.
    issues = check_git_tracking(
        REPO_ROOT,
        [{"path": "pyproject.toml", "policy_id": "raw-social-default"}],
        policies=policies,
    )
    assert [issue.code for issue in issues] == ["GIT_POLICY_TRACKED_WHEN_IGNORED"]

    issues = check_git_tracking(
        REPO_ROOT,
        [{"path": "pyproject.toml", "policy_id": "public-methodology"}],
        policies=policies,
    )
    assert [issue.code for issue in issues] == []


# ---------------------------------------------------------------------------
# select_policy
# ---------------------------------------------------------------------------


def test_select_policy_prefers_exact_match():
    import json

    registry = json.loads(
        (Path(__file__).parent / "fixtures" / "storage_policies.json").read_text(
            encoding="utf-8"
        )
    )
    exact = select_policy(registry, artifact_layer="raw", source_kind="social")
    wildcard = select_policy(registry, artifact_layer="processed", source_kind="search")
    assert exact["policy_id"] == "raw-social-default"
    assert wildcard["policy_id"] == "processed-public-candidate"
    assert select_policy(registry, artifact_layer="interim", source_kind="x") is None


# ---------------------------------------------------------------------------
# Read-only smoke test on the actual repository state
# ---------------------------------------------------------------------------


def test_repository_smoke_read_only():
    """P4-7 acceptance: run the helper against the real repository without
    changing anything.  google-trends raw data is intentionally tracked
    (.gitignore exception), while .venv is ignored and untracked."""
    assert git_tracked(REPO_ROOT, "pyproject.toml") is True
    assert git_tracked(REPO_ROOT, ".venv/bin/python") is False
    assert git_ignored(REPO_ROOT, ".venv/bin/python") is True
