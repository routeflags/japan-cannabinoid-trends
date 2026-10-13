"""G7 dedup + publication-boundary tests (G7-T15/T16/T17, P7).

Contract sources: g.md \u00a712 (dedup), \u00a715 (internal/public), \u00a717.
"""

import json
from pathlib import Path

from research.catalog import build_catalog
from research.dedup import UseIndex, build_repeat_index, observation_key
from research.policy import PUBLIC_FIELDS, split_public_internal

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "datasets"


def test_g7_t15_repeat_relation_recorded_without_merging():
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    report = build_repeat_index(catalog)
    assert report["relation_count"] >= 1
    phase_a = [r for r in report["relations"] if "repeated_collection" in r["relation"]]
    witnessed = [
        r for r in phase_a
        if "20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m" in r["run_ids"]
        and "20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m" in r["run_ids"]
    ]
    assert witnessed, "phase-a / repeat re-fetch relation must be recorded"
    assert witnessed[0]["rule"], "dedup rule must be recorded"


def test_g7_t16_raw_is_never_modified_by_indexing():
    before = {
        str(p): p.read_bytes()
        for p in sorted(DATASETS.rglob("run_metadata.json"))
    }
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    build_repeat_index(catalog)
    split_public_internal(catalog)
    after = {str(p): p.read_bytes() for p in sorted(DATASETS.rglob("run_metadata.json"))}
    assert before == after


def test_observation_keys_separate_record_from_event():
    assert observation_key("google-trends", "CBD リキッド", "2025-10-12") != observation_key(
        "google-trends", "CBD リキッド", "2025-10-19"
    )
    index = UseIndex()
    key = observation_key("google-trends", "CBD リキッド", "2025-10-12")
    index.add(key, artifact_ref="run-a", relation="observed", rule="r")
    index.add(key, artifact_ref="run-b", relation="observed", rule="r")
    uses = index.to_dict()["uses"][key]
    assert {u["artifact_ref"] for u in uses} == {"run-a", "run-b"}
    assert all(u["co_used_by"] for u in uses)


def test_g7_t17_public_catalog_excludes_non_public_and_paths():
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    split = split_public_internal(catalog)
    assert split["public_count"] == 0, "nothing is approved, so nothing is public"
    assert split["internal_count"] == catalog["entry_count"]

    approved = next(iter(catalog["entries"]))["catalog_entry_id"]
    target = next(iter(catalog["entries"]))
    target = dict(target, availability="approved")
    gated = dict(catalog, entries=[target])
    split = split_public_internal(gated, approved_ids={approved})
    assert split["public_count"] == 1
    public_entry = split["public"][0]
    assert set(public_entry) <= set(PUBLIC_FIELDS)
    assert "run_dir" not in public_entry
    dumped = json.dumps(split["public"], ensure_ascii=False)
    assert "run_dir" not in dumped
    assert "token" not in dumped.lower()
    assert "secret" not in dumped.lower()
