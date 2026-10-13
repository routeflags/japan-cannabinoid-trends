"""Runs outside the frozen legacy list must satisfy the current contract.

Contract sources: ``docs/specs/validation-framework.md`` sections 12 and 13,
``docs/specs/collection-pipeline.md``, AGENTS.md (raw/derived pipeline, explicit
provenance).

The decisive pair is
:func:`test_unframeworked_run_fails_the_check` (a run that bypassed the framework
cannot pass) and :func:`test_repository_check_is_not_vacuous` (the rule still
matches the 29 frozen runs, so a green result means something).
"""

import json
from pathlib import Path

import pytest

from validation.cli import load_registries
from validation.legacy import LEGACY_RUN_IDS
from validation.new_runs import RUN_METADATA_NAME, audit_new_runs

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_RUN_FIXTURE = REPO_ROOT / "tests/validation/fixtures/collection_run_valid.json"


@pytest.fixture(scope="module")
def registries():
    return load_registries(REPO_ROOT / "config", REPO_ROOT / "metadata")


def _place(datasets_root: Path, run_id: str, document: dict) -> Path:
    """Write a run under ``datasets/<study>/data/raw/<run_id>/``."""

    target = datasets_root / "probe-study" / "data" / "raw" / run_id
    target.mkdir(parents=True, exist_ok=True)
    (target / RUN_METADATA_NAME).write_text(
        json.dumps(document, ensure_ascii=False), encoding="utf-8"
    )
    return target


# ---------------------------------------------------------------------------
# the real repository
# ---------------------------------------------------------------------------


def test_repository_check_is_not_vacuous() -> None:
    """Green must mean "nothing new to check", not "nothing was checked"."""

    report = audit_new_runs(REPO_ROOT, REPO_ROOT / "datasets")
    assert report["failure_count"] == 0
    assert report["new_run_count"] == 0
    assert report["frozen_legacy_seen"] == report["frozen_legacy_declared"] == len(
        LEGACY_RUN_IDS
    )
    assert report["run_count"] == report["frozen_legacy_seen"]


def test_every_frozen_run_on_disk_is_grandfathered() -> None:
    report = audit_new_runs(REPO_ROOT, REPO_ROOT / "datasets")
    for run in report["runs"]:
        assert run["frozen_legacy"] is True, run["path"]
        assert run["run_id"] in LEGACY_RUN_IDS


# ---------------------------------------------------------------------------
# the rule itself
# ---------------------------------------------------------------------------


def test_unframeworked_run_fails_the_check(tmp_path: Path, registries) -> None:
    """A run with no provenance cannot pass, so the bypass is a failing gate."""

    _place(
        tmp_path / "datasets",
        "20261013T000000Z-x-probe",
        {"schema_version": "1.0.0", "run_id": "20261013T000000Z-x-probe"},
    )
    report = audit_new_runs(tmp_path, "datasets", registries=registries)
    assert report["new_run_count"] == 1
    assert report["failure_count"] == 1
    assert "REQUIRED_FIELD_MISSING" in report["failures"][0]["issue_codes"]


def _first_entry(path: Path, key: str) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    return document[key][0]


def _conformant_document() -> dict:
    """A run that the current registries actually accept.

    The committed fixture uses ``x-apify-example`` as its collector, which is a
    placeholder and is deliberately not registered, so the reference check rejects
    it.  The collector is therefore taken from ``config/collectors.json`` rather
    than hardcoded, so this test keeps describing real registry content.
    """

    document = json.loads(VALID_RUN_FIXTURE.read_text(encoding="utf-8"))
    collector = _first_entry(REPO_ROOT / "config/collectors.json", "collectors")
    document["collector"]["collector_id"] = collector["collector_id"]
    document["collector"]["adapter_id"] = collector["adapter_id"]
    document["source_id"] = collector["source_id"]
    document["study_id"] = _first_entry(
        REPO_ROOT / "metadata/studies/study-registry.json", "studies"
    )["study_id"]
    return document


def test_conformant_new_run_passes(tmp_path: Path, registries) -> None:
    """The check must be passable by framework-produced data, or it is a wall."""

    document = _conformant_document()
    _place(tmp_path / "datasets", document["run_id"], document)
    report = audit_new_runs(tmp_path, "datasets", registries=registries)
    assert report["new_run_count"] == 1
    assert report["failure_count"] == 0, report["failures"]


def test_reference_checks_are_what_registries_add(tmp_path: Path, registries) -> None:
    """A structurally valid run naming an unregistered study must still fail."""

    document = _conformant_document()
    document["study_id"] = "study-that-does-not-exist"
    _place(tmp_path / "datasets", document["run_id"], document)

    without = audit_new_runs(tmp_path, "datasets")
    with_registries = audit_new_runs(tmp_path, "datasets", registries=registries)

    assert without["failure_count"] == 0
    assert with_registries["failure_count"] == 1
    assert any(
        "STUDY" in code or "REFERENCE" in code
        for code in with_registries["failures"][0]["issue_codes"]
    ), with_registries["failures"][0]["issue_codes"]


def test_frozen_run_is_grandfathered(tmp_path: Path, registries) -> None:
    """A frozen run id is exempt even with a body that could not pass today."""

    frozen = sorted(LEGACY_RUN_IDS)[0]
    _place(tmp_path / "datasets", frozen, {"run_id": frozen})
    report = audit_new_runs(tmp_path, "datasets", registries=registries)
    assert report["new_run_count"] == 0
    assert report["failure_count"] == 0
    assert report["runs"][0]["frozen_legacy"] is True


def test_missing_run_id_is_treated_as_new(tmp_path: Path, registries) -> None:
    """No run_id cannot mean "grandfathered"."""

    _place(tmp_path / "datasets", "anonymous", {"schema_version": "1.0.0"})
    report = audit_new_runs(tmp_path, "datasets", registries=registries)
    assert report["new_run_count"] == 1
    assert report["failure_count"] == 1
    assert report["failures"][0]["run_id"] == ""


def test_unreadable_metadata_is_reported(tmp_path: Path) -> None:
    target = tmp_path / "datasets" / "probe-study" / "data" / "raw" / "broken"
    target.mkdir(parents=True)
    (target / RUN_METADATA_NAME).write_text("{ not json", encoding="utf-8")
    report = audit_new_runs(tmp_path, "datasets")
    assert report["failure_count"] == 1
    assert report["failures"][0]["issue_codes"] == ["RUN_METADATA_UNREADABLE"]


def test_absent_datasets_root_is_empty_not_an_error(tmp_path: Path) -> None:
    report = audit_new_runs(tmp_path, "datasets")
    assert report["run_count"] == 0
    assert report["failure_count"] == 0


def test_audit_is_read_only(tmp_path: Path, registries) -> None:
    document = _conformant_document()
    target = _place(tmp_path / "datasets", document["run_id"], document)
    before = (target / RUN_METADATA_NAME).read_bytes()
    audit_new_runs(tmp_path, "datasets", registries=registries)
    assert (target / RUN_METADATA_NAME).read_bytes() == before
    assert sorted(p.name for p in target.iterdir()) == [RUN_METADATA_NAME]
