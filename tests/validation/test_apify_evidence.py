"""Contract tests for the Apify cloud evidence request list (PRV-013).

The committed request list must stay an honest offline derivation of the
adopted YouTube declaration: exactly its 6 runs, no invented values, and
collector capabilities untouched (still ``unknown`` / ``unverified``).
"""

import json
from argparse import Namespace
from copy import deepcopy
from pathlib import Path

from validation.apify_evidence import (
    REQUIRED_FIELDS,
    audit_apify_evidence,
    validate_request_list,
)
from validation.cli import cmd_audit_apify_evidence

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUESTS_PATH = REPO_ROOT / "metadata" / "provenance" / "apify-cloud-evidence-requests.json"
DECLARATION_PATH = (
    REPO_ROOT
    / "metadata"
    / "provenance"
    / "declarations"
    / "20261015-youtube-csv-adoption.json"
)
COLLECTORS_PATH = REPO_ROOT / "config" / "collectors.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_committed_request_list_matches_the_declaration():
    requests_document = _load(REQUESTS_PATH)
    declaration = _load(DECLARATION_PATH)
    assert validate_request_list(requests_document, declaration) == []
    assert len(requests_document["requests"]) == 6
    assert requests_document["collector_id"] == "youtube-apify-scraper"


def test_missing_fields_stay_null_until_retrieved():
    requests_document = _load(REQUESTS_PATH)
    for request in requests_document["requests"]:
        by_name = {item["field"]: item for item in request["fields"]}
        for field in ("actor_input", "evidence_source"):
            assert by_name[field]["status"] == "missing", (request["run_id"], field)
            assert by_name[field]["value"] is None, (request["run_id"], field)
        for field in REQUIRED_FIELDS:
            assert by_name[field]["required"] is True


def test_no_value_exists_outside_the_declaration():
    requests_document = _load(REQUESTS_PATH)
    declaration = _load(DECLARATION_PATH)
    declared_runs = {run["run_id"]: run for run in declaration["runs"]}
    assert {request["run_id"] for request in requests_document["requests"]} == set(
        declared_runs
    )
    for request in requests_document["requests"]:
        run = declared_runs[request["run_id"]]
        by_name = {item["field"]: item for item in request["fields"]}
        assert by_name["actor_run_id"]["value"] == run["environment"]["actor_run_id"]
        assert by_name["apify_dataset_id"]["value"] == run["environment"]["apify_dataset_id"]
        assert by_name["started_at"]["value"] == run["timestamps"]["started_at"]
        assert by_name["finished_at"]["value"] == run["timestamps"]["finished_at"]
        assert by_name["status"]["value"] == run["execution"]["status"]


def test_collector_capabilities_are_not_promoted():
    collectors = _load(COLLECTORS_PATH)["collectors"]
    apify = {
        collector["collector_id"]: collector
        for collector in collectors
        if collector.get("provider") == "apify"
    }
    assert "youtube-apify-scraper" in apify
    entry = apify["youtube-apify-scraper"]
    assert entry["status"] == "unverified"
    assert entry["version"] == "unknown"
    assert set(entry["capabilities"].values()) == {"unknown"}


def test_invented_run_id_is_refused():
    requests_document = _load(REQUESTS_PATH)
    declaration = _load(DECLARATION_PATH)
    forged = deepcopy(requests_document)
    forged["requests"][0]["run_id"] = "20990101T000000Z-youtube-invented"
    assert validate_request_list(forged, declaration) != []


def test_omitted_run_is_refused():
    requests_document = _load(REQUESTS_PATH)
    declaration = _load(DECLARATION_PATH)
    dropped = deepcopy(requests_document)
    dropped["requests"].pop()
    violations = validate_request_list(dropped, declaration)
    assert any("omits declaration runs" in violation for violation in violations)


def test_filled_missing_value_is_refused():
    requests_document = _load(REQUESTS_PATH)
    declaration = _load(DECLARATION_PATH)
    filled = deepcopy(requests_document)
    first = filled["requests"][0]
    for item in first["fields"]:
        if item["field"] == "actor_input":
            item["value"] = {"search": "guessed"}
    violations = validate_request_list(filled, declaration)
    assert any("must be null while status is 'missing'" in v for v in violations)


def test_transcription_mismatch_is_refused():
    requests_document = _load(REQUESTS_PATH)
    declaration = _load(DECLARATION_PATH)
    altered = deepcopy(requests_document)
    altered["requests"][0]["fields"][0]["value"] = "INVENTEDRUNID00000"
    violations = validate_request_list(altered, declaration)
    assert any("does not match the declaration" in v for v in violations)


def test_audit_report_reproduces_the_blocked_checklist():
    requests_document = _load(REQUESTS_PATH)
    declaration = _load(DECLARATION_PATH)
    report = audit_apify_evidence(requests_document, declaration)
    assert report["violations"] == []
    assert report["issue"] == "ISS-20261015-PRV-013"
    assert report["collector_id"] == "youtube-apify-scraper"
    assert report["run_count"] == 6
    # 6 runs x 5 transcribed fields still awaiting cloud corroboration.
    assert report["pending_count"] == 30
    # 6 runs x (actor_input + evidence_source): no value anywhere yet.
    assert report["missing_count"] == 12
    assert report["observed_count"] == 0
    assert report["cloud_evidence_obtained"] is False
    assert report["collector_promotion_allowed"] is False
    assert len(report["blocked"]) == 6
    for entry in report["blocked"]:
        assert entry["pending"] == [
            "actor_run_id",
            "apify_dataset_id",
            "finished_at",
            "started_at",
            "status",
        ], entry["run_id"]
        assert entry["missing"] == ["actor_input", "evidence_source"], entry[
            "run_id"
        ]
        assert entry["observed"] == [], entry["run_id"]


def test_audit_flags_a_dishonest_list_without_allowing_promotion():
    requests_document = _load(REQUESTS_PATH)
    declaration = _load(DECLARATION_PATH)
    forged = deepcopy(requests_document)
    forged["requests"][0]["fields"][0]["value"] = "INVENTEDRUNID00000"
    report = audit_apify_evidence(forged, declaration)
    assert report["violations"] != []
    assert report["cloud_evidence_obtained"] is False
    assert report["collector_promotion_allowed"] is False


def test_observed_actor_input_is_refused_without_a_declaration_source():
    # actor_input has no declaration counterpart, so the request list can
    # never self-declare it as corroborated: real cloud evidence must be
    # registered through the evidence registry by the owner instead.
    requests_document = _load(REQUESTS_PATH)
    declaration = _load(DECLARATION_PATH)
    claimed = deepcopy(requests_document)
    first = claimed["requests"][0]
    for item in first["fields"]:
        if item["field"] == "actor_input":
            item["status"] = "observed"
            item["value"] = {"search": "guessed"}
    report = audit_apify_evidence(claimed, declaration)
    assert report["violations"] != []
    assert report["collector_promotion_allowed"] is False


def test_cli_reports_the_committed_blocked_state_as_honest(capsys):
    args = Namespace(
        requests=str(REQUESTS_PATH),
        declaration=str(DECLARATION_PATH),
        output=None,
        format="text",
    )
    assert cmd_audit_apify_evidence(args) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 6
    assert all("missing=actor_input,evidence_source" in line for line in lines)
