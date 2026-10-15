"""CLI contract tests (P5-1..P5-6, P8 CLI surface, CV-18).

Exit code paths are exercised individually:
0 = success / 1 = data failure / 2 = schema/config error / 3 = I/O error.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from validation.cli import EXIT_CONFIG, EXIT_DATA, EXIT_IO, EXIT_OK, main
from validation.legacy import LEGACY_RUN_IDS

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
REGISTRIES = FIXTURES / "registries"

LEGACY_FILE = (
    REPO_ROOT
    / "datasets"
    / "cbx-search-trends"
    / "data"
    / "raw"
    / "google_trends"
    / "20261001T115959Z-google-trends-cbx-rikiddo"
    / "run_metadata.json"
)


def _registry_tree(tmp_path: Path):
    config = tmp_path / "config"
    metadata = tmp_path / "metadata"
    config.mkdir(parents=True)
    (metadata / "queries").mkdir(parents=True)
    (metadata / "studies").mkdir(parents=True)
    shutil.copy(REGISTRIES / "sources.json", config / "sources.json")
    shutil.copy(REGISTRIES / "collectors.json", config / "collectors.json")
    shutil.copy(REGISTRIES / "queries.json", metadata / "queries" / "query-registry.json")
    shutil.copy(
        REGISTRIES / "query-variants.json",
        metadata / "queries" / "query-variants.json",
    )
    shutil.copy(
        REGISTRIES / "study-registry.json",
        metadata / "studies" / "study-registry.json",
    )
    return config, metadata


def _isolated_registry_args(tmp_path: Path) -> list[str]:
    """Point the CLI at empty registry dirs so repository files are absent."""
    return [
        "--config-dir",
        str(tmp_path / "empty-config"),
        "--metadata-dir",
        str(tmp_path / "empty-metadata"),
    ]


def _valid_run(tmp_path: Path, *, with_manifest: bool) -> dict:
    document = json.loads((FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8"))
    if with_manifest:
        import hashlib

        payload = tmp_path / "payload.json"
        payload.write_bytes(b'{"records": []}')
        manifest = {
            "schema_version": "1.0.0",
            "run_id": document["run_id"],
            "artifacts": [
                {
                    "artifact_id": "artifact-001",
                    "path": "payload.json",
                    "artifact_type": "raw_records",
                    "format": "json",
                    "schema_id": "social-post-v1",
                    "byte_length": payload.stat().st_size,
                    "sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
                    "layer": "raw",
                    "completeness": "complete",
                }
            ],
        }
        (tmp_path / "artifact-manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
    else:
        document.pop("artifact_manifest", None)
    return document


def _study_tree(tmp_path: Path, *, with_manifest: bool) -> Path:
    run_dir = tmp_path / "datasets" / "study-x" / "data" / "raw" / "run-1"
    run_dir.mkdir(parents=True)
    document = _valid_run(run_dir, with_manifest=with_manifest)
    (run_dir / "run_metadata.json").write_text(json.dumps(document), encoding="utf-8")
    return tmp_path / "datasets"


# ---------------------------------------------------------------------------
# validate (P5-1 / P5-4 / P5-6)
# ---------------------------------------------------------------------------


def test_validate_valid_file_exit_0(capsys, tmp_path):
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(FIXTURES / "collection_run_valid.json"),
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert captured.out == ""  # text mode: no machine output on stdout
    assert "OK strict collection-run-v1" in captured.err


def test_validate_json_report_on_stdout(capsys, tmp_path):
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(FIXTURES / "collection_run_valid.json"),
            "--format",
            "json",
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["validation_version"] == "1.0.0"
    assert report["schema_id"] == "collection-run-v1"
    assert report["valid"] is True
    assert report["issues"] == []


def test_validate_real_legacy_file_exit_1(capsys, tmp_path):
    """End-to-end on the real repository data (read-only)."""
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(LEGACY_FILE),
            "--format",
            "json",
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_DATA
    assert report["valid"] is False
    assert report["issues"][0]["code"] == "REQUIRED_FIELD_MISSING"


def test_validate_unknown_schema_exit_2(capsys, tmp_path):
    code = main(
        [
            "validate",
            "--schema",
            "no-such-schema",
            "--file",
            str(FIXTURES / "collection_run_valid.json"),
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_CONFIG
    assert "Unknown schema" in captured.err


def test_validate_missing_file_exit_3(capsys, tmp_path):
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(tmp_path / "nonexistent.json"),
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_IO
    assert "cannot read input file" in captured.err


def test_validate_malformed_json_exit_3(capsys, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(bad),
            *_isolated_registry_args(tmp_path),
        ]
    )
    assert code == EXIT_IO


def test_validate_output_file(capsys, tmp_path):
    output = tmp_path / "reports" / "report.json"
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(FIXTURES / "collection_run_valid.json"),
            "--format",
            "json",
            "--output",
            str(output),
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert captured.out == ""
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["valid"] is True


def test_validate_with_registries_reports_info_issue(capsys, tmp_path):
    """Reference checks are wired in when registries exist; the unverified
    fixture collector yields an info issue without failing the run."""
    config, metadata = _registry_tree(tmp_path)
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(FIXTURES / "collection_run_valid.json"),
            "--format",
            "json",
            "--config-dir",
            str(config),
            "--metadata-dir",
            str(metadata),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["valid"] is True
    assert [issue["code"] for issue in report["issues"]] == [
        "COLLECTOR_LEGACY_REFERENCE"
    ]


def test_validate_malformed_registry_exit_2(capsys, tmp_path):
    config, metadata = _registry_tree(tmp_path)
    (config / "sources.json").write_text("{broken", encoding="utf-8")
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(FIXTURES / "collection_run_valid.json"),
            "--config-dir",
            str(config),
            "--metadata-dir",
            str(metadata),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_CONFIG
    assert "registry file cannot be read" in captured.err


# ---------------------------------------------------------------------------
# legacy profile (P5-5 / P8-3)
# ---------------------------------------------------------------------------


def test_legacy_profile_audit_exit_0(capsys, tmp_path):
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(LEGACY_FILE),
            "--profile",
            "legacy",
            "--format",
            "json",
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["profile"] == "legacy_audit"
    assert report["status"] == "incomplete"
    assert report["run_id"] == "20261001T115959Z-google-trends-cbx-rikiddo"
    assert report["missing_fields"]


def test_legacy_profile_bypass_exit_2(capsys, tmp_path):
    """A new run must not use the legacy profile (P8-3)."""
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(FIXTURES / "collection_run_valid.json"),
            "--profile",
            "legacy",
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_CONFIG
    assert "frozen legacy audit list" in captured.err


# ---------------------------------------------------------------------------
# validate-study / validate-registries / validate-all
# ---------------------------------------------------------------------------


def test_validate_study_no_targets_exit_0(capsys, tmp_path):
    code = main(
        [
            "validate-study",
            "--study",
            "nothing-here",
            "--datasets-root",
            str(tmp_path),
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert "NOTE" in captured.err


def test_validate_study_valid_tree_exit_0(capsys, tmp_path):
    datasets_root = _study_tree(tmp_path, with_manifest=True)
    config, metadata = _registry_tree(tmp_path)
    code = main(
        [
            "validate-study",
            "--study",
            "study-x",
            "--datasets-root",
            str(datasets_root),
            "--format",
            "json",
            "--config-dir",
            str(config),
            "--metadata-dir",
            str(metadata),
        ]
    )
    captured = capsys.readouterr()
    bundle = json.loads(captured.out)
    assert code == EXIT_OK
    assert bundle["valid"] is True
    assert len(bundle["reports"]) == 1


def test_validate_study_missing_manifest_exit_3(capsys, tmp_path):
    datasets_root = _study_tree(tmp_path, with_manifest=False)
    config, metadata = _registry_tree(tmp_path)
    document = json.loads(
        (datasets_root / "study-x" / "data" / "raw" / "run-1" / "run_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    document["artifact_manifest"] = "absent.json"
    (datasets_root / "study-x" / "data" / "raw" / "run-1" / "run_metadata.json").write_text(
        json.dumps(document), encoding="utf-8"
    )
    code = main(
        [
            "validate-study",
            "--study",
            "study-x",
            "--datasets-root",
            str(datasets_root),
            "--config-dir",
            str(config),
            "--metadata-dir",
            str(metadata),
        ]
    )
    assert code == EXIT_IO


def test_validate_study_real_legacy_default_cbsearch(capsys, tmp_path):
    """P5-2 acceptance: the existing study reports strict failures, and the legacy
    profile stays usable for its frozen runs.

    The study also holds contract-era runs now (the 2026-10-15 boundary
    measurements), so the study as a whole no longer passes under either profile:
    strict fails on the legacy runs, and legacy refuses exactly the runs outside
    the frozen list (a new run may not be validated under an audit profile built
    for that list).  Asserting on that set rather than on ids keeps this true when
    pass 2 of the measurement protocol adds runs.
    """

    strict = main(
        [
            "validate-study",
            "--study",
            "cbx-search-trends",
            *_isolated_registry_args(tmp_path),
        ]
    )
    assert strict == EXIT_DATA
    legacy = main(
        [
            "validate-study",
            "--study",
            "cbx-search-trends",
            "--profile",
            "legacy",
            *_isolated_registry_args(tmp_path),
        ]
    )
    # Refusing an audit profile for a run outside the frozen list is a
    # configuration error (2), not a data verdict on that run.
    assert legacy == EXIT_CONFIG

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "legacy profile is only allowed for run_ids in the frozen legacy audit list" in output
    refused = re.findall(r"\(got '([^']+)'\)", output)
    assert refused, output
    for run_id in refused:
        assert run_id not in LEGACY_RUN_IDS, run_id


def test_validate_registries_no_files_exit_0(capsys, tmp_path):
    code = main(
        [
            "validate-registries",
            "--config-dir",
            str(tmp_path / "no-config"),
            "--metadata-dir",
            str(tmp_path / "no-metadata"),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert "nothing to validate" in captured.err


def test_validate_registries_valid_files_exit_0(capsys, tmp_path):
    config, metadata = _registry_tree(tmp_path)
    code = main(
        [
            "validate-registries",
            "--config-dir",
            str(config),
            "--metadata-dir",
            str(metadata),
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    bundle = json.loads(captured.out)
    assert code == EXIT_OK
    assert bundle["valid"] is True
    assert {report["schema_id"] for report in bundle["reports"]} == {
        "source-registry-v1",
        "collector-registry-v1",
        "query-registry-v1",
        "query-variants-registry-v1",
        "study-registry-v1",
    }


def test_validate_registries_broken_file_exit_1(capsys, tmp_path):
    config, metadata = _registry_tree(tmp_path)
    broken = json.loads((config / "sources.json").read_text(encoding="utf-8"))
    del broken["sources"][0]["kind"]
    (config / "sources.json").write_text(json.dumps(broken), encoding="utf-8")
    code = main(
        [
            "validate-registries",
            "--config-dir",
            str(config),
            "--metadata-dir",
            str(metadata),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_DATA
    assert "REQUIRED_FIELD_MISSING" in captured.err


def test_validate_all_bundle(capsys, tmp_path):
    datasets_root = _study_tree(tmp_path, with_manifest=False)
    config, metadata = _registry_tree(tmp_path)
    output = tmp_path / "all.json"
    code = main(
        [
            "validate-all",
            "--datasets-root",
            str(datasets_root),
            "--config-dir",
            str(config),
            "--metadata-dir",
            str(metadata),
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )
    captured = capsys.readouterr()
    bundle = json.loads(output.read_text(encoding="utf-8"))
    assert code == EXIT_OK
    assert bundle["valid"] is True
    assert len(bundle["reports"]) == 6  # 5 registries + 1 run
    assert captured.out == ""


# ---------------------------------------------------------------------------
# audit-legacy (P8-2)
# ---------------------------------------------------------------------------


def test_audit_legacy_command(capsys, tmp_path):
    datasets = tmp_path / "datasets" / "study-y" / "data" / "raw" / "run-a"
    datasets.mkdir(parents=True)
    (datasets / "run_metadata.json").write_text(
        json.dumps({"run_id": "legacy-a", "source": "x"}), encoding="utf-8"
    )
    broken = tmp_path / "datasets" / "study-y" / "data" / "raw" / "run-b"
    broken.mkdir(parents=True)
    (broken / "run_metadata.json").write_text("{broken", encoding="utf-8")

    output = tmp_path / "audit.json"
    code = main(
        [
            "audit-legacy",
            "--datasets-root",
            str(tmp_path / "datasets"),
            "--output",
            str(output),
        ]
    )
    captured = capsys.readouterr()
    audit = json.loads(output.read_text(encoding="utf-8"))
    assert code == EXIT_OK
    assert audit["count"] == 2
    assert audit["raw_modified"] is False
    statuses = {entry["run_id"]: entry["status"] for entry in audit["runs"]}
    assert statuses[None] == "unreadable"
    entry = next(e for e in audit["runs"] if e["run_id"] == "legacy-a")
    assert entry["status"] == "incomplete"
    assert entry["unchanged"] is True
    assert "legacy audit written" in captured.err


# ---------------------------------------------------------------------------
# gate-plan (P6-1 CLI surface)
# ---------------------------------------------------------------------------


def test_gate_plan_proceed_exit_0(capsys, tmp_path):
    config, metadata = _registry_tree(tmp_path)
    code = main(
        [
            "gate-plan",
            "--file",
            str(FIXTURES / "collection_plan.json"),
            "--format",
            "json",
            "--config-dir",
            str(config),
            "--metadata-dir",
            str(metadata),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["action"] == "proceed"
    assert report["valid"] is True


def test_gate_plan_stop_exit_1(capsys, tmp_path):
    config, metadata = _registry_tree(tmp_path)
    plan = json.loads((FIXTURES / "collection_plan.json").read_text(encoding="utf-8"))
    plan["collector_id"] = "x-apify-example"  # unverified capabilities
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    code = main(
        [
            "gate-plan",
            "--file",
            str(plan_path),
            "--format",
            "json",
            "--config-dir",
            str(config),
            "--metadata-dir",
            str(metadata),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_DATA
    assert report["action"] == "stop"
    assert "GATE_CAPABILITY_UNKNOWN" in [issue["code"] for issue in report["issues"]]


def test_gate_plan_missing_file_exit_3(capsys, tmp_path):
    code = main(
        [
            "gate-plan",
            "--file",
            str(tmp_path / "none.json"),
            *_isolated_registry_args(tmp_path),
        ]
    )
    assert code == EXIT_IO


# ---------------------------------------------------------------------------
# gate-run (post-collection L1 decision)
# ---------------------------------------------------------------------------


def _write_staged_run(tmp_path: Path, *, with_manifest: bool) -> Path:
    document = _valid_run(tmp_path, with_manifest=with_manifest)
    path = tmp_path / "run_metadata.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_gate_run_catalogs_a_valid_run(capsys, tmp_path):
    run_file = _write_staged_run(tmp_path, with_manifest=True)
    code = main(
        [
            "gate-run",
            "--file",
            str(run_file),
            "--format",
            "json",
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["action"] == "catalog"
    assert report["valid"] is True


def test_gate_run_quarantines_a_run_without_artifact_evidence(capsys, tmp_path):
    run_file = _write_staged_run(tmp_path, with_manifest=False)
    code = main(
        [
            "gate-run",
            "--file",
            str(run_file),
            "--format",
            "json",
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_DATA
    assert report["action"] == "quarantine"
    assert "MISSINGNESS_RAW_EVIDENCE_MISSING" in [
        issue["code"] for issue in report["issues"]
    ]


def test_gate_run_quarantines_a_tampered_payload(capsys, tmp_path):
    run_file = _write_staged_run(tmp_path, with_manifest=True)
    (tmp_path / "payload.json").write_bytes(b'{"records": ["tampered"]}')
    code = main(
        [
            "gate-run",
            "--file",
            str(run_file),
            "--format",
            "json",
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_DATA
    assert report["action"] == "quarantine"
    codes = [issue["code"] for issue in report["issues"]]
    assert "ARTIFACT_HASH_MISMATCH" in codes
    assert "ARTIFACT_SIZE_MISMATCH" in codes


def test_gate_run_missing_file_exit_3(capsys, tmp_path):
    code = main(
        [
            "gate-run",
            "--file",
            str(tmp_path / "none.json"),
            *_isolated_registry_args(tmp_path),
        ]
    )
    assert code == EXIT_IO


def test_gate_run_refuses_a_non_object_document(capsys, tmp_path):
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    code = main(
        [
            "gate-run",
            "--file",
            str(path),
            "--format",
            "json",
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_DATA
    assert report["action"] == "quarantine"
    assert report["issues"][0]["code"] == "DOCUMENT_FORMAT_INVALID"


def test_validate_refuses_a_non_object_document(capsys, tmp_path):
    """Every command that validates a file must survive a non-object JSON."""
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    code = main(
        [
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(path),
            "--format",
            "json",
            *_isolated_registry_args(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_DATA
    assert report["valid"] is False
    assert report["issues"][0]["code"] == "DOCUMENT_FORMAT_INVALID"
    assert report["issues"][0]["path"] == ""


# ---------------------------------------------------------------------------
# compare-runs (L2)
# ---------------------------------------------------------------------------


def test_compare_runs_reports_conditional(capsys, tmp_path):
    document = json.loads(
        (FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8")
    )
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    for path in (a, b):
        path.write_text(json.dumps(document), encoding="utf-8")
    code = main(["compare-runs", "--a", str(a), "--b", str(b), "--format", "json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK  # L2 restricts comparison; it never invalidates data
    assert report["gate"] == "L2"
    assert report["status"] == "conditional"


def test_compare_runs_detects_a_window_mismatch(capsys, tmp_path):
    document = json.loads(
        (FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8")
    )
    other = json.loads(json.dumps(document))
    other["temporal_provenance"]["requested_end_exclusive"] = "2026-10-01T00:00:00Z"
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps(document), encoding="utf-8")
    b.write_text(json.dumps(other), encoding="utf-8")
    code = main(["compare-runs", "--a", str(a), "--b", str(b), "--format", "json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["status"] == "not_comparable"
    assert "c2_window_mismatch" in report["reasons"]


def test_compare_runs_missing_file_exit_3(capsys, tmp_path):
    document = json.loads(
        (FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8")
    )
    a = tmp_path / "a.json"
    a.write_text(json.dumps(document), encoding="utf-8")
    code = main(
        ["compare-runs", "--a", str(a), "--b", str(tmp_path / "none.json")]
    )
    captured = capsys.readouterr()
    assert code == EXIT_IO
    assert "cannot read input file" in captured.err


# ---------------------------------------------------------------------------
# G2 query commands (classify-query / compare-queries / audit-queries)
# ---------------------------------------------------------------------------


def _repo_args() -> list[str]:
    return [
        "--config-dir",
        str(REPO_ROOT / "config"),
        "--metadata-dir",
        str(REPO_ROOT / "metadata"),
    ]


def test_classify_query_relevant_exit_0(capsys):
    code = main(
        ["classify-query", "--text", "CBD リキッド", "--format", "json", *_repo_args()]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["classification"] == "relevant"
    assert report["query_id"] == "cbd-liquid-ja"
    assert report["registry_version"] == "1.0.0"


def test_classify_query_variant_and_normalization(capsys):
    """Case / width differences are absorbed by normalization (not by extra
    variant entries) and a registered no-space variant resolves."""
    for text in ("CBDリキッド", "cbd リキッド", "ＣＢＤ"):
        code = main(
            ["classify-query", "--text", text, "--format", "json", *_repo_args()]
        )
        captured = capsys.readouterr()
        report = json.loads(captured.out)
        assert code == EXIT_OK, report
        assert report["classification"] == "relevant"


def test_classify_query_durban_cbd_is_not_adoptable(capsys):
    code = main(
        ["classify-query", "--text", "Durban CBD", "--format", "json", *_repo_args()]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_DATA  # classified, but must not be adopted as a compound
    assert report["classification"] == "irrelevant"
    assert report["rule_id"] == "non-compound-durban-cbd"
    assert report["evidence"]


def test_classify_query_missing_registry_exit_2(capsys, tmp_path):
    code = main(
        ["classify-query", "--text", "CBD", *_isolated_registry_args(tmp_path)]
    )
    assert code == EXIT_CONFIG


def test_compare_queries_intent_mismatch_is_not_comparable(capsys):
    code = main(
        [
            "compare-queries",
            "--a",
            "cbd-general-ja",
            "--b",
            "cbd-liquid-ja",
            "--format",
            "json",
            *_repo_args(),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK  # a verdict, not a data failure
    assert report["gate"] == "G2-query-comparability"
    assert report["status"] == "not_comparable"
    assert "q2_intent_mismatch" in report["reasons"]
    assert "q3_text_mismatch" in report["reasons"]


def test_compare_queries_same_query_is_conditional(capsys):
    code = main(
        [
            "compare-queries",
            "--a",
            "cbd-general-ja",
            "--b",
            "cbd-general-ja",
            "--format",
            "json",
            *_repo_args(),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["status"] == "conditional"


def test_compare_queries_unknown_id_exit_2(capsys):
    code = main(
        [
            "compare-queries",
            "--a",
            "cbd-general-ja",
            "--b",
            "no-such-query",
            *_repo_args(),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_CONFIG
    assert "unknown query_id" in captured.err


def test_audit_queries_command(capsys, tmp_path):
    run_dir = tmp_path / "datasets" / "study-z" / "data" / "raw" / "run-a"
    run_dir.mkdir(parents=True)
    (run_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "run_id": "legacy-a",
                "source": "x",
                "queries": [
                    {"term": "CBD"},
                    {"terms": ["CBX リキッド", "Durban CBD"]},
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "audit.json"
    code = main(
        [
            "audit-queries",
            "--datasets-root",
            str(tmp_path / "datasets"),
            "--output",
            str(output),
            *_repo_args(),
        ]
    )
    captured = capsys.readouterr()
    audit = json.loads(output.read_text(encoding="utf-8"))
    assert code == EXIT_OK
    assert audit["count"] == 1
    assert audit["raw_modified"] is False
    states = {
        entry["text"]: entry["state"] for entry in audit["runs"][0]["queries"]
    }
    assert states["CBD"] == "exact_match"
    assert states["CBX リキッド"] == "exact_match"
    assert states["Durban CBD"] == "ambiguous"
    assert "query inventory written" in captured.err


# ---------------------------------------------------------------------------
# Module entry point (P5-6: the documented invocation form works)
# ---------------------------------------------------------------------------


def test_module_entrypoint_subprocess(tmp_path):
    probe = subprocess.run(
        [sys.executable, "-c", "import validation.cli"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        pytest.skip("validation package is not installed for the subprocess")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "validation.cli",
            "validate",
            "--schema",
            "collection-run-v1",
            "--file",
            str(FIXTURES / "collection_run_valid.json"),
            "--config-dir",
            str(tmp_path / "empty-config"),
            "--metadata-dir",
            str(tmp_path / "empty-metadata"),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == EXIT_OK
    assert "OK" in result.stderr
