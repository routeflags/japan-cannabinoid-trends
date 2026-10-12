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
