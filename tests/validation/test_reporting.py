"""Validation Report / Issue normalization tests (CV-17, h.md §14).

The report shape is a stable interface: golden assertions pin the exact
fields, ordering and message templates, and secret-bearing values never
appear in messages.
"""

from validation.reporting import (
    Issue,
    Report,
    ReportBundle,
    VALIDATION_VERSION,
    dump_json,
    normalize_cerberus_errors,
)


def _broken_errors() -> dict:
    return {
        "execution": [
            {
                "returned_count": ["must be of integer type"],
            }
        ],
        "run_id": ["required field"],
        "unexpected": ["unknown field"],
        "status": ["unallowed value super-secret-token"],
    }


def test_normalize_maps_codes_paths_and_rules():
    issues = normalize_cerberus_errors(_broken_errors(), schema_version="1.0.0")
    assert [(issue.code, issue.path, issue.rule) for issue in issues] == [
        ("TYPE_MISMATCH", "/execution/returned_count", "type"),
        ("REQUIRED_FIELD_MISSING", "/run_id", "required"),
        ("UNALLOWED_VALUE", "/status", "allowed"),
        ("UNKNOWN_FIELD", "/unexpected", "unknown_field"),
    ]
    assert all(issue.schema_version == "1.0.0" for issue in issues)
    assert all(issue.severity == "error" for issue in issues)


def test_messages_never_contain_offending_values():
    """h.md §14: no values in messages; the interpelled value from Cerberus's
    "unallowed value X" must be replaced by a fixed template."""
    issues = normalize_cerberus_errors(_broken_errors(), schema_version="1.0.0")
    blob = dump_json({"issues": [issue.to_dict() for issue in issues]})
    assert "super-secret-token" not in blob
    assert "value is not one of the allowed values" in blob


def test_normalize_is_deterministic_and_sorted():
    first = normalize_cerberus_errors(_broken_errors(), schema_version="1.0.0")
    second = normalize_cerberus_errors(_broken_errors(), schema_version="1.0.0")
    assert first == second
    paths = [issue.path for issue in first]
    assert paths == sorted(paths)


def test_pointer_escaping_for_special_keys():
    errors = {"weird/key~name": ["unknown field"]}
    issues = normalize_cerberus_errors(errors)
    assert issues[0].path == "/weird~1key~0name"


def test_report_golden_shape():
    report = Report(
        schema_id="collection-run-v1",
        target="datasets/x/run_metadata.json",
        valid=False,
        issues=[
            Issue(
                code="REQUIRED_FIELD_MISSING",
                path="/run_id",
                severity="error",
                message="required field is missing",
                rule="required",
                schema_version="1.0.0",
            )
        ],
    )
    assert report.to_dict() == {
        "validation_version": VALIDATION_VERSION,
        "schema_id": "collection-run-v1",
        "target": "datasets/x/run_metadata.json",
        "profile": "strict",
        "valid": False,
        "issues": [
            {
                "code": "REQUIRED_FIELD_MISSING",
                "path": "/run_id",
                "severity": "error",
                "message": "required field is missing",
                "rule": "required",
                "schema_version": "1.0.0",
            }
        ],
    }


def test_legacy_report_merges_audit_fields():
    report = Report(
        schema_id="collection-run-v1",
        target="datasets/x/run_metadata.json",
        valid=True,
        issues=[],
        profile="legacy_audit",
        legacy={
            "run_id": "legacy-run-001",
            "status": "incomplete",
            "missing_fields": ["collection_started_at", "query_provenance"],
            "sha256": "f" * 64,
        },
    )
    data = report.to_dict()
    assert data["profile"] == "legacy_audit"
    assert data["run_id"] == "legacy-run-001"
    assert data["status"] == "incomplete"
    assert data["missing_fields"] == [
        "collection_started_at",
        "query_provenance",
    ]
    assert data["valid"] is True


def test_bundle_validity_is_the_conjunction():
    ok = Report(schema_id="s", target="a", valid=True)
    bad = Report(schema_id="s", target="b", valid=False)
    assert ReportBundle(reports=[ok]).valid is True
    assert ReportBundle(reports=[ok, bad]).valid is False


def test_dump_json_is_stable_and_utf8():
    document = {"b": 1, "a": "日本語"}
    assert dump_json(document) == dump_json(dict(document))
    assert "日本語" in dump_json(document)
    assert dump_json(document).endswith("\n")
