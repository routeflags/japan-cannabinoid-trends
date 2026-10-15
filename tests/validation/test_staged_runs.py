"""Lightweight staged-run guard (``ISS-20261015-COL-020``).

Contract sources: ``docs/specs/validation-framework.md`` section 22.4,
``src/validation/legacy.py`` (the frozen allow-list), ``src/validation/new_runs.py``
(the CI gate this guard must not replace).

The decisive pairs are :func:`test_missing_key_fails_before_commit` (an
obvious omission is caught locally) and
:func:`test_frozen_legacy_run_is_exempt` (the exemption reuses the CI gate's
own allow-list instead of reclassifying legacy runs).

All git exercises use throwaway repositories under ``tmp_path``; nothing
here touches the real ``datasets/`` tree.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from validation.legacy import LEGACY_RUN_IDS
from validation.staged_runs import (
    REQUIRED_PROVENANCE_PATHS,
    audit_staged_runs,
    check_document,
    is_run_metadata_path,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _valid_document(run_id: str = "20261015T000000Z-x-probe") -> dict:
    return {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "study_id": "probe-study",
        "source_id": "x",
        "purpose": "probe",
        "collector": {"collector_id": "probe-collector", "adapter_id": "probe@1"},
        "collection_started_at": "2026-10-15T00:00:00Z",
        "query_provenance": {"query_id": "probe-query", "submitted_query": "probe"},
        "temporal_provenance": {
            "window_id": "w",
            "requested_start": "2026-10-14T00:00:00Z",
            "requested_end_exclusive": "2026-10-15T00:00:00Z",
            "granularity": "day",
            "timezone": "Asia/Tokyo",
        },
        "execution": {"status": "success", "returned_count": 3, "errors": []},
    }


def _init_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "probe@example.test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "probe"],
        check=True,
    )
    return path


def _stage_run_metadata(repo: Path, payload: bytes, run_id: str = "probe-run") -> str:
    relative = f"datasets/probe-study/data/raw/x/{run_id}/run_metadata.json"
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    subprocess.run(["git", "-C", str(repo), "add", relative], check=True)
    return relative


def _stage_worktree_tampered_copy(repo: Path, relative: str, payload: bytes) -> None:
    """Rewrite the worktree copy after staging: the guard must read the index."""

    (repo / relative).write_bytes(payload)


# ---------------------------------------------------------------------------
# path selection
# ---------------------------------------------------------------------------


def test_run_metadata_paths_are_selected() -> None:
    assert is_run_metadata_path(
        "datasets/probe-study/data/raw/x/20261015T000000Z-x-probe/run_metadata.json"
    )
    # Conservative: deeper nesting below raw/ is still inspected, not skipped.
    assert is_run_metadata_path(
        "datasets/probe-study/data/raw/x/extra/20261015T000000Z-x-probe/run_metadata.json"
    )


def test_non_metadata_paths_are_ignored() -> None:
    assert not is_run_metadata_path("datasets/probe-study/data/processed/trends.csv")
    assert not is_run_metadata_path(
        "datasets/probe-study/data/raw/x/20261015T000000Z-x-probe/payload.json"
    )
    assert not is_run_metadata_path(
        "datasets/probe-study/data/raw/run_metadata.json"
    )
    assert not is_run_metadata_path("metadata/datapackage.json")


# ---------------------------------------------------------------------------
# staged valid metadata passes
# ---------------------------------------------------------------------------


def test_staged_valid_metadata_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    _stage_run_metadata(
        repo, json.dumps(_valid_document()).encode("utf-8"), run_id="20261015T000000Z-x-probe"
    )
    assert main(["--repo-root", str(repo)]) == 0


def test_guard_reads_the_index_not_the_worktree(tmp_path: Path) -> None:
    """A worktree edit after ``git add`` must not change the verdict."""

    repo = _init_repo(tmp_path / "repo")
    relative = _stage_run_metadata(
        repo,
        json.dumps(_valid_document()).encode("utf-8"),
        run_id="20261015T000000Z-x-probe",
    )
    _stage_worktree_tampered_copy(repo, relative, b"{ not json")
    assert main(["--repo-root", str(repo)]) == 0


def test_nothing_staged_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    (repo / "README.md").write_text("probe\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
    report = audit_staged_runs(str(repo))
    assert report["candidate_count"] == 0
    assert report["failure_count"] == 0
    assert main(["--repo-root", str(repo)]) == 0


# ---------------------------------------------------------------------------
# missing keys fail with dotted paths
# ---------------------------------------------------------------------------


def test_missing_key_fails_before_commit(tmp_path: Path, capsys) -> None:
    repo = _init_repo(tmp_path / "repo")
    document = _valid_document()
    del document["query_provenance"]["query_id"]
    del document["execution"]["status"]
    relative = _stage_run_metadata(
        repo, json.dumps(document).encode("utf-8"), run_id="20261015T000000Z-x-probe"
    )
    assert main(["--repo-root", str(repo)]) == 1
    out = capsys.readouterr().out
    assert f"{relative}: missing execution.status, query_provenance.query_id" in out


def test_missing_run_id_is_never_exempt(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    document = _valid_document()
    del document["run_id"]
    _stage_run_metadata(repo, json.dumps(document).encode("utf-8"), run_id="anonymous")
    report = audit_staged_runs(str(repo))
    assert report["failure_count"] == 1
    assert report["failures"][0]["frozen_legacy"] is False
    assert "run_id" in report["failures"][0]["missing"]


def test_guard_is_read_only(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    payload = json.dumps(_valid_document()).encode("utf-8")
    relative = _stage_run_metadata(repo, payload, run_id="20261015T000000Z-x-probe")
    audit_staged_runs(str(repo))
    assert (repo / relative).read_bytes() == payload


# ---------------------------------------------------------------------------
# malformed JSON fails deterministically
# ---------------------------------------------------------------------------


def test_malformed_json_fails_without_printing_content(tmp_path: Path, capsys) -> None:
    repo = _init_repo(tmp_path / "repo")
    relative = _stage_run_metadata(repo, b"{ not json, SECRET_PAYLOAD", run_id="broken")
    assert main(["--repo-root", str(repo)]) == 1
    out = capsys.readouterr().out
    assert f"{relative}: malformed JSON" in out
    assert "SECRET_PAYLOAD" not in out


def test_malformed_json_is_deterministic(tmp_path: Path, capsys) -> None:
    repo = _init_repo(tmp_path / "repo")
    _stage_run_metadata(repo, b"[1, 2,", run_id="broken")
    first = audit_staged_runs(str(repo))
    capsys.readouterr()
    assert main(["--repo-root", str(repo)]) == 1
    second_out = capsys.readouterr().out
    assert main(["--repo-root", str(repo)]) == 1
    third_out = capsys.readouterr().out
    assert second_out == third_out
    assert first["failures"][0]["unreadable"] is True


# ---------------------------------------------------------------------------
# frozen legacy exemption reuses the CI allow-list
# ---------------------------------------------------------------------------


def test_frozen_legacy_run_is_exempt(tmp_path: Path) -> None:
    frozen = sorted(LEGACY_RUN_IDS)[0]
    repo = _init_repo(tmp_path / "repo")
    _stage_run_metadata(
        repo, json.dumps({"run_id": frozen}).encode("utf-8"), run_id="legacy-dir"
    )
    report = audit_staged_runs(str(repo))
    assert report["failure_count"] == 0
    assert report["frozen_legacy_seen"] == 1
    assert main(["--repo-root", str(repo)]) == 0


def test_exemption_uses_the_ci_allow_list_source_of_truth() -> None:
    """The exemption must not drift from the gate it shadows."""

    import validation.legacy as legacy
    import validation.staged_runs as staged_runs

    assert staged_runs.LEGACY_RUN_IDS is legacy.LEGACY_RUN_IDS


def test_minimal_key_set_is_a_subset_of_the_ci_contract() -> None:
    """The guard must stay reduced: every checked path is a required CI field."""

    from validation.legacy import missing_required_paths
    from validation.schemas.collection_run import COLLECTION_RUN_SCHEMA

    probe = {
        "run_id": "probe",
        "collector": {},
        "query_provenance": {},
        "execution": {},
    }
    ci_required = set(missing_required_paths(probe, COLLECTION_RUN_SCHEMA))
    assert set(REQUIRED_PROVENANCE_PATHS) <= ci_required
    run_id, frozen, missing = check_document({"run_id": "probe"})
    assert (run_id, frozen) == ("probe", False)
    assert missing == sorted(REQUIRED_PROVENANCE_PATHS)


# ---------------------------------------------------------------------------
# dependency-light behavior (AC5)
# ---------------------------------------------------------------------------


def test_guard_runs_without_third_party_imports(tmp_path: Path) -> None:
    """Fresh interpreter, Cerberus blocked: the guard must still pass valid metadata."""

    repo = _init_repo(tmp_path / "repo")
    _stage_run_metadata(
        repo, json.dumps(_valid_document()).encode("utf-8"), run_id="20261015T000000Z-x-probe"
    )
    script_lines = [
        "import sys",
        "_BLOCKED = {'validation.pipeline', 'validation.core', 'validation.cli',",
        "              'validation.semantic'}",
        "class _Blocker:",
        "    def find_module(self, name, path=None):",
        "        if name.split('.')[0] == 'cerberus' or name in _BLOCKED:",
        "            return self",
        "        return None",
        "    def load_module(self, name):",
        "        raise ImportError('blocked for dependency-light check: ' + name)",
        "sys.meta_path.insert(0, _Blocker())",
        "import validation.staged_runs as g",
        "_hit = {'cerberus'} | _BLOCKED",
        "_hit &= set(sys.modules)",
        "assert not _hit, _hit",
        f"sys.exit(g.main(['--repo-root', r'''{repo}''']))",
    ]
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-c", "\n".join(script_lines)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_hook_wiring_mentions_guard_and_trigger() -> None:
    """The pre-commit hook must trigger the guard on raw run paths."""

    hook = (REPO_ROOT / "scripts/git-hooks/pre-commit").read_text(encoding="utf-8")
    assert "validation.staged_runs" in hook
    assert "datasets/*/data/raw/*" in hook
    assert "audit-new-runs" in hook


def _hook_copy(tmp_path: Path, repo: Path) -> Path:
    """Install the real hook for a bare repo (``src`` symlinked for PYTHONPATH)."""

    (repo / "src").symlink_to(REPO_ROOT / "src", target_is_directory=True)
    hook = tmp_path / "pre-commit"
    shutil.copy(REPO_ROOT / "scripts/git-hooks/pre-commit", hook)
    return hook


def test_hook_leaves_unrelated_commits_alone(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    hook = _hook_copy(tmp_path, repo)
    (repo / "note.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "note.txt"], check=True)
    result = subprocess.run(
        ["bash", str(hook)], cwd=str(repo), capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert "Staged Run Metadata" not in result.stdout


def test_hook_checks_staged_run_metadata(tmp_path: Path) -> None:
    """Section 7 runs on staged raw metadata in a bare repo.

    Other sections fail there (no validation scripts/denylist), so this
    asserts the section-7 lines rather than the overall exit code.
    """

    repo = _init_repo(tmp_path / "repo")
    hook = _hook_copy(tmp_path, repo)
    _stage_run_metadata(
        repo, json.dumps(_valid_document()).encode("utf-8"), run_id="20261015T000000Z-x-probe"
    )
    result = subprocess.run(
        ["bash", str(hook)], cwd=str(repo), capture_output=True, text=True, check=False
    )
    assert "7. Staged Run Metadata" in result.stdout
    assert "✅ staged run メタデータの軽量検査に合格しました" in result.stdout

    document = _valid_document()
    del document["execution"]["status"]
    _stage_run_metadata(
        repo, json.dumps(document).encode("utf-8"), run_id="20261015T000000Z-x-probe"
    )
    result = subprocess.run(
        ["bash", str(hook)], cwd=str(repo), capture_output=True, text=True, check=False
    )
    assert result.returncode == 1
    assert "❌ staged run メタデータの軽量検査に失敗しました" in result.stdout
    assert "missing execution.status" in result.stdout
