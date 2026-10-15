"""Downstream correction manifest for frozen Google Trends legacy labels.

The raw Google Trends phase-a records are immutable.  This module records a
reproducible downstream correction for ``ISS-20261015-GT-002``: records derived
from the verbatim tool output stored ``Dec 28, 2025 – Jan 3, 2026`` as
``2026-12-28`` in eight legacy JSON series.  The original ``raw_text`` (or the
same run's comparison ``raw_text`` when the per-term file omitted it) anchors
the correction to ``2025-12-28`` without editing raw observations.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from collection.adapters.google_trends.boundary import BoundaryCaptureError, _label_to_date
from validation.reporting import dump_json

__all__ = [
    "BAD_LABEL_DATE",
    "CORRECTED_LABEL_DATE",
    "LEGACY_RUN_IDS",
    "TARGET_RECORDS",
    "build_manifest",
    "correct_record",
    "dump_manifest",
    "write_manifest",
]


SCHEMA_ID = "gt-legacy-label-correction-v1"
SCHEMA_VERSION = "1.0.0"
ISSUE_ID = "ISS-20261015-GT-002"
STUDY_ID = "cannabinoid-multi-trends"
SOURCE = "google_trends"
BAD_LABEL_DATE = "2026-12-28"
CORRECTED_LABEL_DATE = "2025-12-28"

LEGACY_RUN_IDS = (
    "20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m",
    "20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m",
)

TARGET_RECORDS = (
    "records_cbd-rikiddo.json",
    "records_cbg-rikiddo.json",
    "records_cbn-rikiddo.json",
    "records_thc-rikiddo.json",
)

COMPARISON_FALLBACK = "comparison_ja1.json"


class CorrectionError(ValueError):
    """Raised when the frozen legacy records no longer match the correction rule."""


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise CorrectionError(f"not a JSON object: {path}")
    return document


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _split_terms(header: str) -> list[str]:
    if header.startswith("Interest over time for: "):
        body = header[len("Interest over time for: "):]
        return [part.strip() for part in body.split(",") if part.strip()]
    if header.startswith("Comparison: "):
        body = header[len("Comparison: "):]
        return [part.strip() for part in body.split(" vs ") if part.strip()]
    raise CorrectionError("raw_text does not carry a supported Google Trends header")


def _parse_raw_text_table(raw_text: str) -> list[dict[str, Any]]:
    """Parse the stored text table into labels, parsed dates, and term values."""

    lines = raw_text.splitlines()
    terms: list[str] | None = None
    rows: list[dict[str, Any]] = []
    for line in lines:
        if line.startswith("Interest over time for: ") or line.startswith("Comparison: "):
            terms = _split_terms(line)
            continue
        if not line or line.startswith("Geo: ") or line.startswith("Average interest scores"):
            continue
        if line.startswith("  ") or line.startswith("Date\t"):
            continue
        if "\t" not in line:
            continue
        if terms is None:
            raise CorrectionError("data row appears before term header")
        label, *raw_values = line.split("\t")
        if len(raw_values) != len(terms):
            raise CorrectionError(
                f"raw_text row has {len(raw_values)} values for {len(terms)} terms: {label!r}"
            )
        try:
            parsed_date = _label_to_date(label.strip())
        except BoundaryCaptureError as error:
            raise CorrectionError(f"raw_text label cannot be parsed: {label!r}") from error
        values: dict[str, int] = {}
        for term, raw in zip(terms, raw_values):
            try:
                values[term] = int(raw.strip())
            except ValueError as error:
                raise CorrectionError(f"raw_text value is not an integer: {raw!r}") from error
        rows.append({"label": label.strip(), "date": parsed_date, "values": values})
    if not rows:
        raise CorrectionError("raw_text carries no data rows")
    return rows


def _point_index(record: dict[str, Any], date: str) -> int:
    data = record.get("data")
    if not isinstance(data, list):
        raise CorrectionError("record has no data array")
    matches = [index for index, point in enumerate(data) if isinstance(point, dict) and point.get("date") == date]
    if len(matches) != 1:
        raise CorrectionError(f"expected exactly one point dated {date}, found {len(matches)}")
    return matches[0]


def _evidence_document(record_path: Path, record: dict[str, Any]) -> tuple[Path, str]:
    raw_text = record.get("raw_text")
    if isinstance(raw_text, str) and raw_text.strip():
        return record_path, raw_text
    fallback = record_path.parent / COMPARISON_FALLBACK
    document = _read_json(fallback)
    raw_text = document.get("raw_text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise CorrectionError(f"no raw_text evidence in {record_path.name} or {COMPARISON_FALLBACK}")
    return fallback, raw_text


def _entry_for_record(repo_root: Path, run_id: str, record_name: str) -> dict[str, Any]:
    record_path = (
        repo_root
        / "datasets"
        / STUDY_ID
        / "data"
        / "raw"
        / SOURCE
        / run_id
        / record_name
    )
    record = _read_json(record_path)
    keyword = str(record.get("keyword") or "")
    index = _point_index(record, BAD_LABEL_DATE)
    point = record["data"][index]
    value = point.get("value")
    if not isinstance(value, int):
        raise CorrectionError(f"target point has no integer value: {record_path}")
    evidence_path, raw_text = _evidence_document(record_path, record)
    evidence_rows = _parse_raw_text_table(raw_text)
    same_series_evidence = evidence_path == record_path
    evidence_matches = [
        row
        for row in evidence_rows
        if row["date"] == CORRECTED_LABEL_DATE
        and keyword in row["values"]
        and (not same_series_evidence or row["values"][keyword] == value)
    ]
    if len(evidence_matches) != 1:
        raise CorrectionError(
            f"expected one raw_text evidence row for {keyword} at "
            f"{CORRECTED_LABEL_DATE}, found {len(evidence_matches)}"
        )
    evidence_value = evidence_matches[0]["values"][keyword]
    corrected = correct_record(record)
    corrected_dates = [point["date"] for point in corrected["data"]]
    if corrected_dates != sorted(corrected_dates):
        raise CorrectionError(f"corrected record is not chronological: {record_path}")
    return {
        "run_id": run_id,
        "path": _repo_relative(repo_root, record_path),
        "sha256": _sha256(record_path),
        "keyword": keyword,
        "timeframe": record.get("timeframe"),
        "collected_at": record.get("collected_at"),
        "data_index": index,
        "recorded_date": BAD_LABEL_DATE,
        "corrected_date": CORRECTED_LABEL_DATE,
        "value": value,
        "adjacent_recorded_dates": {
            "previous": record["data"][index - 1]["date"] if index else None,
            "next": record["data"][index + 1]["date"] if index + 1 < len(record["data"]) else None,
        },
        "raw_text_evidence": {
            "path": _repo_relative(repo_root, evidence_path),
            "label": evidence_matches[0]["label"],
            "parsed_start_date": evidence_matches[0]["date"],
            "value": evidence_value,
            "value_scale": (
                "same_single_series"
                if same_series_evidence
                else "comparison_relative_index_not_same_scale"
            ),
        },
        "raw_modified": False,
    }


def correct_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return a downstream-corrected copy of one affected legacy record."""

    corrected = copy.deepcopy(record)
    index = _point_index(corrected, BAD_LABEL_DATE)
    corrected["data"][index]["date"] = CORRECTED_LABEL_DATE
    return corrected


def build_manifest(repo_root: Path | str = ".") -> dict[str, Any]:
    repo = Path(repo_root)
    entries = [
        _entry_for_record(repo, run_id, record_name)
        for run_id in LEGACY_RUN_IDS
        for record_name in TARGET_RECORDS
    ]
    entries.sort(key=lambda entry: entry["path"])
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "issue_id": ISSUE_ID,
        "recorded_at": "2026-10-15",
        "layer": "interim",
        "study_id": STUDY_ID,
        "source": SOURCE,
        "rule": {
            "id": "gt-phase-a-week-label-year-correction",
            "recorded_date": BAD_LABEL_DATE,
            "corrected_date": CORRECTED_LABEL_DATE,
            "reason": (
                "Stored raw_text labels the affected bucket as "
                "Dec 28, 2025 – Jan 3, 2026; raw JSON records rendered the "
                "bucket start as 2026-12-28. Raw files remain immutable."
            ),
        },
        "scope": {
            "run_ids": list(LEGACY_RUN_IDS),
            "record_names": list(TARGET_RECORDS),
        },
        "summary": {
            "affected_file_count": len(entries),
            "raw_files_modified": False,
            "correction_action": "downstream_date_label_correction",
        },
        "files": entries,
    }


def dump_manifest(manifest: dict[str, Any]) -> str:
    return dump_json(manifest)


def write_manifest(repo_root: Path | str, output: Path | str) -> dict[str, Any]:
    manifest = build_manifest(repo_root)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_manifest(manifest), encoding="utf-8")
    return manifest
