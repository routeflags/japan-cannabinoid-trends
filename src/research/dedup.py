"""G7 \u00a712 deduplication tracking (non-destructive).

Contract source: ``docs/plans/20261013g.md`` \u00a712.

Principles enforced here:

- Raw duplicate records are never deleted; deduplication happens on derived
  data and the rule is recorded.
- Record identity and observation-event identity are separated (\u00a712.2):
  the same native record observed at different snapshot times is two
  observation events, not one record.
- Lineage to the source artifact is kept on every use entry.
- Relations that do not exist are never created: ``build_repeat_index`` only
  records repeat relations witnessed by shared (term, type, timeframe) fetch
  groups in the catalog.
"""

from __future__ import annotations

__all__ = [
    "DEDUP_VERSION",
    "UseIndex",
    "observation_key",
    "build_repeat_index",
]

DEDUP_VERSION = "1.0.0"


def observation_key(source_id: str, term: str, period: str) -> str:
    """Observation-event key (\u00a712.2: ``source_id + native_record_id`` style).

    For Google Trends weekly buckets the native identity is the fetched term
    and the bucket period; the observing run is recorded separately on the
    use entry so re-fetches stay distinguishable.
    """
    return f"{source_id}:{term}:{period}"


class UseIndex:
    """Derived-data use registry: key -> consuming artifacts (read-only on raw)."""

    def __init__(self) -> None:
        self._uses: dict[str, list[dict]] = {}

    def add(self, key: str, *, artifact_ref: str, relation: str, rule: str) -> None:
        entry = {"artifact_ref": artifact_ref, "relation": relation, "rule": rule}
        bucket = self._uses.setdefault(key, [])
        if entry not in bucket:
            bucket.append(entry)
        for other in bucket:
            other.setdefault("co_used_by", [])
        for other in bucket:
            others = sorted({u["artifact_ref"] for u in bucket} - {other["artifact_ref"]})
            other["co_used_by"] = others

    def to_dict(self) -> dict:
        return {
            "dedup_version": DEDUP_VERSION,
            "key_count": len(self._uses),
            "uses": {key: sorted(v, key=lambda u: u["artifact_ref"]) for key, v in sorted(self._uses.items())},
        }


def build_repeat_index(catalog: dict) -> dict:
    """Record witnessed repeat-collection relations (no merging, no deletion).

    Two catalog entries form a repeat relation only when they share the same
    ``study_id``, ``source_id``, ``timeframe`` and an identical fetch group
    (same terms, same query type) with different ``run_id`` values -- i.e.
    the same observation was fetched twice.  Anything else is not recorded.
    """
    entries = catalog.get("entries")
    if not isinstance(entries, list):
        entries = []
    groups: dict[tuple, list[dict]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for group in entry.get("terms") or []:
            if not isinstance(group, dict):
                continue
            key = (
                str(entry.get("study_id")),
                str(entry.get("source_id")),
                str(group.get("timeframe")),
                str(group.get("type")),
                tuple(sorted(group.get("terms") or [])),
            )
            groups.setdefault(key, []).append(entry)
    index = UseIndex()
    relations: list[dict] = []
    for key, bucket in sorted(groups.items()):
        run_ids = sorted({str(e.get("run_id")) for e in bucket})
        if len(run_ids) < 2:
            continue
        study, source, timeframe, kind, terms = key
        relations.append(
            {
                "relation": "repeated_collection",
                "study_id": study,
                "source_id": source,
                "timeframe": timeframe,
                "query_type": kind,
                "terms": list(terms),
                "run_ids": run_ids,
                "rule": "same fetch group re-collected under a new run_id; raw kept on both sides",
            }
        )
        for run_id in run_ids:
            index.add(
                f"{source}:{timeframe}:{kind}:{','.join(terms)}",
                artifact_ref=run_id,
                relation="repeated_collection",
                rule="shared fetch group",
            )
    return {
        "dedup_version": DEDUP_VERSION,
        "relation_count": len(relations),
        "relations": relations,
        "use_index": index.to_dict(),
    }
