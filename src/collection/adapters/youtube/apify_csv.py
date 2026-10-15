"""YouTube Apify CSV handover adapter/driver (COL-016 MVP, COL-033 pattern).

This module codifies the adopted COL-033 pattern as a reusable,
declaration-driven entry point: an operator hands over a YouTube Apify CSV
export obtained outside the pipeline, and this wrapper turns explicitly
declared facts about it into a ``staging-declaration-v1`` document for the
existing adoption path (``collection.core.staging.stage_declaration`` ->
``collection.core.pipeline.adopt_staged``).  It adds no new catalog,
adoption, counting, or quarantine rule; those stay where they already live.

What this module is NOT:

- not a live Apify client: there is no token handling, no HTTP transport,
  no pagination, and no dataset export fetching.  ``collect`` always fails
  closed until a live transport lands under a separate plan;
- not a window compiler: ``date_filter`` values are recorded as the request
  parameter they are and are never compiled into absolute windows (WIN-002
  stays open);
- not a CSV normalizer: the payload is staged byte-for-byte and never
  re-expressed as JSON or mapped onto a generic YouTube schema (observed
  exports vary from ~100 to ~500 columns);
- not registered in ``collection.adapters`` dispatch (``_FACTORIES`` /
  ``_WINDOW_COMPILERS``): registering a source that cannot collect would
  imply a capability that has no evidence.  Build the adapter explicitly
  with :func:`build_adapter`.

Fail-closed rules (one rule, applied uniformly):

- request facts (``query_id`` / keyword / ``date_filter`` / reference time)
  are declared, never inferred from the payload's own columns;
- a missing or unreadable CSV is a configuration error: nothing is staged
  and no ``returned_count=0`` success run is invented;
- identity and capabilities come from the collector registry
  (``config/collectors.json``); ``unknown`` / ``unverified`` are reported
  as-is and never upgraded without measured evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

from collection.core.contracts import CollectionResult
from collection.core.registry import find_collector
from collection.core.staging import load_declaration, stage_declaration
from validation.schemas.artifact import COMPLETENESS_VALUES
from validation.schemas.collection_run import EXECUTION_STATUSES
from validation.schemas.temporal import COLLECTOR_WINDOW_TYPES, GRANULARITIES

__all__ = [
    "ADAPTER_VERSION",
    "ARTIFACT_FORMAT",
    "ARTIFACT_SCHEMA_ID",
    "ARTIFACT_TYPE",
    "COLLECTOR_ID",
    "DATE_FILTERS",
    "SOURCE_ID",
    "YouTubeApifyCsvAdapter",
    "YouTubeApifyCsvError",
    "build_adapter",
    "build_csv_run",
    "build_declaration",
    "collector_identity",
    "stage_csv",
]

#: Pinned routing identity for the handover path.  The adapter instance itself
#: is bound to the registry entry (see :func:`build_adapter`); these constants
#: exist so the declaration builder cannot be pointed at another collector.
SOURCE_ID = "youtube"
COLLECTOR_ID = "youtube-apify-scraper"
#: Expected adapter build; the instance reports the registry's value, and the
#: contract test pins the two to be equal (A7).
ADAPTER_VERSION = "unknown"

#: The only artifact this handover accepts: the Apify dataset CSV export as
#: produced (``metadata/artifacts/artifact-registry.json``; counted with
#: ``csv-record-reader``, i.e. CSV records via the ``csv`` module, never
#: physical lines).
ARTIFACT_SCHEMA_ID = "youtube-dataset-csv-v1"
ARTIFACT_FORMAT = "csv"
ARTIFACT_TYPE = "raw_records"

#: Request vocabulary the wrapper accepts for ``collection_request.date_filter``.
#: Evidence: ``hour`` / ``today`` / ``week`` / ``month`` / ``year`` are the
#: actor input values documented in
#: ``.github/skills/apify-youtube-scraper/SKILL.md`` (relative rolling
#: windows; ``month`` measured as trailing ~30 days on 2026-10-10);
#: ``all`` is the value used by five of the six adopted COL-033 runs
#: (``metadata/provenance/declarations/20261015-youtube-csv-adoption.json``)
#: for the unbounded request.  The *meanings* are deliberately not encoded
#: here: resolving a relative filter against a reference time is the window
#: compiler's job (WIN-002, not implemented in this MVP).
DATE_FILTERS = ("all", "hour", "today", "week", "month", "year")

#: Default description of what the absolute window means for these runs
#: (COL-033 wording): the observed video publish-date range in the payload,
#: not the API condition.
DEFAULT_BOUNDARY_SEMANTICS = (
    "observed video publish-date range in payload; not the API condition"
)

#: Canonical limitation recorded on every run built here: the request filter
#: and the observed range are separate facts (owner direction 2026-10-15).
DATE_FILTER_SEPARATION_LIMITATION = (
    "date_filter is the API request parameter (a relative rolling window "
    "resolved by the collector); window.start/end_exclusive is the observed "
    "video publish-date range in the payload and must not be treated as the "
    "API search condition (owner direction 2026-10-15)"
)

_DECLARATION_VERSION = "staging-declaration-v1"


class YouTubeApifyCsvError(ValueError):
    """A handover input cannot be used (fail closed, nothing staged)."""


def collector_identity(registries) -> dict:
    """Return the registry evidence for ``youtube-apify-scraper``.

    The registry is the record of truth: status, version, and capabilities
    are reported as recorded (currently ``unverified`` / ``unknown``) and
    are never upgraded here.  Raises :class:`YouTubeApifyCsvError` when the
    collector is not registered at all.
    """
    entry = find_collector(registries, SOURCE_ID, COLLECTOR_ID)
    if entry is None:
        raise YouTubeApifyCsvError(
            f"collector {COLLECTOR_ID!r} is not registered for source "
            f"{SOURCE_ID!r}; register it before handing over its payloads"
        )
    return {
        "collector_id": entry.get("collector_id"),
        "source_id": entry.get("source_id"),
        "adapter_id": entry.get("adapter_id"),
        "version": entry.get("version"),
        "status": entry.get("status"),
        "capabilities": dict(entry.get("capabilities") or {}),
    }


class YouTubeApifyCsvAdapter:
    """Handover-only adapter for the Apify ``youtube-scraper`` CSV export.

    Implements the :mod:`collection.core.contracts` shape so it is verified
    with the same contract check as every other adapter, but the transport
    is a handover directory, not the Apify API: :meth:`collect` always
    returns a ``failed`` result (failure evidence, never zero observations)
    and :meth:`extract_observations` returns no rows (row-level CSV parsing
    and normalization are out of scope; record counts are determined by the
    registered ``csv-record-reader`` at the L1 gate).

    Instances are built with :func:`build_adapter` so identity and
    capabilities are the registry's values, not this module's guesses.
    """

    source_id = SOURCE_ID
    collector_id = COLLECTOR_ID

    def __init__(self, *, adapter_id: str, version: str, capabilities=None):
        self.adapter_id = adapter_id
        self.version = version
        self._capabilities = dict(capabilities or {})

    def capabilities(self) -> dict:
        """The registry's capability map (a copy; callers cannot mutate it)."""
        return dict(self._capabilities)

    def validate_plan(self, plan: dict) -> list:
        """Generic request checks; the YouTube request vocabulary lives in
        :func:`build_csv_run` (the declaration path), not in the plan."""
        violations: list[str] = []
        query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
        text = query.get("text")
        if not isinstance(text, str) or not text:
            violations.append(
                "query.text is required (declared, never inferred from a payload)"
            )
        window = plan.get("window") if isinstance(plan.get("window"), dict) else {}
        if not window.get("start") or not window.get("end_exclusive"):
            violations.append("window.start and window.end_exclusive are required")
        return violations

    def collect(self, plan: dict) -> CollectionResult:
        """Refuse: live Apify collection is not implemented (MVP blocked).

        The failure is recorded as evidence with ``completeness="missing"``;
        it is never converted into zero observations.
        """
        message = (
            "live Apify collection is not implemented; this adapter only "
            f"hands over CSV exports through {_DECLARATION_VERSION} "
            "(build_csv_run/stage_csv)"
        )
        return CollectionResult(
            raw={
                "collector_id": self.collector_id,
                "error": {"message": message},
            },
            status="failed",
            returned_count=0,
            errors=[{"code": "LIVE_TRANSPORT_UNIMPLEMENTED", "message": message}],
            pagination_exhausted=None,
            completeness="missing",
            submitted_parameters={},
            temporal={},
        )

    def extract_observations(self, raw) -> list:
        """No row-level extraction: the raw CSV layer is never normalized
        into a generic schema here, and per-video rows are never published."""
        return []

    def describe_execution(self) -> dict:
        return {
            "collector_id": self.collector_id,
            "adapter_id": self.adapter_id,
            "collection_mode": "external_staged",
            "transport": "actor handover (no live call is issued)",
            "version": self.version,
        }


def build_adapter(registries) -> YouTubeApifyCsvAdapter:
    """Bind the adapter to the registry's ``youtube-apify-scraper`` entry."""
    identity = collector_identity(registries)
    return YouTubeApifyCsvAdapter(
        adapter_id=identity["adapter_id"],
        version=identity["version"],
        capabilities=identity["capabilities"],
    )


def _require_text(name: str, value) -> str:
    if not isinstance(value, str) or not value:
        raise YouTubeApifyCsvError(
            f"{name} is required: the handover declares it and never infers "
            "it from the CSV payload"
        )
    return value


def _require_csv_file(csv_path) -> Path:
    path = Path(csv_path)
    if not path.is_file():
        raise YouTubeApifyCsvError(
            f"csv source {str(csv_path)!r} does not exist or is not a file: "
            "a missing or failed collection is never recorded as "
            "returned_count=0 (nothing was staged)"
        )
    return path


def build_csv_run(
    *,
    csv_path,
    run_id: str,
    study_id: str,
    query_keyword: str,
    query_id: str,
    date_filter: str,
    reference_time: str,
    window_start: str,
    window_end_exclusive: str,
    started_at: str,
    finished_at: str,
    timestamp_basis: str,
    purpose: str,
    granularity: str = "day",
    timezone: str = "UTC",
    collector_window_type: str,
    boundary_semantics: str = DEFAULT_BOUNDARY_SEMANTICS,
    exact_window_match: bool = False,
    limitations=None,
    execution_status: str = "success",
    returned_count: int | None = None,
    record_count: int | None = None,
    errors=None,
    artifact_filename: str | None = None,
    completeness: str = "complete",
    environment=None,
) -> dict:
    """Build one ``staging-declaration-v1`` run entry for a YouTube CSV.

    Every request fact is a caller-supplied argument: ``query_id`` /
    ``query_keyword`` / ``date_filter`` / ``reference_time`` have no defaults
    worth guessing, so omitting one fails closed instead of reading the
    payload's own columns.  Pattern-descriptive facts (granularity /
    boundary semantics / the dateFilter separation limitation) default to the
    adopted COL-033 wording and may be overridden explicitly.

    ``collector_window_type`` has no default on purpose: mapping a relative
    ``date_filter`` onto a window type is compilation (WIN-002), and this
    wrapper does not compile.

    Counts: ``record_count`` / ``returned_count`` left as ``None`` are
    derived by the existing driver with the registered ``csv-record-reader``
    (CSV records via the ``csv`` module, not physical lines); declared values
    are passed through unchanged for the L1 gate to verify.  Nothing here
    re-implements that rule.
    """
    source = _require_csv_file(csv_path)
    _require_text("run_id", run_id)
    _require_text("study_id", study_id)
    _require_text("purpose", purpose)
    _require_text("query_keyword", query_keyword)
    _require_text("query.query_id", query_id)
    _require_text("collection_request.date_filter", date_filter)
    if date_filter not in DATE_FILTERS:
        raise YouTubeApifyCsvError(
            f"collection_request.date_filter {date_filter!r} is not in the "
            f"evidenced request vocabulary {list(DATE_FILTERS)}; unmeasured "
            "filter values fail closed (nothing was staged)"
        )
    _require_text("collection_request.reference_time", reference_time)
    _require_text("window.start", window_start)
    _require_text("window.end_exclusive", window_end_exclusive)
    _require_text("timestamps.started_at", started_at)
    _require_text("timestamps.finished_at", finished_at)
    _require_text("timestamps.basis", timestamp_basis)
    _require_text("temporal.collector_window_type", collector_window_type)
    if collector_window_type not in COLLECTOR_WINDOW_TYPES:
        raise YouTubeApifyCsvError(
            f"temporal.collector_window_type {collector_window_type!r} is not "
            f"one of {list(COLLECTOR_WINDOW_TYPES)} (nothing was staged)"
        )
    _require_text("temporal.boundary_semantics", boundary_semantics)
    if granularity not in GRANULARITIES:
        raise YouTubeApifyCsvError(
            f"window.granularity {granularity!r} is not one of "
            f"{list(GRANULARITIES)} (nothing was staged)"
        )
    if execution_status not in EXECUTION_STATUSES:
        raise YouTubeApifyCsvError(
            f"execution.status {execution_status!r} is not one of "
            f"{list(EXECUTION_STATUSES)} (nothing was staged)"
        )
    if completeness not in COMPLETENESS_VALUES:
        raise YouTubeApifyCsvError(
            f"artifacts[0].completeness {completeness!r} is not one of "
            f"{list(COMPLETENESS_VALUES)} (nothing was staged)"
        )
    for name, count in (
        ("artifacts[0].record_count", record_count),
        ("execution.returned_count", returned_count),
    ):
        if count is not None and (not isinstance(count, int) or count < 0):
            raise YouTubeApifyCsvError(
                f"{name} must be a non-negative integer or be omitted for "
                f"derivation (got {count!r}; nothing was staged)"
            )
    extra_limitations = list(limitations) if limitations is not None else []
    for limitation in extra_limitations:
        if not isinstance(limitation, str) or not limitation:
            raise YouTubeApifyCsvError(
                "temporal.limitations entries must be non-empty strings "
                "(nothing was staged)"
            )
    filename = artifact_filename or source.name
    if not filename or filename in (".", "..") or "/" in filename or "\\" in filename:
        raise YouTubeApifyCsvError(
            f"artifact filename {filename!r} is not a single path component "
            "(nothing was staged)"
        )
    declared_environment = dict(environment) if environment is not None else {}
    if not isinstance(declared_environment, dict):
        raise YouTubeApifyCsvError("environment must be a mapping (nothing was staged)")
    declared_environment["declared_by"] = "collection.adapters.youtube.apify_csv"

    return {
        "run_id": run_id,
        "study_id": study_id,
        "source_id": SOURCE_ID,
        "collector_id": COLLECTOR_ID,
        "purpose": purpose,
        "query": {"keyword": query_keyword, "query_id": query_id},
        "window": {
            "start": window_start,
            "end_exclusive": window_end_exclusive,
            "granularity": granularity,
            "timezone": timezone,
        },
        "collection_request": {
            "date_filter": date_filter,
            "reference_time": reference_time,
        },
        "temporal": {
            "collector_window_type": collector_window_type,
            "boundary_semantics": boundary_semantics,
            "exact_window_match": bool(exact_window_match),
            "limitations": [DATE_FILTER_SEPARATION_LIMITATION, *extra_limitations],
        },
        "timestamps": {
            "started_at": started_at,
            "finished_at": finished_at,
            "basis": timestamp_basis,
        },
        "execution": {
            "status": execution_status,
            "returned_count": returned_count,
            "errors": list(errors) if errors is not None else [],
        },
        "artifacts": [
            {
                "source": str(source),
                "path": filename,
                "artifact_type": ARTIFACT_TYPE,
                "format": ARTIFACT_FORMAT,
                "schema_id": ARTIFACT_SCHEMA_ID,
                "completeness": completeness,
                "record_count": record_count,
            }
        ],
        "environment": declared_environment,
    }


def build_declaration(runs, *, description: str | None = None) -> dict:
    """Wrap built run entries in a ``staging-declaration-v1`` document."""
    if not runs:
        raise YouTubeApifyCsvError("at least one built run is required")
    document = {
        "declaration_version": _DECLARATION_VERSION,
        "runs": list(runs),
    }
    if description is not None:
        document["description"] = description
    return document


def stage_csv(
    run: dict,
    *,
    declarations_dir,
    workspace_root,
    datasets_root,
    registries,
    declaration_name: str = "youtube-apify-csv-declaration.json",
    description: str | None = None,
) -> dict:
    """Stage one wrapper-built run through the existing declaration driver.

    The declaration is written to ``declarations_dir`` (caller-owned scratch
    space, never the workspace), structurally validated with
    :func:`load_declaration`, and staged with :func:`stage_declaration`:
    the CSV is copied byte-for-byte into ``.staging/<run-id>/`` and adoption
    itself stays the L1 gate's verdict (``adopt_staged``).  An existing
    ``run_id`` under ``.staging/`` / ``.quarantine/`` / the raw catalog
    stops the run with ``RUN_ID_ALREADY_EXISTS``; existing raw is never
    overwritten.
    """
    directory = Path(declarations_dir)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / declaration_name
    target.write_text(
        json.dumps(
            build_declaration([run], description=description),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    declaration = load_declaration(target)
    return stage_declaration(
        declaration,
        workspace_root=workspace_root,
        datasets_root=datasets_root,
        registries=registries,
    )