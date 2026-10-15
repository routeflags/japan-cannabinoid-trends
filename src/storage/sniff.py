"""Content-based artifact identification (d.md P3 / §16).

Legacy artifacts have no manifest, so their meaning has to come from their
content: ``sniff_path`` inspects binary magic / text shape and delegates JSON
structure to ``sniff_document``.  Every claim carries evidence strings, and
uncertain content stays ``ambiguous`` or ``partial`` - it is never forced
into a schema (d.md §16: "既存ファイルの命名規則だけで意味を確定しない").

States
------
- ``recognized``: the content matches a registered artifact schema;
- ``partial``   : the storage format is known but no registered schema can be
  asserted (candidate type only);
- ``ambiguous`` : two interpretations conflict (e.g. an aggregate summary
  block *and* a per-bucket array);
- ``unknown``   : the file cannot be identified at all.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

__all__ = ["SniffResult", "sniff_document", "sniff_path"]

SQLITE_MAGIC = b"SQLite format 3\x00"
PDF_MAGIC = b"%PDF"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
PARQUET_MAGIC = b"PAR1"

#: A JSON document larger than this is not parsed for sniffing (the file is
#: still hashed and counted; only the structural claim is withheld).
_MAX_JSON_BYTES = 256 * 1024 * 1024
_HEAD_BYTES = 65536

_SUMMARY_MARKS = ("data_points", "avg_5y", "peak_value", "first_value", "last_value")

#: Known database schemas (tables observed in the consistency stores).
_TRENDS_DB_TABLES = {"runs"}


@dataclass(frozen=True)
class SniffResult:
    format: str
    state: str
    artifact_type: str | None = None
    schema_id: str | None = None
    contains_full_timeseries: bool | None = None
    record_count: int | None = None
    #: ``data_points`` declared by a summary block (an aggregate claim, not a
    #: record count - kept separate so the two are never conflated).
    declared_data_points: int | None = None
    evidence: tuple[str, ...] = ()


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# JSON structure
# ---------------------------------------------------------------------------


def _sniff_list(items: list) -> SniffResult:
    if not items:
        # The count is determinate (0) even though the meaning is not:
        # an empty array could be a zero series or an empty page.
        return SniffResult(
            "json", "ambiguous", record_count=0, evidence=("empty_json_array",)
        )
    objects = [item for item in items[:5] if isinstance(item, dict)]
    if not objects:
        return SniffResult("json", "partial", evidence=("json_array_non_objects",))
    if any(item.get("schemaVersion") == "tweet-result-v1" for item in objects) or any(
        "recordType" in item for item in objects
    ):
        return SniffResult(
            "json",
            "recognized",
            artifact_type="raw_records",
            schema_id="x-tweet-result-list-v1",
            record_count=len(items),
            evidence=("records:schemaVersion=tweet-result-v1",),
        )
    kinds = [item.get("kind") for item in objects if "kind" in item]
    if kinds and all(kind == "youtube#searchResult" for kind in kinds):
        return SniffResult(
            "json",
            "recognized",
            artifact_type="raw_records",
            schema_id="youtube-search-result-list-v1",
            record_count=len(items),
            evidence=("records:kind=youtube#searchResult",),
        )
    return SniffResult(
        "json", "partial", record_count=len(items), evidence=("json_array_of_objects",)
    )


def _sniff_dict(document: dict) -> SniffResult:
    keys = set(document)
    if {"job_id", "status"} <= keys and ({"updated_at", "started_at"} & keys):
        return SniffResult(
            "json",
            "recognized",
            artifact_type="checkpoint",
            schema_id="collection-checkpoint-v1",
            evidence=("fields:job_id,status",),
        )
    # A platform no-data response is evidence, not a zero series (P8); the
    # shape is a registered raw_response (google-trends-no-data-v1) read by
    # the no-data reader, which refuses every series mode (d.md §12).
    if "no_data_keywords" in keys:
        return SniffResult(
            "json",
            "recognized",
            artifact_type="raw_response",
            schema_id="google-trends-no-data-v1",
            evidence=("fields:no_data_keywords",),
        )
    if "error" in keys:
        # A recorded error response is evidence of a failed call; it is never
        # an empty result (AGENTS.md: a collection failure is not zero).
        return SniffResult(
            "json",
            "partial",
            artifact_type="raw_response",
            evidence=("fields:error",),
        )
    if "monthly_stats" in keys:
        return SniffResult(
            "json", "partial", evidence=("fields:monthly_stats",)
        )

    summary_marks = [mark for mark in _SUMMARY_MARKS if mark in keys]
    data = document.get("data")
    if isinstance(data, list) and summary_marks:
        return SniffResult(
            "json",
            "ambiguous",
            evidence=("both:data_array", *(f"aggregate:{mark}" for mark in summary_marks)),
        )

    if isinstance(data, list):
        if data:
            rows = [row for row in data[:5] if isinstance(row, dict)]
            if not rows:
                return SniffResult("json", "partial", evidence=("data_rows_not_objects",))
            row = rows[0]
            terms = document.get("terms")
            if isinstance(terms, list) and terms and all(
                term in row for term in terms if isinstance(term, str)
            ):
                return SniffResult(
                    "json",
                    "recognized",
                    artifact_type="comparison",
                    schema_id="google-trends-comparison-v1",
                    contains_full_timeseries=True,
                    record_count=len(data),
                    evidence=("comparison:terms", f"rows:{len(data)}"),
                )
            if isinstance(row.get("date"), str):
                has_value = any(_is_number(item.get("value")) for item in rows)
                has_interest = any(_is_number(item.get("interest")) for item in rows)
                if has_value and has_interest:
                    return SniffResult(
                        "json", "ambiguous", evidence=("series:value_and_interest",)
                    )
                if has_value or has_interest:
                    schema_id = (
                        "google-trends-records-v1"
                        if has_interest
                        else "google-trends-interest-over-time-v1"
                    )
                    return SniffResult(
                        "json",
                        "recognized",
                        artifact_type="timeseries",
                        schema_id=schema_id,
                        contains_full_timeseries=True,
                        record_count=len(data),
                        evidence=(
                            "series:date+interest" if has_interest else "series:date+value",
                            f"points:{len(data)}",
                        ),
                    )
                return SniffResult(
                    "json", "partial", evidence=("series:no_values",)
                )
            return SniffResult("json", "partial", evidence=("data_rows_unrecognized",))
        # an empty series can still be identified by its companion fields
        if "keyword" in keys:
            return SniffResult(
                "json",
                "recognized",
                artifact_type="timeseries",
                schema_id="google-trends-interest-over-time-v1",
                contains_full_timeseries=True,
                record_count=0,
                evidence=("series:empty", "fields:keyword"),
            )
        if "query" in keys:
            return SniffResult(
                "json",
                "recognized",
                artifact_type="timeseries",
                schema_id="google-trends-records-v1",
                contains_full_timeseries=True,
                record_count=0,
                evidence=("series:empty", "fields:query"),
            )
        return SniffResult("json", "partial", evidence=("empty_data_array",))

    if isinstance(document.get("items"), list):
        page_info = document.get("pageInfo")
        evidence = [f"items:{len(document['items'])}"]
        if isinstance(page_info, dict) and _is_number(page_info.get("totalResults")):
            evidence.append(f"pageInfo:totalResults={page_info['totalResults']}")
        return SniffResult(
            "json",
            "recognized",
            artifact_type="page",
            schema_id="youtube-search-list-response-v1",
            record_count=len(document["items"]),
            evidence=tuple(evidence),
        )

    if "result" in keys and "term" in keys:
        return SniffResult(
            "json",
            "recognized",
            artifact_type="raw_response",
            schema_id="google-trends-related-queries-v1",
            evidence=("fields:term,result",),
        )

    if summary_marks:
        declared = document.get("data_points")
        evidence = ["summary:" + ",".join(summary_marks)]
        if _is_number(declared) and isinstance(declared, int):
            evidence.append(f"declared_data_points:{declared}")
        return SniffResult(
            "json",
            "recognized",
            artifact_type="summary",
            schema_id="google-trends-summary-v1",
            contains_full_timeseries=False,
            declared_data_points=int(declared) if _is_number(declared) else None,
            evidence=tuple(evidence),
        )

    # Legacy variants: structural evidence without a registered schema.
    # They are reported as partial (never forced into a schema), with the
    # fields that made them recognisable so the audit stays actionable
    # (a reader can be registered later - d.md §7).
    if "queries" in keys and isinstance(data, dict):
        return SniffResult(
            "json", "partial", evidence=("fields:queries", "data:object")
        )
    if "queries" in keys:
        return SniffResult(
            "json", "partial", artifact_type="raw_response", evidence=("fields:queries",)
        )
    if "comparisons" in keys:
        return SniffResult("json", "partial", evidence=("fields:comparisons",))
    averages_keys = {"averages", "average_interest"} & keys
    if "terms" in keys and averages_keys:
        # Comparison averages without any per-bucket series (ART-006): the
        # two recorded spellings (``averages`` / ``average_interest``) share
        # one aggregate-only schema.  Both spellings together, or per-bucket
        # ``data`` alongside the averages, is an unattested variant and stays
        # partial (never forced into the schema).
        if len(averages_keys) == 1 and "data" not in document:
            return SniffResult(
                "json",
                "recognized",
                artifact_type="summary",
                schema_id="google-trends-comparison-averages-v1",
                contains_full_timeseries=False,
                evidence=("comparison:averages_only",),
            )
        return SniffResult(
            "json", "partial", evidence=("comparison:averages_only",)
        )
    return SniffResult("json", "partial", evidence=("json_object",))


def sniff_document(document) -> SniffResult:
    """Identify a parsed JSON document (d.md §16)."""
    if isinstance(document, list):
        return _sniff_list(document)
    if isinstance(document, dict):
        return _sniff_dict(document)
    return SniffResult("json", "partial", evidence=("json_scalar",))


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------


def _sniff_sqlite(path: Path) -> SniffResult:
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    except sqlite3.Error:
        return SniffResult(
            "sqlite", "partial", evidence=("magic:sqlite", "tables:unreadable")
        )
    try:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error:
        return SniffResult(
            "sqlite", "partial", evidence=("magic:sqlite", "tables:unreadable")
        )
    finally:
        connection.close()
    evidence = ["magic:sqlite", "tables:" + ",".join(tables)]
    if tables and _TRENDS_DB_TABLES <= set(tables):
        return SniffResult(
            "sqlite",
            "recognized",
            artifact_type="database",
            schema_id="sqlite-trends-db-v1",
            evidence=tuple(evidence),
        )
    return SniffResult("sqlite", "partial", evidence=tuple(evidence))


def sniff_path(path) -> SniffResult:
    """Identify a stored file without changing it (read-only).

    The file name is a hint only (suffix for text formats); binary formats are
decided by magic bytes and JSON structure by parsing the document.
    """
    target = Path(path)
    suffix = target.suffix.lower()
    try:
        with target.open("rb") as handle:
            head = handle.read(_HEAD_BYTES)
        size = target.stat().st_size
    except OSError:
        return SniffResult("unknown", "unknown", evidence=("unreadable",))

    if size == 0:
        return SniffResult("unknown", "unknown", evidence=("empty_file",))

    if head.startswith(SQLITE_MAGIC):
        return _sniff_sqlite(target)
    if suffix in (".db", ".sqlite", ".sqlite3"):
        return SniffResult(
            "unknown", "partial", evidence=("sqlite_extension_without_magic",)
        )
    if head.startswith(PARQUET_MAGIC):
        return SniffResult("parquet", "partial", evidence=("magic:parquet",))
    if head.startswith(PDF_MAGIC):
        return SniffResult("binary", "partial", evidence=("magic:pdf",))
    if head.startswith(PNG_MAGIC):
        return SniffResult("binary", "partial", evidence=("magic:png",))
    if head.startswith(JPEG_MAGIC):
        return SniffResult("binary", "partial", evidence=("magic:jpeg",))
    if b"\x00" in head:
        return SniffResult(
            "binary", "partial", evidence=(f"extension:{suffix or 'none'}", "null_bytes")
        )

    if suffix == ".csv":
        return SniffResult("csv", "partial", evidence=("extension:csv",))
    if suffix in (".md", ".txt"):
        return SniffResult("text", "partial", evidence=(f"extension:{suffix.lstrip('.')}",))

    if suffix == ".jsonl":
        try:
            first_line = head.split(b"\n", 1)[0].strip()
            json.loads(first_line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return SniffResult(
                "jsonl", "unknown", evidence=("jsonl:first_line_unparsable",)
            )
        return SniffResult("jsonl", "partial", evidence=("jsonl:records",))

    looks_json = suffix == ".json" or head.lstrip()[:1] in (b"{", b"[")
    if looks_json:
        if size > _MAX_JSON_BYTES:
            return SniffResult(
                "json", "partial", evidence=("json:too_large_to_parse",)
            )
        try:
            with target.open(encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return SniffResult("json", "unknown", evidence=("json_parse_error",))
        return sniff_document(document)

    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        return SniffResult("binary", "partial", evidence=("non_utf8_bytes",))
    return SniffResult("text", "partial", evidence=("text_head",))
