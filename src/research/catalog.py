"""G7 \u00a75 federated research catalog (discovery index).

Contract source: ``docs/plans/20261013g.md`` \u00a75 (entry shape) and
\u00a714 (catalog is a regenerable index; registries stay the source of
truth).

What this module does
---------------------
- Walk ``datasets/**/run_metadata.json`` (read-only) and build one catalog
  entry per run (legacy runs) or per artifact (new-format runs carrying an
  ``artifact-manifest.json`` + ``query_provenance`` / ``temporal_provenance``).
- Link legacy free-text query terms to the G2 query registry by **exact
  string match only** (``canonical_text`` / variants).  The linkage rule is
  recorded on every entry (``compound_link_rule``); non-matching terms link
  to nothing (no guessing, AGENTS.md).
- Declare the native measurement per source (P5 semantics, \u00a77) without
  converting values (P6).
- Legacy runs carry no ``window_id`` / granularity / sampling / coverage
  evidence, so those fields stay ``None`` / ``unknown`` instead of being
  inferred.

Every search result is discovery-only (P4): retrievability does not imply
statistical comparability.  Comparability is judged separately by
``research.comparability``.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "RESEARCH_CATALOG_VERSION",
    "SOURCE_MEASUREMENTS",
    "DISCOVERY_NOTE",
    "DERIVATION_RULES",
    "build_catalog",
    "find_artifacts",
    "get_provenance",
]

RESEARCH_CATALOG_VERSION = "1.0.0"

#: Source-native measurement declaration (P5).  This maps a source to the
#: measurement it natively produces; it never converts values (P6).
#: ``google-search-console`` has no G7 measurement registered, so it maps to
#: ``None`` (recorded, not guessed).
SOURCE_MEASUREMENTS: dict[str, tuple[str, str] | None] = {
    "google-trends": ("search_interest_index", "relative_index_0_100"),
    "x": ("social_post_count", "posts"),
    "instagram": ("social_post_count", "posts"),
    "youtube": ("video_publication_count", "videos"),
    "tiktok": ("video_publication_count", "videos"),
    "google-search-console": None,
}

#: Attached to every discovery response (P4: Discovery != Comparability).
DISCOVERY_NOTE = (
    "discovery_only: retrievability does not imply statistical "
    "comparability (G7 P4). Run research.comparability before comparing values."
)

#: Derivation rules recorded on the catalog itself (methodological
#: transparency, AGENTS.md reproducibility rule).
DERIVATION_RULES = {
    "compound_link_rule": (
        "term_exact_match: a legacy query term links to a compound only when "
        "it exactly equals a query-registry canonical_text or variant text; "
        "otherwise compound_ids is empty (no inference)"
    ),
    "measurement_rule": (
        "source_native: measurement_id/unit follow SOURCE_MEASUREMENTS; "
        "unmapped sources record null (no forced normalization, P6)"
    ),
    "period_rule": (
        "observed_only: entry keeps the run's timeframe/geo strings verbatim "
        "and matches period filters on collection_timestamp only; absolute "
        "windows are never derived from relative timeframes"
    ),
    "availability_rule": (
        "default_private: legacy runs without publication approval record "
        "availability=private (G6 publication gate: unreviewed stays non-public)"
    ),
    "quality_rule": (
        "unknown_without_gate: legacy runs without L1 gate evidence record "
        "quality_status=unknown (never inferred)"
    ),
}


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _term_index(query_registry, variants_registry) -> dict[str, tuple[str, str, str]]:
    """Map exact term text -> (query_id, compound_id, intent_id)."""
    index: dict[str, tuple[str, str, str]] = {}
    queries = []
    if isinstance(query_registry, dict):
        queries = query_registry.get("queries") or []
    if not isinstance(queries, list):
        queries = []
    for item in queries:
        if not isinstance(item, dict):
            continue
        query_id = item.get("query_id")
        text = item.get("canonical_text")
        if isinstance(query_id, str) and isinstance(text, str) and text not in index:
            index[text] = (
                query_id,
                item.get("compound_id"),
                item.get("intent_id"),
            )
    variant_sets = []
    if isinstance(variants_registry, dict):
        variant_sets = variants_registry.get("variant_sets") or []
    if not isinstance(variant_sets, list):
        variant_sets = []
    query_lookup = {
        item.get("query_id"): item
        for item in queries
        if isinstance(item, dict) and isinstance(item.get("query_id"), str)
    }
    for bundle in variant_sets:
        if not isinstance(bundle, dict):
            continue
        query_id = bundle.get("query_id")
        base = query_lookup.get(query_id)
        variants = bundle.get("variants")
        if base is None or not isinstance(variants, list):
            continue
        for variant in variants:
            if not isinstance(variant, dict):
                continue
            text = variant.get("text")
            if isinstance(text, str) and text not in index:
                index[text] = (
                    query_id,
                    base.get("compound_id"),
                    base.get("intent_id"),
                )
    return index


def _default_registries(repo_root: Path):
    metadata = Path(repo_root) / "metadata"
    return (
        _load_json(metadata / "queries" / "query-registry.json"),
        _load_json(metadata / "queries" / "query-variants.json"),
    )


def _legacy_terms(run: dict) -> list[dict]:
    queries = run.get("queries")
    if not isinstance(queries, list):
        return []
    terms: list[dict] = []
    for item in queries:
        if not isinstance(item, dict):
            continue
        record = {}
        if isinstance(item.get("term"), str):
            record["terms"] = [item["term"]]
        elif isinstance(item.get("terms"), list):
            record["terms"] = [t for t in item["terms"] if isinstance(t, str)]
        else:
            continue
        for key in ("geo", "timeframe", "type", "label"):
            if isinstance(item.get(key), str):
                record[key] = item[key]
        terms.append(record)
    return terms


def _link_compounds(terms: list[dict], index: dict) -> tuple[list[str], list[str], list[str], str]:
    compounds: list[str] = []
    query_ids: list[str] = []
    intents: list[str] = []
    matched = False
    for group in terms:
        for term in group.get("terms", []):
            hit = index.get(term)
            if hit is None:
                continue
            matched = True
            query_id, compound_id, intent_id = hit
            if isinstance(compound_id, str) and compound_id not in compounds:
                compounds.append(compound_id)
            if query_id not in query_ids:
                query_ids.append(query_id)
            if isinstance(intent_id, str) and intent_id not in intents:
                intents.append(intent_id)
    rule = "term_exact_match" if matched else "no_match"
    return sorted(compounds), sorted(query_ids), sorted(intents), rule


def _new_format_entry(run: dict, manifest: dict, artifact: dict, run_dir: Path, root: Path) -> dict:
    """Entry for a new-format run (G1/G5 contract fields present)."""
    query = run.get("query_provenance")
    query = query if isinstance(query, dict) else {}
    temporal = run.get("temporal_provenance")
    temporal = temporal if isinstance(temporal, dict) else {}
    source_id = run.get("source_id")
    measurement = SOURCE_MEASUREMENTS.get(source_id) if isinstance(source_id, str) else None
    compound_id = query.get("compound_id")
    return {
        "catalog_entry_id": f"{run.get('study_id')}:{run.get('run_id')}:{artifact.get('artifact_id')}",
        "study_id": run.get("study_id"),
        "run_id": run.get("run_id"),
        "artifact_id": artifact.get("artifact_id"),
        "source_id": source_id,
        "compound_ids": [compound_id] if isinstance(compound_id, str) else [],
        "query_ids": [query["query_id"]] if isinstance(query.get("query_id"), str) else [],
        "intent_ids": [query["intent_id"]] if isinstance(query.get("intent_id"), str) else [],
        "window_id": temporal.get("window_id"),
        "terms": [],
        "timeframe": None,
        "geo": None,
        "measurement_id": measurement[0] if measurement else None,
        "unit": measurement[1] if measurement else None,
        "granularity": temporal.get("granularity"),
        "collection_timestamp": run.get("collection_started_at"),
        "compound_link_rule": "direct_provenance",
        "availability": "private",
        "quality_status": "unknown",
        "run_dir": _display(run_dir, root),
    }


def _display(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _legacy_entry(run: dict, run_dir: Path, root: Path, index: dict) -> dict:
    terms = _legacy_terms(run)
    compounds, query_ids, intents, rule = _link_compounds(terms, index)
    source = run.get("source")
    measurement = SOURCE_MEASUREMENTS.get(source) if isinstance(source, str) else None
    timeframes = sorted({g["timeframe"] for g in terms if "timeframe" in g})
    geos = sorted({g["geo"] for g in terms if "geo" in g})
    return {
        "catalog_entry_id": f"{run.get('study_id')}:{run.get('run_id')}",
        "study_id": run.get("study_id"),
        "run_id": run.get("run_id"),
        "artifact_id": None,
        "source_id": source,
        "compound_ids": compounds,
        "query_ids": query_ids,
        "intent_ids": intents,
        "window_id": None,
        "terms": terms,
        "timeframe": timeframes[0] if len(timeframes) == 1 else (timeframes or None),
        "geo": geos[0] if len(geos) == 1 else (geos or None),
        "measurement_id": measurement[0] if measurement else None,
        "unit": measurement[1] if measurement else None,
        "granularity": None,
        "collection_timestamp": run.get("collection_timestamp"),
        "compound_link_rule": rule,
        "availability": "private",
        "quality_status": "unknown",
        "run_dir": _display(run_dir, root),
    }


def build_catalog(datasets_root, *, repo_root=None, query_registry=None, query_variants=None) -> dict:
    """Build the federated discovery index (read-only, deterministic).

    ``datasets_root`` is walked for ``run_metadata.json`` files.  Registry
    documents may be injected (tests) or loaded from ``<repo_root>/metadata``
    (default: parents of ``datasets_root``).  The result carries no
    timestamps and entries sort by ``(study_id, run_id, artifact_id)`` so
    identical inputs always produce byte-identical output (G7-T06).
    """
    datasets = Path(datasets_root)
    root = Path(repo_root) if repo_root is not None else datasets.parent
    if query_registry is None or query_variants is None:
        loaded_registry, loaded_variants = _default_registries(root)
        if query_registry is None:
            query_registry = loaded_registry
        if query_variants is None:
            query_variants = loaded_variants
    index = _term_index(query_registry, query_variants)

    entries: list[dict] = []
    errors: list[dict] = []
    files = sorted(datasets.rglob("run_metadata.json")) if datasets.is_dir() else []
    for path in files:
        run = _load_json(path)
        if not isinstance(run, dict):
            errors.append({"path": _display(path, root), "reason": "run_metadata_unreadable"})
            continue
        run_dir = path.parent
        manifest = _load_json(run_dir / "artifact-manifest.json")
        if (
            isinstance(manifest, dict)
            and isinstance(manifest.get("artifacts"), list)
            and isinstance(run.get("query_provenance"), dict)
        ):
            for artifact in manifest["artifacts"]:
                if not isinstance(artifact, dict):
                    continue
                entries.append(_new_format_entry(run, manifest, artifact, run_dir, root))
        else:
            entries.append(_legacy_entry(run, run_dir, root, index))
    entries.sort(
        key=lambda e: (
            str(e.get("study_id")),
            str(e.get("run_id")),
            str(e.get("artifact_id")),
        )
    )
    return {
        "catalog_version": RESEARCH_CATALOG_VERSION,
        "entry_count": len(entries),
        "derivation_rules": dict(DERIVATION_RULES),
        "entries": entries,
        "errors": errors,
        "discovery_note": DISCOVERY_NOTE,
    }


def find_artifacts(
    catalog: dict,
    *,
    compound_id: str | None = None,
    source_id: str | None = None,
    study_id: str | None = None,
    measurement_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    """Cross-study discovery filter (P4: finding is not comparing).

    ``start`` / ``end`` are ISO-8601 bounds matched against the observed
    ``collection_timestamp`` only (period_rule).  Returns matching entries
    plus the discovery note; an empty result is a valid outcome (no
    fabrication of absent runs).
    """
    entries = catalog.get("entries")
    if not isinstance(entries, list):
        entries = []
    matched: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if compound_id is not None and compound_id not in (entry.get("compound_ids") or []):
            continue
        if source_id is not None and entry.get("source_id") != source_id:
            continue
        if study_id is not None and entry.get("study_id") != study_id:
            continue
        if measurement_id is not None and entry.get("measurement_id") != measurement_id:
            continue
        stamp = entry.get("collection_timestamp")
        if start is not None and (not isinstance(stamp, str) or stamp < start):
            continue
        if end is not None and (not isinstance(stamp, str) or stamp > end):
            continue
        matched.append(entry)
    return {
        "match_count": len(matched),
        "entries": matched,
        "discovery_note": DISCOVERY_NOTE,
    }


def get_provenance(run_id: str, datasets_root) -> dict | None:
    """Locate a run's provenance bundle by ``run_id`` (read-only lookup)."""
    datasets = Path(datasets_root)
    root = datasets.parent
    if not datasets.is_dir():
        return None
    for path in sorted(datasets.rglob("run_metadata.json")):
        run = _load_json(path)
        if isinstance(run, dict) and run.get("run_id") == run_id:
            manifest = _load_json(path.parent / "artifact-manifest.json")
            siblings = sorted(p.name for p in path.parent.iterdir())
            return {
                "run_id": run_id,
                "study_id": run.get("study_id"),
                "run_metadata_path": _display(path, root),
                "run_metadata": run,
                "artifact_manifest": manifest,
                "sibling_files": siblings,
            }
    return None
