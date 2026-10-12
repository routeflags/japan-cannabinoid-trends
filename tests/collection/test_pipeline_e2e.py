"""End-to-end pipeline tests: collect -> L1 -> catalog / quarantine (G1 §3, §10-§13).

Everything runs offline in a tmp workspace; the repository raw data is only
read (and its hashes asserted unchanged).
"""

import json
import shutil
import stat
from pathlib import Path

from validation.comparability import compare_runs
from validation.integrity import sha256_file
from validation.pipeline import validate_full

from collection.core.pipeline import adopt_staged, run_collection

from conftest import (
    FIXTURE_12M,
    FIXTURE_5Y,
    RECORDED_CBD_5Y,
    REFERENCE_NOW,
    build_replay_adapter,
    load_json,
    make_plan,
    make_workspace,
)

RUN_ID_12M = "20261013T000000Z-google-trends-e2e-12m"
RUN_ID_5Y = "20261013T000001Z-google-trends-e2e-5y"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _collect(registries, root, *, fixture, plan, run_id):
    adapter = build_replay_adapter(registries, fixture)
    return run_collection(
        plan,
        adapter=adapter,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
        run_id=run_id,
        now=REFERENCE_NOW,
    )


def _staged_copy(
    catalog_dir: Path,
    staged_root: Path,
    *,
    new_run_id: str,
    mutate_metadata=None,
    mutate_manifest=None,
    mutate_payload=None,
) -> Path:
    """Copy a cataloged run back into staging under a new run_id.

    Used to simulate the staging output of an external collector (and to
    tamper with it).  The copy keeps the manifest hash honest unless a test
    mutates the payload on purpose.
    """
    target = staged_root / new_run_id
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(catalog_dir, target)

    metadata_path = target / "run_metadata.json"
    document = load_json(metadata_path)
    document["run_id"] = new_run_id
    if mutate_metadata is not None:
        mutate_metadata(document)
    metadata_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    manifest_path = target / "artifact-manifest.json"
    manifest = load_json(manifest_path)
    manifest["run_id"] = new_run_id
    for artifact in manifest["artifacts"]:
        artifact["artifact_id"] = artifact["artifact_id"].replace(
            catalog_dir.name, new_run_id
        )
    if mutate_manifest is not None:
        mutate_manifest(manifest)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if mutate_payload is not None:
        payload_path = target / "payload.json"
        payload_path.write_bytes(mutate_payload(payload_path.read_bytes()))
    return target


# ---------------------------------------------------------------------------
# Happy path: collect -> adopt (catalog)
# ---------------------------------------------------------------------------


def test_collect_adopts_a_valid_run(tmp_path, registries):
    root = make_workspace(tmp_path)
    result = _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)

    assert result.action == "adopted", [i.code for i in result.issues]
    assert result.l1 is not None and result.l1.valid is True
    final = Path(result.final_dir)
    assert final == root / "datasets" / "cbx-search-trends" / "data" / "raw" / RUN_ID_12M
    assert sorted(p.name for p in final.iterdir()) == [
        "artifact-manifest.json",
        "payload.json",
        "run_metadata.json",
    ]
    # staging was moved, not copied
    assert not (root / ".staging" / RUN_ID_12M).exists()


def test_adopted_run_is_strict_valid(tmp_path, registries):
    root = make_workspace(tmp_path)
    result = _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)
    document = load_json(Path(result.final_dir) / "run_metadata.json")

    outcome = validate_full(
        document,
        schema_id="collection-run-v1",
        target=str(result.final_dir),
        registries=registries,
        base_dir=Path(result.final_dir),
        verify_artifacts=True,
    )
    assert outcome.valid is True, [i.to_dict() for i in outcome.issues]

    assert document["execution"] == {
        "status": "success",
        "returned_count": 52,
        "errors": [],
        "pagination_exhausted": True,
    }
    assert document["collector"] == {
        "collector_id": "google-trends-mcp",
        "adapter_id": "google-trends-mcp@1",
        "version": "0.1.1",
        "provider": "mcp",
        "transport": "mcp",
        "external_id": "google-trends-mcp",
    }
    assert document["environment"]["adapter"]["collection_mode"] == "recorded_replay"

    manifest = load_json(Path(result.final_dir) / "artifact-manifest.json")
    artifact = manifest["artifacts"][0]
    assert artifact["sha256"] == sha256_file(Path(result.final_dir) / "payload.json")
    assert artifact["record_count"] == 52
    assert artifact["completeness"] == "complete"


def test_observed_zero_run_keeps_its_evidence(tmp_path, registries):
    """A zero-observation run is adopted only with a record_count:0 artifact
    (L1-09: zero is not indistinguishable from missing)."""
    root = make_workspace(tmp_path)
    empty_fixture = tmp_path / "empty.json"
    fixture = load_json(FIXTURE_12M)
    fixture["response"]["data"] = []
    fixture["description"] = "Synthetic empty series (observed-zero evidence test)."
    empty_fixture.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    result = _collect(
        registries, root, fixture=empty_fixture, plan=make_plan(), run_id=RUN_ID_12M
    )
    assert result.action == "adopted"
    document = load_json(Path(result.final_dir) / "run_metadata.json")
    assert document["execution"]["status"] == "success"
    assert document["execution"]["returned_count"] == 0
    manifest = load_json(Path(result.final_dir) / "artifact-manifest.json")
    assert manifest["artifacts"][0]["record_count"] == 0
    assert manifest["artifacts"][0]["completeness"] == "complete"


# ---------------------------------------------------------------------------
# Fail closed: stopped before collection
# ---------------------------------------------------------------------------


def test_invalid_plan_is_stopped(tmp_path, registries):
    root = make_workspace(tmp_path)
    plan = make_plan()
    del plan["required_capabilities"]
    result = _collect(registries, root, fixture=FIXTURE_12M, plan=plan, run_id=RUN_ID_12M)
    assert result.action == "stopped"
    assert any(issue.code == "REQUIRED_FIELD_MISSING" for issue in result.issues)
    assert not (root / ".staging").exists()


def test_adapter_plan_validation_stops_unverified_timeframes(tmp_path, registries):
    """Adapter-level period validation still fails closed when no compiler
    applies (a plan without a window); with a window, the G3 compiler gate
    runs instead (see tests/collection/test_window_compiler.py)."""
    root = make_workspace(tmp_path)
    plan = make_plan(timeframe="today 2-y")
    plan.pop("window")
    result = _collect(registries, root, fixture=FIXTURE_12M, plan=plan, run_id=RUN_ID_12M)
    assert result.action == "stopped"
    assert any(issue.code == "ADAPTER_PLAN_REJECTED" for issue in result.issues)


def test_adapter_identity_mismatch_stops(tmp_path, registries):
    root = make_workspace(tmp_path)
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    adapter.adapter_id = "google-trends-mcp@999"
    result = run_collection(
        make_plan(), adapter=adapter, workspace_root=root,
        datasets_root=root / "datasets", registries=registries, run_id=RUN_ID_12M,
        now=REFERENCE_NOW,
    )
    assert result.action == "stopped"
    assert [issue.code for issue in result.issues] == ["ADAPTER_IDENTITY_MISMATCH"]


def test_adapter_capability_mismatch_stops(tmp_path, registries):
    """The registry is the record of truth: an adapter cannot widen its own
    capabilities (e.g. reporting supported while the registry says unknown)."""
    root = make_workspace(tmp_path)
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    adapter._capabilities["language_filter"] = "supported"
    result = run_collection(
        make_plan(), adapter=adapter, workspace_root=root,
        datasets_root=root / "datasets", registries=registries, run_id=RUN_ID_12M,
        now=REFERENCE_NOW,
    )
    assert result.action == "stopped"
    assert [issue.code for issue in result.issues] == ["ADAPTER_CAPABILITY_MISMATCH"]


def test_missing_study_directory_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path, studies=())
    result = _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)
    assert result.action == "stopped"
    assert [issue.code for issue in result.issues] == ["STUDY_DIRECTORY_MISSING"]


def test_run_id_reuse_is_refused(tmp_path, registries):
    root = make_workspace(tmp_path)
    assert _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M).adopted
    result = _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)
    assert result.action == "stopped"
    assert [issue.code for issue in result.issues] == ["RUN_ID_ALREADY_EXISTS"]


# ---------------------------------------------------------------------------
# Fail closed: collection failure -> quarantine (never zero observations)
# ---------------------------------------------------------------------------


def test_failed_collection_is_quarantined_not_recorded_as_zero(tmp_path, registries):
    root = make_workspace(tmp_path)
    from collection.adapters.google_trends import GoogleTrendsMcpAdapter, SessionMcpTransport

    adapter = GoogleTrendsMcpAdapter(
        SessionMcpTransport(), capabilities={}
    )
    # Use the registry capabilities so the capability cross-check passes; the
    # collection itself is what fails (no live session in this repository).
    from conftest import capabilities_of

    adapter._capabilities = capabilities_of(registries, "google-trends-mcp")
    result = run_collection(
        make_plan(), adapter=adapter, workspace_root=root,
        datasets_root=root / "datasets", registries=registries, run_id=RUN_ID_12M,
        now=REFERENCE_NOW,
    )
    assert result.action == "quarantined"
    quarantine_dir = Path(result.final_dir)
    assert quarantine_dir == root / ".quarantine" / RUN_ID_12M
    assert not (root / "datasets" / "cbx-search-trends" / "data" / "raw" / RUN_ID_12M).exists()

    document = load_json(quarantine_dir / "run_metadata.json")
    assert document["execution"]["status"] == "failed"
    assert document["execution"]["returned_count"] == 0
    assert document["execution"]["errors"], "failure evidence must be recorded"

    # raw (the error record) is preserved, and the reason is recorded
    assert (quarantine_dir / "payload.json").is_file()
    reason = load_json(quarantine_dir / "quarantine-reason.json")
    assert reason["action"] == "quarantine"
    assert reason["run_id"] == RUN_ID_12M
    codes = [issue["code"] for issue in reason["issues"]]
    assert "COLLECTION_FAILED_NOT_ADOPTED" in codes


# ---------------------------------------------------------------------------
# Quarantine (adopt_staged) - tampered / incomplete / secret runs
# ---------------------------------------------------------------------------


def _adopt(registries, root, staged: Path):
    return adopt_staged(
        staged,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )


def test_adopt_valid_staged_run_is_cataloged(tmp_path, registries):
    root = make_workspace(tmp_path)
    first = _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)
    staged = _staged_copy(
        Path(first.final_dir), root / ".staging", new_run_id=RUN_ID_5Y
    )
    result = _adopt(registries, root, staged)
    assert result.action == "adopted", [i.code for i in (result.l1.issues if result.l1 else [])]
    assert (root / "datasets" / "cbx-search-trends" / "data" / "raw" / RUN_ID_5Y).is_dir()


def test_tampered_payload_is_quarantined(tmp_path, registries):
    """a.md §15: raw hash mismatch -> L1 FAIL -> quarantine."""
    root = make_workspace(tmp_path)
    first = _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)
    staged = _staged_copy(
        Path(first.final_dir), root / ".staging", new_run_id=RUN_ID_5Y,
        mutate_payload=lambda data: data.replace(b'"value": 44', b'"value": 99'),
    )
    result = _adopt(registries, root, staged)
    assert result.action == "quarantined"
    codes = [issue.code for issue in result.l1.issues]
    assert "ARTIFACT_HASH_MISMATCH" in codes
    quarantine_dir = Path(result.final_dir)
    assert quarantine_dir.parent.name == ".quarantine"
    reason = load_json(quarantine_dir / "quarantine-reason.json")
    assert "ARTIFACT_HASH_MISMATCH" in [issue["code"] for issue in reason["issues"]]
    # not adopted as research data
    assert not (root / "datasets" / "cbx-search-trends" / "data" / "raw" / RUN_ID_5Y).exists()


def test_metadata_missing_field_is_quarantined(tmp_path, registries):
    root = make_workspace(tmp_path)
    first = _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)
    staged = _staged_copy(
        Path(first.final_dir), root / ".staging", new_run_id=RUN_ID_5Y,
        mutate_metadata=lambda document: document.pop("purpose"),
    )
    result = _adopt(registries, root, staged)
    assert result.action == "quarantined"
    assert "REQUIRED_FIELD_MISSING" in [issue.code for issue in result.l1.issues]


def test_success_with_partial_artifact_is_quarantined(tmp_path, registries):
    root = make_workspace(tmp_path)
    first = _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)

    def mark_partial(manifest):
        manifest["artifacts"][0]["completeness"] = "partial"

    staged = _staged_copy(
        Path(first.final_dir), root / ".staging", new_run_id=RUN_ID_5Y,
        mutate_manifest=mark_partial,
    )
    result = _adopt(registries, root, staged)
    assert result.action == "quarantined"
    assert "COMPLETENESS_INCONSISTENT_WITH_SUCCESS" in [issue.code for issue in result.l1.issues]


def test_secret_in_metadata_is_quarantined_and_restricted(tmp_path, registries):
    """a.md §15: API key混入 -> 保存拒否 (fail closed) + restricted area."""
    root = make_workspace(tmp_path)
    first = _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)

    def inject(document):
        document.setdefault("environment", {})["access_token"] = "sk-" + "a" * 24

    staged = _staged_copy(
        Path(first.final_dir), root / ".staging", new_run_id=RUN_ID_5Y,
        mutate_metadata=inject,
    )
    result = _adopt(registries, root, staged)
    assert result.action == "quarantined"
    assert "SECRET_DETECTED" in [issue.code for issue in result.l1.issues]
    quarantine_dir = Path(result.final_dir)
    reason = load_json(quarantine_dir / "quarantine-reason.json")
    assert reason["contains_secrets"] is True
    assert stat.S_IMODE(quarantine_dir.stat().st_mode) == 0o700
    assert not (root / "datasets" / "cbx-search-trends" / "data" / "raw" / RUN_ID_5Y).exists()


# ---------------------------------------------------------------------------
# L2 on adopted runs (validity != comparability, P5)
# ---------------------------------------------------------------------------


def test_l2_separates_validity_from_comparability(tmp_path, registries):
    root = make_workspace(tmp_path)
    plan_12m = make_plan()
    plan_5y = make_plan(
        timeframe="today 5-y",
        start="2021-10-10T00:00:00Z",
        window_id="2021-10-10_2026-10-12",
    )
    first = _collect(registries, root, fixture=FIXTURE_12M, plan=plan_12m, run_id=RUN_ID_12M)
    same = _staged_copy(Path(first.final_dir), root / ".staging", new_run_id=RUN_ID_5Y)
    rerun = _adopt(registries, root, same)  # same request, different run
    other = _collect(registries, root, fixture=FIXTURE_5Y, plan=plan_5y, run_id="20261013T000002Z-google-trends-e2e-5y")
    assert first.adopted and rerun.adopted and other.adopted

    doc_first = load_json(Path(first.final_dir) / "run_metadata.json")
    doc_rerun = load_json(Path(rerun.final_dir) / "run_metadata.json")
    doc_other = load_json(Path(other.final_dir) / "run_metadata.json")

    same_window = compare_runs(doc_first, doc_rerun)
    assert same_window.status == "conditional"
    assert "coverage_and_sampling_review_required" in same_window.reasons

    different_window = compare_runs(doc_first, doc_other)
    assert different_window.status == "not_comparable"
    assert "c2_window_mismatch" in different_window.reasons
    # Both runs are L1-valid, yet not directly comparable: validity and
    # comparability are reported separately (P5).
    for document in (doc_first, doc_other):
        assert validate_full(
            document,
            schema_id="collection-run-v1",
            registries=registries,
        ).valid is True

    other_query = json.loads(json.dumps(doc_first))
    other_query["query_provenance"]["submitted_query"] = "THC リキッド"
    query_mismatch = compare_runs(doc_first, other_query)
    assert query_mismatch.status == "not_comparable"
    assert "c1_query_mismatch" in query_mismatch.reasons


def test_compare_runs_across_sources_is_not_comparable():
    base = {
        "source_id": "google-trends",
        "query_provenance": {"query_id": "q", "submitted_query": "CBX", "compound_id": "CBX"},
        "temporal_provenance": {
            "start": "2025-10-12T00:00:00Z",
            "end_exclusive": "2026-10-12T00:00:00Z",
            "granularity": "week",
            "timezone": "Asia/Tokyo",
        },
        "collector": {"collector_id": "google-trends-mcp"},
    }
    other = json.loads(json.dumps(base))
    other["source_id"] = "x"
    result = compare_runs(base, other)
    assert result.status == "not_comparable"
    assert "c3_source_mismatch" in result.reasons


# ---------------------------------------------------------------------------
# Raw immutability of the existing repository data
# ---------------------------------------------------------------------------


def test_existing_repo_raw_is_untouched_by_a_pipeline_run(tmp_path, registries):
    if not RECORDED_CBD_5Y.is_file():
        return
    metadata_path = RECORDED_CBD_5Y.parent / "run_metadata.json"
    before = (sha256_file(RECORDED_CBD_5Y), sha256_file(metadata_path))

    root = make_workspace(tmp_path)
    _collect(registries, root, fixture=FIXTURE_12M, plan=make_plan(), run_id=RUN_ID_12M)

    after = (sha256_file(RECORDED_CBD_5Y), sha256_file(metadata_path))
    assert after == before
