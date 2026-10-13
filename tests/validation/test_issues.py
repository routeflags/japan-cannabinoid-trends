"""Issue records must be machine-readable, and an OPEN P0 must not pass quietly.

Contract sources: ``docs/reports/README.md`` (what belongs in ``docs/issues/``),
AGENTS.md (validation before publication, explicit uncertainty).  The rule and the
rejected alternative are documented in ``validation/issues.py``.
"""

from pathlib import Path

import pytest

from validation.issues import STATUSES, TERMINAL_STATUSES, audit_issues

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def report() -> dict:
    return audit_issues(REPO_ROOT)


def _write(directory: Path, name: str, body: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(body, encoding="utf-8")


def _issue(**fields) -> str:
    body = "# Issue: probe\n\n"
    for key in ("ID", "優先度", "ステータス"):
        if key in fields:
            body += f"**{key}:** {fields[key]}\n"
    return body


# ---------------------------------------------------------------------------
# the real repository
# ---------------------------------------------------------------------------


def test_repository_issue_records_are_well_formed(report: dict) -> None:
    assert report["issue_count"] > 0
    assert report["malformed"] == []
    assert report["duplicate_ids"] == {}
    assert report["failures"] == []


def test_no_critical_issue_is_silently_open(report: dict) -> None:
    """The gate with teeth: a P0 is resolved or its deferral is recorded."""

    assert report["open_critical"] == []


def test_open_issues_are_reported_so_they_stay_visible(report: dict) -> None:
    """P1+ may remain open, but the count is reported rather than hidden."""

    assert report["open_count"] >= len(report["open_high"])
    for path in report["open_high"]:
        assert path.startswith("docs/issues/")


def test_statuses_used_in_the_repository_are_known(report: dict) -> None:
    for issue in report["issues"]:
        assert issue["status"] in STATUSES, issue["path"]


# ---------------------------------------------------------------------------
# the rule
# ---------------------------------------------------------------------------


def test_missing_fields_are_reported(tmp_path: Path) -> None:
    _write(tmp_path / "docs/issues", "a.md", "# Issue: probe\n")
    report = audit_issues(tmp_path)
    assert len(report["malformed"]) == 1
    assert report["failure_count"] == 1


def test_open_critical_fails_the_check(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/issues",
        "a.md",
        _issue(ID="ISS-1", 優先度="P0 (Critical)", ステータス="OPEN"),
    )
    report = audit_issues(tmp_path)
    assert report["open_critical"] == ["docs/issues/a.md"]
    assert "docs/issues/a.md" in report["failures"]


def test_deferring_a_critical_issue_is_the_way_out(tmp_path: Path) -> None:
    """The rule is "do not ignore", not "never defer"."""

    _write(
        tmp_path / "docs/issues",
        "a.md",
        _issue(ID="ISS-1", 優先度="P0 (Critical)", ステータス="PENDING (管理画面で対応)"),
    )
    report = audit_issues(tmp_path)
    assert report["open_critical"] == []
    assert report["failure_count"] == 0


def test_open_high_is_reported_but_not_fatal(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/issues",
        "a.md",
        _issue(ID="ISS-1", 優先度="P1 (High)", ステータス="OPEN"),
    )
    report = audit_issues(tmp_path)
    assert report["open_high"] == ["docs/issues/a.md"]
    assert report["failure_count"] == 0


@pytest.mark.parametrize("status", sorted(TERMINAL_STATUSES))
def test_terminal_status_without_a_date_is_rejected(tmp_path: Path, status: str) -> None:
    """A status flip with no evidence is what this repository keeps having to undo."""

    _write(
        tmp_path / "docs/issues",
        "a.md",
        _issue(ID="ISS-1", 優先度="P2 (Medium)", ステータス=status),
    )
    report = audit_issues(tmp_path)
    assert len(report["malformed"]) == 1
    assert "date" in report["issues"][0]["problems"][0]


def test_terminal_status_with_a_date_passes(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/issues",
        "a.md",
        _issue(ID="ISS-1", 優先度="P2 (Medium)", ステータス="RESOLVED (2026-10-13)"),
    )
    report = audit_issues(tmp_path)
    assert report["failure_count"] == 0
    assert report["issues"][0]["status_note"] == "2026-10-13"


def test_wrong_level_for_a_priority_is_rejected(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/issues",
        "a.md",
        _issue(ID="ISS-1", 優先度="P0 (Low)", ステータス="OPEN"),
    )
    report = audit_issues(tmp_path)
    assert any("Critical" in problem for problem in report["issues"][0]["problems"])


def test_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    for name in ("a.md", "b.md"):
        _write(
            tmp_path / "docs/issues",
            name,
            _issue(ID="ISS-1", 優先度="P2 (Medium)", ステータス="OPEN"),
        )
    report = audit_issues(tmp_path)
    assert report["duplicate_ids"] == {"ISS-1": ["docs/issues/a.md", "docs/issues/b.md"]}
    assert report["failure_count"] == 2


def test_absent_directory_is_empty_not_an_error(tmp_path: Path) -> None:
    report = audit_issues(tmp_path)
    assert report["issue_count"] == 0
    assert report["failure_count"] == 0
