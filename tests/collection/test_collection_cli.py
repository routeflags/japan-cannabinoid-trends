"""CLI tests for the collection core (``python -m collection.core.cli``).

Exit codes: 0 adopted / 1 quarantined or stopped / 2 config / 3 I/O.
Offline only (recorded replay fixtures).
"""

import json
from pathlib import Path

from collection.core.cli import EXIT_CONFIG, EXIT_GATE, EXIT_IO, EXIT_OK, main

from conftest import (
    FIXTURE_12M,
    REFERENCE_NOW,
    REFERENCE_NOW_ISO,
    REPO_CONFIG,
    REPO_METADATA,
    load_json,
    make_plan,
    make_workspace,
)

# The stage command's declaration helper and identifiers are shared with the
# driver's contract tests (same package under tests/collection).
from test_staging_driver import (  # noqa: E402  (shared test helper)
    RUN_ID as STAGE_RUN_ID,
    STUDY_ID as STAGE_STUDY_ID,
    _declaration as _stage_declaration_document,
    _run as _stage_run_entry,
    _write as _write_stage_declaration,
)

RUN_ID = "20261013T000000Z-google-trends-cli-12m"


def _write_plan(path: Path, plan: dict) -> Path:
    path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def _base_args(root: Path) -> list:
    return [
        "--workspace",
        str(root),
        "--datasets-root",
        str(root / "datasets"),
        "--config-dir",
        str(REPO_CONFIG),
        "--metadata-dir",
        str(REPO_METADATA),
    ]


def test_collect_adopts_via_cli(capsys, tmp_path):
    root = make_workspace(tmp_path)
    plan_path = _write_plan(tmp_path / "plan.json", make_plan())
    code = main(
        [
            "collect",
            "--plan",
            str(plan_path),
            "--fixture",
            str(FIXTURE_12M),
            "--run-id",
            RUN_ID,
            "--now",
            REFERENCE_NOW_ISO,
            "--format",
            "json",
            *_base_args(root),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["action"] == "adopted"
    assert report["l1"]["valid"] is True
    final = root / "datasets" / "cbx-search-trends" / "data" / "raw" / RUN_ID
    assert (final / "run_metadata.json").is_file()


def test_collect_without_a_session_fails_closed(capsys, tmp_path):
    """No fixture and no live session: the run is recorded as failed and
    quarantined - data is never fabricated."""
    root = make_workspace(tmp_path)
    plan_path = _write_plan(tmp_path / "plan.json", make_plan())
    code = main(
        [
            "collect",
            "--plan",
            str(plan_path),
            "--run-id",
            RUN_ID,
            "--now",
            REFERENCE_NOW_ISO,
            "--format",
            "json",
            *_base_args(root),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_GATE
    assert report["action"] == "quarantined"
    quarantine = root / ".quarantine" / RUN_ID
    document = load_json(quarantine / "run_metadata.json")
    assert document["execution"]["status"] == "failed"
    assert document["execution"]["errors"]
    assert not (root / "datasets" / "cbx-search-trends" / "data" / "raw" / RUN_ID).exists()


def test_collect_unknown_source_exit_2(capsys, tmp_path):
    root = make_workspace(tmp_path)
    plan = make_plan(source_id="x", collector_id=None)
    plan_path = _write_plan(tmp_path / "plan.json", plan)
    code = main(
        ["collect", "--plan", str(plan_path), *_base_args(root)]
    )
    captured = capsys.readouterr()
    assert code == EXIT_CONFIG
    assert "no adapter implementation" in captured.err


def test_collect_missing_plan_exit_3(capsys, tmp_path):
    root = make_workspace(tmp_path)
    code = main(
        ["collect", "--plan", str(tmp_path / "none.json"), *_base_args(root)]
    )
    assert code == EXIT_IO


def test_collect_invalid_plan_stops_exit_1(capsys, tmp_path):
    root = make_workspace(tmp_path)
    plan = make_plan()
    del plan["query_id"]  # required by collection-plan-v1
    plan_path = _write_plan(tmp_path / "plan.json", plan)
    code = main(
        [
            "collect",
            "--plan",
            str(plan_path),
            "--fixture",
            str(FIXTURE_12M),
            "--run-id",
            RUN_ID,
            "--format",
            "json",
            *_base_args(root),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_GATE
    assert report["action"] == "stopped"
    assert any(issue["code"] == "REQUIRED_FIELD_MISSING" for issue in report["issues"])


def test_adopt_command_quarantines_a_tampered_run(capsys, tmp_path):
    from test_pipeline_e2e import _staged_copy
    from conftest import build_replay_adapter
    from collection.core.pipeline import run_collection
    from collection.core.registry import load_registries

    root = make_workspace(tmp_path)
    registries = load_registries(REPO_CONFIG, REPO_METADATA)
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    first = run_collection(
        make_plan(),
        adapter=adapter,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
        run_id=RUN_ID,
        now=REFERENCE_NOW,
    )
    staged = _staged_copy(
        Path(first.final_dir),
        root / ".staging",
        new_run_id="20261013T000001Z-google-trends-cli-tampered",
        mutate_payload=lambda data: data.replace(b'"value": 44', b'"value": 77'),
    )
    code = main(
        ["adopt", "--staged", str(staged), "--format", "json", *_base_args(root)]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_GATE
    assert report["action"] == "quarantined"
    assert "ARTIFACT_HASH_MISMATCH" in [issue["code"] for issue in report["l1"]["issues"]]


def test_adopt_missing_staged_dir_exit_1(capsys, tmp_path):
    root = make_workspace(tmp_path)
    code = main(
        [
            "adopt",
            "--staged",
            str(tmp_path / "nowhere"),
            "--format",
            "json",
            *_base_args(root),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_GATE
    assert report["action"] == "stopped"


# ---------------------------------------------------------------------------
# stage (ISS-20261015-COL-017: declaration-driven staging driver)
# ---------------------------------------------------------------------------


def test_stage_command_stages_then_adopt_catalogs(capsys, tmp_path):
    root = make_workspace(tmp_path, studies=(STAGE_STUDY_ID,))
    declaration = _write_stage_declaration(tmp_path, _stage_declaration_document())
    code = main(
        [
            "stage",
            "--declaration",
            str(declaration),
            "--format",
            "json",
            *_base_args(root),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["runs_requested"] == 1
    assert report["staged"] == 1 and report["stopped"] == 0
    result = report["results"][0]
    assert result["action"] == "staged"
    assert result["run_id"] == STAGE_RUN_ID

    code = main(
        [
            "adopt",
            "--staged",
            result["staging_dir"],
            "--format",
            "json",
            *_base_args(root),
        ]
    )
    captured = capsys.readouterr()
    adopted = json.loads(captured.out)
    assert code == EXIT_OK
    assert adopted["action"] == "adopted"
    final = root / "datasets" / STAGE_STUDY_ID / "data" / "raw" / STAGE_RUN_ID
    assert (final / "run_metadata.json").is_file()


def test_stage_command_reports_a_stopped_run_exit_1(capsys, tmp_path):
    run = _stage_run_entry()
    run["collector_id"] = "no-such-collector"
    root = make_workspace(tmp_path, studies=(STAGE_STUDY_ID,))
    declaration = _write_stage_declaration(tmp_path, _stage_declaration_document(run))
    code = main(
        [
            "stage",
            "--declaration",
            str(declaration),
            "--format",
            "json",
            *_base_args(root),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_GATE
    assert report["stopped"] == 1
    assert "STAGING_COLLECTOR_UNKNOWN" in [
        issue["code"] for issue in report["results"][0]["issues"]
    ]


def test_stage_command_declaration_error_exit_2(capsys, tmp_path):
    document = _stage_declaration_document()
    document["runs"][0]["query"]["query_id"] = "no-such-query"
    root = make_workspace(tmp_path, studies=(STAGE_STUDY_ID,))
    declaration = _write_stage_declaration(tmp_path, document)
    code = main(
        ["stage", "--declaration", str(declaration), *_base_args(root)]
    )
    captured = capsys.readouterr()
    assert code == EXIT_CONFIG
    assert "invalid staging declaration" in captured.err
    assert "no-such-query" in captured.err
    assert not (root / ".staging").exists()


def test_stage_command_unreadable_declaration_exit_3(capsys, tmp_path):
    root = make_workspace(tmp_path, studies=(STAGE_STUDY_ID,))
    missing = main(
        ["stage", "--declaration", str(tmp_path / "absent.json"), *_base_args(root)]
    )
    assert missing == EXIT_IO

    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert main(["stage", "--declaration", str(broken), *_base_args(root)]) == EXIT_IO


def test_stage_command_writes_the_report_file(capsys, tmp_path):
    root = make_workspace(tmp_path, studies=(STAGE_STUDY_ID,))
    declaration = _write_stage_declaration(tmp_path, _stage_declaration_document())
    output = tmp_path / "reports" / "stage.json"
    code = main(
        [
            "stage",
            "--declaration",
            str(declaration),
            "--format",
            "json",
            "--output",
            str(output),
            *_base_args(root),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_OK
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["declaration_name"] == "declaration.json"
    assert "stage: 1 staged / 0 stopped of 1" in captured.err
