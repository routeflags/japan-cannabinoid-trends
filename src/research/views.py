"""G7 \u00a710 research views (reproducible derived views, P8).

Contract source: ``docs/plans/20261013g.md`` \u00a710 (definition, outputs)
and \u00a711 (long format + per-row lineage identifiers).

Rules enforced here:

- Only ``parallel_timeseries`` is accepted: distinct measurements are placed
  side by side on a shared time axis and never summed (G2 ``research-view-v1``
  aggregation ban).  Any other ``comparison_mode`` is rejected.
- Values come only from observed artifact files (read-only).  No synthetic
  values are ever written.
- Google Trends ``0`` conflates true zero with below-threshold weeks; rows
  record ``observed_zero`` with that ambiguity noted in ``provenance.json``
  (explicit uncertainty, AGENTS.md).
- Every row carries lineage identifiers back to the source artifact, query
  group and normalization scale (\u00a711).
- When ``require_comparability_gate`` is true, every series pair is judged
  by ``research.comparability`` and the report is stored alongside the
  dataset; a ``not_comparable`` pair blocks *comparison*, never the
  parallel display itself.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from research.comparability import check_cross_study_comparability
from validation.core import validate_document
from validation.schema_registry import get_schema

__all__ = [
    "VIEW_BUILDER_VERSION",
    "GT_ZERO_NOTE",
    "validate_view_definition",
    "extract_gt_series",
    "build_view",
]

VIEW_BUILDER_VERSION = "1.0.0"

GT_ZERO_NOTE = (
    "google_trends_zero_ambiguity: a value of 0 conflates true zero with "
    "below-threshold weeks; recorded as observed_zero, not as proven absence"
)

_CSV_COLUMNS = [
    "study_id",
    "source_id",
    "compound_id",
    "query_id",
    "period",
    "period_start",
    "period_end",
    "measurement_id",
    "value",
    "unit",
    "normalization_scale",
    "time_axis",
    "granularity",
    "run_id",
    "artifact_ref",
    "status",
]


def validate_view_definition(definition: dict) -> list:
    """Structural check of a view definition (returns issue list, empty = ok)."""
    schema = get_schema("research-view-v1")
    result = validate_document(definition, schema)
    if result.valid:
        return []
    return [f"{path}: {', '.join(msgs) if isinstance(msgs, list) else msgs}" for path, msgs in result.errors.items()]


def _split_period(raw: object) -> tuple[str, str, str]:
    if not isinstance(raw, str) or not raw:
        return "", "", ""
    if "/" in raw:
        start, end = raw.split("/", 1)
        return raw, start.strip(), end.strip()
    return raw, raw.strip(), raw.strip()


def extract_gt_series(artifact_path: Path, *, term: str) -> tuple[list[dict], dict]:
    """Extract weekly rows for ``term`` from a legacy GT artifact (read-only).

    Supports single-term shapes (``data: [{date, interest|value}]``) and
    comparison shapes (``data: [{date, <term>: value}]``).  Returns
    ``(rows, scale_info)`` where each row holds period/value facts only;
    semantic fields are attached by :func:`build_view`.
    """
    try:
        document = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"artifact unreadable: {artifact_path}: {error}") from error
    if not isinstance(document, dict) or not isinstance(document.get("data"), list):
        raise ValueError(f"artifact has no machine-readable data array: {artifact_path}")
    data = document["data"]
    terms = document.get("terms")
    if isinstance(terms, list) and terms:
        scale = f"comparison:{sorted(t for t in terms if isinstance(t, str))}"
        value_key = term
    else:
        label = document.get("query", document.get("keyword"))
        scale = f"single:{label}"
        value_key = None
    rows: list[dict] = []
    for point in data:
        if not isinstance(point, dict):
            continue
        if value_key is not None:
            value = point.get(value_key)
        else:
            value = point.get("interest", point.get("value"))
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        period, start, end = _split_period(point.get("date"))
        if not period:
            continue
        rows.append(
            {
                "period": period,
                "period_start": start,
                "period_end": end,
                "value": value,
                "status": "observed_nonzero" if value != 0 else "observed_zero",
            }
        )
    if not rows:
        raise ValueError(f"no usable points for term {term!r} in {artifact_path}")
    scale_info = {
        "normalization_scale": scale,
        "geo": document.get("geo"),
        "timeframe": document.get("timeframe"),
        "collected_at": document.get("collected_at"),
    }
    return rows, scale_info


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_view(definition: dict, series: list[dict], catalog: dict, *, repo_root, out_dir) -> dict:
    """Build a parallel-timeseries research view (derived output, P8).

    ``definition`` must satisfy ``research-view-v1`` with
    ``comparison_mode == "parallel_timeseries"``.  ``series`` selects
    artifacts::

        {"series_id", "run_id", "artifact_file", "term",
         "compound_id", "query_id", "time_axis", "granularity"}

    ``catalog`` supplies the entries gated pairwise.  Writes
    ``view-definition.json`` / ``dataset.csv`` / ``comparability-report.json``
    / ``provenance.json`` into ``out_dir`` and returns the summary.
    Raw inputs are only read.
    """
    issues = validate_view_definition(definition)
    if issues:
        raise ValueError(f"invalid view definition: {[str(i) for i in issues]}")
    if definition.get("comparison_mode") != "parallel_timeseries":
        raise ValueError(
            "only parallel_timeseries is supported: measurements must not be summed "
            "(G2 research-view-v1 aggregation ban)"
        )
    mode = definition.get("comparison_mode")
    root = Path(repo_root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    entries_by_run: dict[str, dict] = {}
    for entry in catalog.get("entries") or []:
        if isinstance(entry, dict) and isinstance(entry.get("run_id"), str):
            entries_by_run.setdefault(entry["run_id"], entry)

    rows: list[dict] = []
    lineage: list[dict] = []
    gated_pairs: list[dict] = []
    series_ids = [s.get("series_id") for s in series]
    for spec in series:
        artifact_path = root / spec["artifact_file"]
        points, scale = extract_gt_series(artifact_path, term=spec["term"])
        entry = entries_by_run.get(spec.get("run_id"))
        scale_id = f"{scale['normalization_scale']}@{spec.get('run_id')}"
        for point in points:
            rows.append(
                {
                    "study_id": (entry or {}).get("study_id"),
                    "source_id": "google-trends",
                    "compound_id": spec.get("compound_id"),
                    "query_id": spec.get("query_id"),
                    "period": point["period"],
                    "period_start": point["period_start"],
                    "period_end": point["period_end"],
                    "measurement_id": "search_interest_index",
                    "value": point["value"],
                    "unit": "relative_index_0_100",
                    "normalization_scale": scale_id,
                    "time_axis": spec.get("time_axis"),
                    "granularity": spec.get("granularity") or definition.get("granularity"),
                    "run_id": spec.get("run_id"),
                    "artifact_ref": spec["artifact_file"],
                    "status": point["status"],
                }
            )
        lineage.append(
            {
                "series_id": spec.get("series_id"),
                "run_id": spec.get("run_id"),
                "artifact_ref": spec["artifact_file"],
                "artifact_sha256": _sha256(artifact_path),
                "term": spec.get("term"),
                "normalization_scale": scale_id,
                "point_count": len(points),
                "geo": scale.get("geo"),
                "timeframe": scale.get("timeframe"),
                "collected_at": scale.get("collected_at"),
            }
        )
    rows.sort(key=lambda r: (str(r["period_start"]), str(r["run_id"]), str(r["query_id"])))

    if definition.get("require_comparability_gate"):
        for pos, left in enumerate(series):
            for right in series[pos + 1:]:
                verdict = check_cross_study_comparability(
                    entries_by_run.get(left.get("run_id")) or {},
                    entries_by_run.get(right.get("run_id")) or {},
                )
                gated_pairs.append(
                    {
                        "pair": [left.get("series_id"), right.get("series_id")],
                        "status": verdict["status"],
                        "reasons": verdict["reasons"],
                    }
                )
    blocked = [p for p in gated_pairs if p["status"] == "not_comparable"]

    dataset_path = out / "dataset.csv"
    with dataset_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    (out / "view-definition.json").write_text(
        json.dumps(definition, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = {
        "view_id": definition.get("view_id"),
        "comparison_mode": mode,
        "series": series_ids,
        "pair_verdicts": gated_pairs,
        "direct_comparison_blocked_pairs": len(blocked),
        "aggregation_performed": False,
        "note": (
            "parallel display only: series with not_comparable verdicts are shown "
            "side by side, never summed or rescaled (P6)"
        ),
    }
    (out / "comparability-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    provenance = {
        "view_id": definition.get("view_id"),
        "builder": {"module": "research.views", "version": VIEW_BUILDER_VERSION},
        "lineage": lineage,
        "uncertainty_notes": [GT_ZERO_NOTE],
        "inputs_read_only": True,
    }
    (out / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "out_dir": str(out),
        "row_count": len(rows),
        "series_count": len(series),
        "pair_verdicts": gated_pairs,
        "direct_comparison_blocked_pairs": len(blocked),
        "files": ["view-definition.json", "dataset.csv", "comparability-report.json", "provenance.json"],
    }
