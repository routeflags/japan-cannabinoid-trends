"""External collector staging: ``stage_run`` -> ``adopt_staged`` (G1 §13).

These tests run the *real* recorded Google Trends series kept in the
repository (``datasets/cannabinoid-multi-trends/data/raw/google_trends/``) through
the staging producer, so the replay shape the adapter assumes is exercised
against a response an MCP session actually returned.  The repository raw data
is only read, never rewritten (hashes asserted before/after).

Everything runs offline in a tmp workspace: staging copies the collector's file
into ``.staging/``, adoption moves it to the catalog.
"""

import json
from dataclasses import replace
from pathlib import Path

from validation.integrity import sha256_file
from validation.pipeline import validate_full

from collection.core.pipeline import (
    ARTIFACT_MANIFEST_NAME,
    RUN_METADATA_NAME,
    CollectedArtifact,
    adopt_staged,
    stage_run,
)

from conftest import RECORDED_CBD_5Y, load_json, make_plan, make_workspace

STUDY_ID = "cannabinoid-multi-trends"
RUN_ID = "20261012T064246Z-google-trends-staging-cbd-5y"
SCHEMA_ID = "google-trends-interest-over-time-v1"


def _series() -> dict:
    return load_json(RECORDED_CBD_5Y)


def _staging_plan() -> dict:
    """The plan that describes the real recorded run (5y CBD リキッド)."""
    return make_plan(
        term="CBD リキッド",
        timeframe="today 5-y",
        start="2021-10-10T00:00:00Z",
        end_exclusive="2026-10-12T00:00:00Z",
        window_id="2021-10-10_2026-10-12",
        query_id="cbd-liquid-ja",
        compound_id="compound_cbd",
        study_id=STUDY_ID,
        # A staged run makes no request, so it requires no capability.
        required_capabilities=(),
    )


def _artifact(series: dict) -> CollectedArtifact:
    return CollectedArtifact(
        source=str(RECORDED_CBD_5Y),
        path="payload.json",
        artifact_type="timeseries",
        format="json",
        schema_id=SCHEMA_ID,
        record_count=len(series["data"]),
    )


def _temporal(series: dict) -> dict:
    dates = sorted(point["date"] for point in series["data"])
    return {
        "granularity": "week",
        "week_start": "sunday",
        "collector_window_type": "relative_duration",
        "exact_window_match": False,
        "boundary_semantics": (
            "timeframe resolved by the collector at request time; the observed "
            "range is the bucket-label range of the returned series"
        ),
        "observed_min_timestamp": f"{dates[0]}T00:00:00Z",
        "observed_max_timestamp": f"{dates[-1]}T00:00:00Z",
    }


def _stage(root: Path, registries, *, run_id=RUN_ID, **overrides):
    series = _series()
    kwargs = {
        "artifacts": [_artifact(series)],
        "execution": {
            "status": "success",
            "returned_count": len(series["data"]),
            "errors": [],
            "pagination_exhausted": True,
        },
        "started_at": series["collected_at"],
        "finished_at": series["collected_at"],
        "temporal": _temporal(series),
        "submitted_parameters": {
            "tool": "interest_over_time",
            "terms": [series["keyword"]],
            "geo": series["geo"],
            "timeframe": series["timeframe"],
        },
        "environment": {"collection_mode": "recorded_replay"},
    }
    kwargs.update(overrides)
    return stage_run(
        _staging_plan(),
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
        run_id=run_id,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# happy path
# ---------------------------------------------------------------------------


def test_staging_writes_a_run_that_adoption_catalogs(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    result = _stage(root, registries)

    assert result.action == "staged", [i.code for i in result.issues]
    assert result.run_id == RUN_ID
    staged = Path(result.staging_dir)
    assert staged == root / ".staging" / RUN_ID
    assert sorted(p.name for p in staged.iterdir()) == [
        ARTIFACT_MANIFEST_NAME,
        "payload.json",
        RUN_METADATA_NAME,
    ]

    adopted = adopt_staged(
        staged,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    assert adopted.action == "adopted", [i.code for i in adopted.issues]
    assert Path(adopted.final_dir) == (
        root / "datasets" / STUDY_ID / "data" / "raw" / "google_trends" / RUN_ID
    )


def test_cataloged_run_is_strict_valid_with_verified_artifacts(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    adopted = adopt_staged(
        Path(_stage(root, registries).staging_dir),
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    final = Path(adopted.final_dir)

    document = load_json(final / RUN_METADATA_NAME)
    outcome = validate_full(
        document,
        schema_id="collection-run-v1",
        target=str(final),
        registries=registries,
        base_dir=final,
        verify_artifacts=True,
    )
    assert outcome.valid is True, [i.to_dict() for i in outcome.issues]
    assert not [i for i in outcome.issues if i.severity in ("warning",)]


def test_payload_is_the_collectors_file_byte_for_byte(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    adopted = adopt_staged(
        Path(_stage(root, registries).staging_dir),
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    payload = Path(adopted.final_dir) / "payload.json"
    assert payload.read_bytes() == RECORDED_CBD_5Y.read_bytes()

    manifest = load_json(Path(adopted.final_dir) / ARTIFACT_MANIFEST_NAME)
    artifact = manifest["artifacts"][0]
    assert artifact["sha256"] == sha256_file(RECORDED_CBD_5Y)
    assert artifact["byte_length"] == RECORDED_CBD_5Y.stat().st_size
    assert artifact["record_count"] == len(_series()["data"])
    assert artifact["layer"] == "raw"


def test_repository_raw_is_only_read(tmp_path, registries):
    before = sha256_file(RECORDED_CBD_5Y)
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    _stage(root, registries)
    assert sha256_file(RECORDED_CBD_5Y) == before


def test_artifact_in_a_subdirectory_is_staged_and_cataloged(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    artifact = replace(_artifact(_series()), path="series/payload.json")
    staged = _stage(root, registries, artifacts=[artifact])

    assert staged.action == "staged", [i.code for i in staged.issues]
    copied = Path(staged.staging_dir) / "series" / "payload.json"
    assert copied.read_bytes() == RECORDED_CBD_5Y.read_bytes()

    adopted = adopt_staged(
        Path(staged.staging_dir),
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    assert adopted.action == "adopted", [i.code for i in adopted.issues]
    assert (Path(adopted.final_dir) / "series" / "payload.json").is_file()


def test_collector_identity_comes_from_the_registry(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    staged = Path(_stage(root, registries).staging_dir)
    document = load_json(staged / RUN_METADATA_NAME)

    assert document["collector"] == {
        "collector_id": "google-trends-mcp",
        "adapter_id": "google-trends-mcp@1",
        "version": "0.1.1",
        "provider": "mcp",
        "transport": "mcp",
        "external_id": "google-trends-mcp",
    }
    assert document["environment"]["adapter"]["collection_mode"] == "external_staged"
    assert document["temporal_provenance"]["observed_min_timestamp"] == (
        _temporal(_series())["observed_min_timestamp"]
    )


# ---------------------------------------------------------------------------
# refusals (fail closed, nothing staged)
# ---------------------------------------------------------------------------


def _assert_stopped(result, code):
    assert result.action == "stopped"
    assert code in [issue.code for issue in result.issues], result.issues


def test_missing_artifact_file_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    artifact = replace(_artifact(_series()), source=str(tmp_path / "absent.json"))
    result = _stage(root, registries, artifacts=[artifact])
    _assert_stopped(result, "STAGING_ARTIFACT_MISSING")
    assert not (root / ".staging" / RUN_ID).exists()


def test_artifact_path_outside_the_run_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    artifact = replace(_artifact(_series()), path="../escaped.json")
    result = _stage(root, registries, artifacts=[artifact])
    _assert_stopped(result, "STAGING_ARTIFACT_PATH_UNSAFE")


def test_staging_without_artifacts_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    _assert_stopped(_stage(root, registries, artifacts=[]), "STAGING_NO_ARTIFACTS")


def test_reusing_a_cataloged_run_id_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    adopt_staged(
        Path(_stage(root, registries).staging_dir),
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    _assert_stopped(_stage(root, registries), "RUN_ID_ALREADY_EXISTS")


def test_unregistered_collector_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    plan = _staging_plan()
    plan["collector_id"] = "no-such-collector"
    series = _series()
    result = stage_run(
        plan,
        artifacts=[_artifact(series)],
        execution={"status": "success", "returned_count": len(series["data"]), "errors": []},
        started_at=series["collected_at"],
        finished_at=series["collected_at"],
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    _assert_stopped(result, "STAGING_COLLECTOR_UNKNOWN")


def test_incomplete_window_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    plan = _staging_plan()
    del plan["window"]["granularity"]
    series = _series()
    result = stage_run(
        plan,
        artifacts=[_artifact(series)],
        execution={"status": "success", "returned_count": len(series["data"]), "errors": []},
        started_at=series["collected_at"],
        finished_at=series["collected_at"],
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    _assert_stopped(result, "STAGING_WINDOW_INCOMPLETE")


def test_window_that_contradicts_the_registry_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    plan = _staging_plan()
    plan["window"]["start"] = "2020-01-01T00:00:00Z"
    series = _series()
    result = stage_run(
        plan,
        artifacts=[_artifact(series)],
        execution={"status": "success", "returned_count": len(series["data"]), "errors": []},
        started_at=series["collected_at"],
        finished_at=series["collected_at"],
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    assert result.action == "stopped"
    assert not (root / ".staging" / RUN_ID).exists()


def test_finish_before_start_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    _assert_stopped(
        _stage(root, registries, finished_at="2026-10-11T00:00:00Z"),
        "STAGING_TIMESTAMP_ORDER",
    )


def test_run_id_that_is_not_a_path_component_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    _assert_stopped(_stage(root, registries, run_id="../escaped-run"), "RUN_ID_UNSAFE")
    assert not (tmp_path / "escaped-run").exists()
    assert not (root / ".staging").exists()


def test_adoption_refuses_a_declared_run_id_that_escapes_the_run_directory(
    tmp_path, registries
):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    staged = root / ".staging" / "20261012T064246Z-google-trends-handover"
    staged.mkdir(parents=True)
    (staged / RUN_METADATA_NAME).write_text(
        json.dumps({"run_id": "../escaped-adopt"}), encoding="utf-8"
    )

    result = adopt_staged(
        staged,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )

    _assert_stopped(result, "RUN_ID_UNSAFE")
    assert staged.is_dir()  # a refused run is not moved anywhere
    assert not (root / "escaped-adopt").exists()
    assert not (root / "datasets" / STUDY_ID / "data" / "escaped-adopt").exists()


def test_study_id_that_is_not_a_path_component_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    # ``datasets/../escaped-study`` resolves to a real directory, so the
    # "does the study directory exist" check alone would let it through.
    (root / "escaped-study").mkdir()
    plan = _staging_plan()
    plan["study_id"] = "../escaped-study"
    series = _series()

    result = stage_run(
        plan,
        artifacts=[_artifact(series)],
        execution={"status": "success", "returned_count": len(series["data"]), "errors": []},
        started_at=series["collected_at"],
        finished_at=series["collected_at"],
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )

    _assert_stopped(result, "STUDY_ID_UNSAFE")
    assert not (root / ".staging").exists()


def test_undeclared_execution_outcome_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    _assert_stopped(_stage(root, registries, execution={}), "STAGING_EXECUTION_INCOMPLETE")
    assert not (root / ".staging").exists()


def test_declared_environment_cannot_restate_the_fingerprint(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    staged = _stage(
        root,
        registries,
        environment={
            "collection_mode": "recorded_replay",
            "adapter": {"collection_mode": "live_fetched", "collector_version": "9.9.9"},
            "collection_core_version": "0.0.1",
            "runtime_version": "python-0.0.0",
            "code_commit": "0" * 40,
        },
    )
    environment = load_json(Path(staged.staging_dir) / RUN_METADATA_NAME)["environment"]

    assert environment["adapter"] == {
        "collection_mode": "external_staged",
        "collector_version": "0.1.1",
    }
    assert environment["collection_mode"] == "recorded_replay"
    assert environment["collection_core_version"] == "1.0.0"
    assert environment["runtime_version"] != "python-0.0.0"
    assert environment.get("code_commit") != "0" * 40


def test_artifact_path_without_a_filename_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    artifact = replace(_artifact(_series()), path=".")
    _assert_stopped(
        _stage(root, registries, artifacts=[artifact]),
        "STAGING_ARTIFACT_PATH_UNSAFE",
    )


def test_unknown_study_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=(STUDY_ID,))
    plan = _staging_plan()
    plan["study_id"] = "not-a-study"
    series = _series()
    result = stage_run(
        plan,
        artifacts=[_artifact(series)],
        execution={"status": "success", "returned_count": len(series["data"]), "errors": []},
        started_at=series["collected_at"],
        finished_at=series["collected_at"],
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    _assert_stopped(result, "STUDY_DIRECTORY_MISSING")
