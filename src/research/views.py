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
import json
from pathlib import Path

from research.catalog import SOURCE_MEASUREMENTS
from research.comparability import check_cross_study_comparability
from storage.contracts import ArtifactDescriptor
from storage.readers import get_reader
from storage.registry import ArtifactRegistry
from storage.sniff import sniff_path
from validation.core import validate_document
from validation.integrity import sha256_file
from validation.schema_registry import get_schema

__all__ = [
    "VIEW_BUILDER_VERSION",
    "GT_ZERO_NOTE",
    "validate_view_definition",
    "refuse_raw_output",
    "build_view",
]

VIEW_BUILDER_VERSION = "1.1.0"

#: Default artifact registry (G4).  The registry decides which reader reads
#: which shape; views never parse artifact JSON themselves.
DEFAULT_ARTIFACT_REGISTRY = Path("metadata/artifacts/artifact-registry.json")

#: Google Trends ``0`` conflates a true zero with a below-threshold week.
#: Recorded as ``observed_zero`` with this note in ``provenance.json``.
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


def _gt_document_metadata(artifact_path: Path) -> dict:
    """Read the *document-level* metadata of a Google Trends artifact.

    The storage reader contract carries bucket points but not document
    metadata, so this reads the label keys only (never the ``data`` array):
    that is a Google-Trends document fact, not a second artifact parser.
    """
    try:
        document = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"artifact unreadable: {artifact_path}: {error}") from error
    label = document.get("query", document.get("keyword"))
    return {
        "label": label if isinstance(label, str) else None,
        "geo": document.get("geo"),
        "timeframe": document.get("timeframe"),
        "collected_at": document.get("collected_at"),
    }


def _point_row(bucket: object, value: object) -> dict:
    period, start, end = _split_period(bucket)
    return {
        "period": period,
        "period_start": start,
        "period_end": end,
        "value": value,
        "status": "observed_nonzero" if value != 0 else "observed_zero",
    }


def _read_series_points(
    artifact_path: Path, *, term: str, artifact_registry: ArtifactRegistry | None
) -> tuple[list[dict], dict]:
    """Read bucket values for ``term`` through the G4 storage contract.

    Format detection comes from ``storage.sniff`` and the reader from the
    artifact registry, so a shape is read exactly as the G4 registry says it
    should be (G4 §8).  An unregistered or ambiguous shape is refused rather
    than parsed here (d.md §12 / P8: no reconstruction outside the contract).
    Only the comparison/single *label* is read directly, because the reader
    returns points, not document metadata.
    """
    if artifact_registry is None:
        raise ValueError(
            "artifact registry is not available; refusing to read an artifact "
            "outside the storage contract"
        )
    sniff = sniff_path(artifact_path)
    reader_id = artifact_registry.reader_for(
        schema_id=sniff.schema_id,
        artifact_type=sniff.artifact_type,
        format=sniff.format,
    )
    reader = get_reader(reader_id) if reader_id else None
    if reader is None:
        raise ValueError(
            f"no registered reader for {artifact_path.name} "
            f"(format={sniff.format}, artifact_type={sniff.artifact_type}); "
            "refusing to read it outside the storage contract"
        )
    descriptor = ArtifactDescriptor(
        artifact_id=artifact_path.name,
        artifact_type=sniff.artifact_type,
        format=sniff.format,
        schema_id=sniff.schema_id,
        path=str(artifact_path),
    )
    rows: list[dict] = []
    scale: str | None = None
    metadata = _gt_document_metadata(artifact_path)
    if sniff.artifact_type == "comparison":
        for point in reader.read(descriptor, mode="comparison_rows"):
            values = point.get("values") or {}
            if scale is None:
                # The reader returns every declared term for every row, so the
                # first row's key set is the full comparison set (§11).
                scale = f"comparison:{sorted(str(key) for key in values)}"
            value = values.get(term)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            rows.append(_point_row(point.get("bucket"), value))
    else:
        scale = f"single:{metadata['label']}"
        for point in reader.read(descriptor, mode="points"):
            value = point.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            rows.append(_point_row(point.get("bucket"), value))
    if not rows:
        raise ValueError(f"no usable points for term {term!r} in {artifact_path}")
    scale_info = {
        "normalization_scale": scale,
        "geo": metadata["geo"],
        "timeframe": metadata["timeframe"],
        "collected_at": metadata["collected_at"],
    }
    return rows, scale_info


#: Source-specific extractors (G7 P1/P6: the core names no platform in its
#: flow).  A source joins by registering an extractor here **and** a
#: ``SOURCE_MEASUREMENTS`` row; ``build_view`` refuses a source that has
#: neither, so rows can never carry another source's measurement.
_SOURCE_EXTRACTORS = {
    "google-trends": _read_series_points,
}


def _is_under_data_raw(path: Path, repo_root: Path) -> bool:
    """True when ``path`` sits under any ``data/raw`` directory of the repo."""
    try:
        parts = path.resolve().relative_to(Path(repo_root).resolve()).parts
    except ValueError:
        return False
    return any(
        parts[index] == "data" and parts[index + 1] == "raw"
        for index in range(len(parts) - 1)
    )


def refuse_raw_output(out_dir, repo_root) -> None:
    """Refuse to write derived output under any ``data/raw`` directory.

    Exported because every derived-output writer (views, audits) must honour
    the same invariant: raw data is immutable (AGENTS.md).
    """
    if _is_under_data_raw(Path(out_dir), Path(repo_root)):
        raise ValueError(
            f"refusing to write derived output under data/raw: {out_dir} "
            "(raw data is immutable)"
        )


def _sha256(path: Path) -> str:
    return sha256_file(path)


def build_view(
    definition: dict,
    series: list[dict],
    catalog: dict,
    *,
    repo_root,
    out_dir,
    artifact_registry: ArtifactRegistry | None = None,
) -> dict:
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
    refuse_raw_output(out, root)
    registry = (
        artifact_registry
        if artifact_registry is not None
        else ArtifactRegistry.load(root / DEFAULT_ARTIFACT_REGISTRY)
    )
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
        entry = entries_by_run.get(spec.get("run_id"))
        source_id = (entry or {}).get("source_id")
        extractor = _SOURCE_EXTRACTORS.get(source_id)
        if extractor is None:
            raise ValueError(
                f"no view extractor for source_id {source_id!r} "
                f"(run_id {spec.get('run_id')!r}); refusing to emit rows "
                "carrying another source's measurement (G7 P1/P6)"
            )
        measurement = SOURCE_MEASUREMENTS.get(source_id)
        if measurement is None:
            raise ValueError(
                f"source {source_id!r} has no registered measurement; refusing to guess one"
            )
        measurement_id, unit = measurement
        points, scale = extractor(
            artifact_path, term=spec["term"], artifact_registry=registry
        )
        scale_id = f"{scale['normalization_scale']}@{spec.get('run_id')}"
        for point in points:
            rows.append(
                {
                    "study_id": (entry or {}).get("study_id"),
                    "source_id": source_id,
                    "compound_id": spec.get("compound_id"),
                    "query_id": spec.get("query_id"),
                    "period": point["period"],
                    "period_start": point["period_start"],
                    "period_end": point["period_end"],
                    "measurement_id": measurement_id,
                    "value": point["value"],
                    "unit": unit,
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
