"""P3-11: no schema may be registered without a Contract Test.

h.md §9: "新しいスキーマを登録した場合、対応するContract Testを必須とする".
This test makes the rule mechanical: every registry entry must be listed in
EXPECTED_COVERAGE with an existing test file that references the schema ID.
Adding a schema without a contract test therefore fails the suite.
"""

from pathlib import Path

from validation.schema_registry import SCHEMA_REGISTRY

TESTS_DIR = Path(__file__).parent

#: schema ID -> test module expected to exercise it (grep-checked below).
EXPECTED_COVERAGE = {
    "collection-run-v1": "test_collection_run.py",
    "collection-run-v1-running": "test_running_profile.py",
    "source-registry-v1": "test_registries_g1.py",
    "collector-registry-v1": "test_registries_g1.py",
    "query-registry-v1": "test_query_registry.py",
    "query-variants-v1": "test_query_registry.py",
    "temporal-window-v1": "test_temporal_window.py",
    "artifact-manifest-v1": "test_artifact_manifest.py",
    "transformation-v1": "test_transformation.py",
    "storage-policy-registry-v1": "test_storage_policy_schemas.py",
    "publication-decision-v1": "test_storage_policy_schemas.py",
    "study-registry-v1": "test_study_registry.py",
    "measurement-registry-v1": "test_study_registry.py",
    "research-view-v1": "test_study_registry.py",
    "collection-plan-v1": "test_collection_plan.py",
}


def test_coverage_map_matches_the_registry_exactly():
    assert set(EXPECTED_COVERAGE) == set(SCHEMA_REGISTRY)


def test_every_schema_has_a_referencing_test_file():
    for schema_id, filename in EXPECTED_COVERAGE.items():
        path = TESTS_DIR / filename
        assert path.is_file(), f"missing test module for {schema_id}: {filename}"
        content = path.read_text(encoding="utf-8")
        assert schema_id in content, (
            f"test module {filename} never references schema ID {schema_id}"
        )


def test_registered_schemas_are_nonempty_and_structured():
    for schema_id, schema in SCHEMA_REGISTRY.items():
        assert isinstance(schema, dict) and schema, schema_id
        # Documents that carry a schema_version declare it as required; other
        # document types (windows, transformation records, decisions,
        # research views) have no version field in their contracts.
        if "schema_version" in schema:
            assert schema["schema_version"].get("required") is True, schema_id
