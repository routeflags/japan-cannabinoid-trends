"""Semantic validators (Phase 4).

Runs only after Cerberus structural validation succeeds (rollout plan P4-11;
rollout instruction §11: "Cerberusによる構造検証に成功した後、意味検証を
実行する").  The orchestration lives in ``validation.pipeline``; this module
provides the individual checks:
Functions
---------

- ``check_schema_version``      CV-20 / P3-2 (registry-managed versions)
- ``check_temporal_semantics``  CV-08 / P4-1 (ordering, timezone,
  week_start consistency, run start/finish ordering)
- ``check_execution_consistency`` P4-4 (status / errors / counts, completion
  evidence for the finalized profile)
- ``check_registry_references`` P4-2 (source/collector/query/study existence,
  adapter mismatch, registered-but-legacy distinction)
- ``check_missingness_consistency`` G1 L1-09 (zero observations vs missing
  data vs collection failure; raw evidence requirement for terminal runs)
- ``eligible_collectors`` / ``check_capability_gate`` P4-3 (a.md §9)
- ``scan_for_secrets``          P4-10 (detection only, never auto-removal)

Design rules
------------
- No Cerberus import: these checks consume plain dicts and never re-do
  structural validation.
- No mutation: checks are read-only (AGENTS.md Raw Data Rule).
- Issue messages never contain the offending value (h.md §14).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from validation.reporting import Issue, join_pointer
from validation.schema_registry import get_schema_version

__all__ = [
    "Registries",
    "check_capability_gate",
    "check_execution_consistency",
    "check_missingness_consistency",
    "check_registry_references",
    "check_schema_version",
    "check_temporal_semantics",
    "eligible_collectors",
    "scan_for_secrets",
]

#: Execution statuses that mean "this run is over" (the finalized profile
#: requires completion evidence for these; P3-1 / e.md §4.1).
TERMINAL_EXECUTION_STATUSES = ("success", "partial", "failed")

#: Field pairs that describe a half-open window (c.md §2 P2, G3 §4.1).
_WINDOW_PAIRS = (
    ("start", "end_exclusive"),
    ("requested_start", "requested_end_exclusive"),
)


def _parse_iso(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _issue(code, path, message, rule, severity="error", schema_version=""):
    return Issue(
        code=code,
        path=path,
        severity=severity,
        message=message,
        rule=rule,
        schema_version=schema_version,
    )


# ---------------------------------------------------------------------------
# CV-20 / P3-2: schema version management
# ---------------------------------------------------------------------------


def check_schema_version(document, schema_id: str) -> list[Issue]:
    """CV-20: the document's ``schema_version`` must match the registry's
    contract version for ``schema_id``.

    Absence is *not* reported here: the structural schema owns the required
    check and would have run first.  ``schema_id`` must be registered; the
    pipeline resolves it before calling this function.
    """
    expected = get_schema_version(schema_id)
    if not isinstance(document, dict):
        return []
    actual = document.get("schema_version")
    if actual is None:
        return []
    if actual == expected:
        return []
    return [
        _issue(
            "SCHEMA_VERSION_MISMATCH",
            "/schema_version",
            "document schema_version does not match the schema contract "
            f"version {expected}",
            "schema_version",
            schema_version=expected,
        )
    ]


# ---------------------------------------------------------------------------
# P4-1 / CV-08: temporal semantics
# ---------------------------------------------------------------------------


def _check_window_block(block: dict, path: str, issues: list[Issue]) -> None:
    """Ordering / timezone / granularity checks for one window-like block."""
    for start_key, end_key in _WINDOW_PAIRS:
        if start_key not in block and end_key not in block:
            continue
        start = block.get(start_key)
        end = block.get(end_key)
        if start is None or end is None:
            issues.append(
                _issue(
                    "TEMPORAL_BOUNDARY_MISSING",
                    join_pointer(path, start_key if start is None else end_key),
                    "temporal boundary is missing",
                    "temporal_order",
                )
            )
            continue
        start_dt = _parse_iso(start)
        end_dt = _parse_iso(end)
        if start_dt is None or end_dt is None:
            issues.append(
                _issue(
                    "DATETIME_INVALID",
                    join_pointer(path, start_key),
                    "window boundary is not a parseable ISO 8601 datetime",
                    "temporal_order",
                )
            )
            continue
        if start_dt.tzinfo is None or end_dt.tzinfo is None:
            issues.append(
                _issue(
                    "DATETIME_TIMEZONE_MISSING",
                    join_pointer(path, start_key),
                    "timezone is required for datetimes",
                    "temporal_order",
                )
            )
        elif start_dt >= end_dt:
            issues.append(
                _issue(
                    "TEMPORAL_ORDER_INVALID",
                    join_pointer(path, start_key),
                    f"{start_key} must be earlier than {end_key}",
                    "temporal_order",
                )
            )

    timezone = block.get("timezone")
    if isinstance(timezone, str) and timezone:
        try:
            ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError):
            issues.append(
                _issue(
                    "TIMEZONE_UNKNOWN",
                    join_pointer(path, "timezone"),
                    "timezone is not a known IANA timezone",
                    "temporal_timezone",
                )
            )

    granularity = block.get("granularity")
    week_start = block.get("week_start")
    if granularity == "week":
        if not week_start:
            issues.append(
                _issue(
                    "WEEK_START_REQUIRED",
                    join_pointer(path, "week_start"),
                    "week_start is required for week granularity",
                    "temporal_granularity",
                )
            )
    elif granularity in ("hour", "day", "month") and week_start:
        issues.append(
            _issue(
                "WEEK_START_UNEXPECTED",
                join_pointer(path, "week_start"),
                "week_start is set but the granularity is not weekly",
                "temporal_granularity",
                severity="warning",
            )
        )


def check_temporal_semantics(document) -> list[Issue]:
    """CV-08 / P4-1.

    Accepts three shapes and checks every temporal block it finds:

    - a standalone G3 window (``start`` / ``end_exclusive`` / ...);
    - a G5 ``temporal_provenance`` block (``requested_start`` /
      ``requested_end_exclusive`` / ...);
    - a full ``run_metadata.json`` document (top-level
      ``collection_started_at`` / ``collection_finished_at`` plus the nested
      ``temporal_provenance`` block).

    Checks: half-open ordering (start < end), timezone parseability (IANA),
    ``granularity`` / ``week_start`` consistency, and run-level
    ``collection_started_at`` <= ``collection_finished_at`` (G5-T08).
    """
    if not isinstance(document, dict):
        return []
    issues: list[Issue] = []

    _check_window_block(document, "", issues)

    nested = document.get("temporal_provenance")
    if isinstance(nested, dict):
        _check_window_block(nested, "/temporal_provenance", issues)

    started = document.get("collection_started_at")
    finished = document.get("collection_finished_at")
    if started is not None and finished is not None:
        started_dt = _parse_iso(started)
        finished_dt = _parse_iso(finished)
        if started_dt is None or finished_dt is None:
            issues.append(
                _issue(
                    "DATETIME_INVALID",
                    "/collection_finished_at",
                    "collection timestamps are not parseable ISO 8601 datetimes",
                    "temporal_order",
                )
            )
        elif started_dt.tzinfo is None or finished_dt.tzinfo is None:
            issues.append(
                _issue(
                    "DATETIME_TIMEZONE_MISSING",
                    "/collection_finished_at",
                    "timezone is required for datetimes",
                    "temporal_order",
                )
            )
        elif finished_dt < started_dt:
            issues.append(
                _issue(
                    "COLLECTION_FINISHED_BEFORE_START",
                    "/collection_finished_at",
                    "collection_finished_at must not be earlier than "
                    "collection_started_at",
                    "temporal_order",
                )
            )

    return issues


# ---------------------------------------------------------------------------
# P4-4: execution consistency
# ---------------------------------------------------------------------------


def check_execution_consistency(document) -> list[Issue]:
    """P4-4: status / errors / counts / pagination / completion evidence.

    Rules (e.md P09/P13, G5-T10, c.md G3-T12, rollout plan P3-1):

    - ``success`` with a non-empty ``errors`` list -> inconsistent;
    - ``failed`` with ``returned_count > 0`` -> inconsistent (P13/G5-T10 of the
      plan);
    - ``success`` with ``pagination_exhausted: false`` -> the run cannot claim
      completeness while page collection stopped early;
    - terminal status without ``collection_finished_at`` -> the finalized
      profile requires completion evidence.

    ``running`` runs are intentionally unconstrained here: their profile is
    ``collection-run-v1-running`` and the structural layer has already
    enforced the running-only shape.
    """
    if not isinstance(document, dict):
        return []
    execution = document.get("execution")
    if not isinstance(execution, dict):
        return []

    issues: list[Issue] = []
    status = execution.get("status")
    returned_count = execution.get("returned_count")
    errors = execution.get("errors")

    if status == "success" and errors:
        issues.append(
            _issue(
                "EXECUTION_ERRORS_ON_SUCCESS",
                "/execution/errors",
                "a successful run must not record errors",
                "execution_status",
            )
        )

    if status == "failed" and isinstance(returned_count, int) and returned_count > 0:
        issues.append(
            _issue(
                "EXECUTION_COUNT_ON_FAILURE",
                "/execution/returned_count",
                "a failed run must not report a positive returned_count",
                "execution_status",
            )
        )

    if status == "success" and execution.get("pagination_exhausted") is False:
        issues.append(
            _issue(
                "EXECUTION_PAGINATION_INCOMPLETE",
                "/execution/pagination_exhausted",
                "a successful run cannot be complete while pagination was "
                "not exhausted",
                "execution_completeness",
            )
        )

    if status in TERMINAL_EXECUTION_STATUSES and "collection_finished_at" not in document:
        issues.append(
            _issue(
                "COMPLETION_EVIDENCE_MISSING",
                "/collection_finished_at",
                "finalized runs require collection_finished_at",
                "completion_evidence",
            )
        )

    return issues


# ---------------------------------------------------------------------------
# G1 L1-09: missingness / completeness (zero vs missing vs failure)
# ---------------------------------------------------------------------------

_RAW_COMPLETENESS_INCOMPLETE = ("partial", "missing")


def check_missingness_consistency(document, manifest=None) -> list[Issue]:
    """G1 §11 L1-09 / AGENTS.md missing-data rules.

    Distinguishes observed zero, partial collection and collection failure:

    - a terminal run must have verifiable **raw artifact evidence** in its
      artifact manifest (a run that claims ``success`` / ``partial`` /
      ``failed`` without raw artifacts has no evidence to grade);
    - ``success`` with ``returned_count == 0`` is an *observed zero* only when
      an artifact declares ``record_count: 0``; otherwise the zero cannot be
      distinguished from missing data (fail closed);
    - ``success`` cannot coexist with raw artifacts marked ``partial`` /
      ``missing`` (the run must say ``partial`` instead);
    - ``failed`` requires recorded error evidence (a failure must not be
      silently converted into a zero-observation success).

    ``manifest`` is the parsed artifact manifest (``None`` when the run does
    not reference one or it cannot be read).  A missing manifest is reported
    here as evidence absence so that L1 refuses the run; callers that also
    verify the manifest file get both findings (they describe different
    problems: unreadable file vs unsubstantiated claim).

    Read-only: the document and manifest are never modified.
    """
    if not isinstance(document, dict):
        return []
    execution = document.get("execution")
    if not isinstance(execution, dict):
        return []
    status = execution.get("status")
    if status not in TERMINAL_EXECUTION_STATUSES:
        return []

    issues: list[Issue] = []

    artifacts = None
    if isinstance(manifest, dict) and isinstance(manifest.get("artifacts"), list):
        artifacts = [
            artifact
            for artifact in manifest["artifacts"]
            if isinstance(artifact, dict) and artifact.get("layer") == "raw"
        ]

    if not artifacts:
        issues.append(
            _issue(
                "MISSINGNESS_RAW_EVIDENCE_MISSING",
                "/artifact_manifest",
                "terminal run has no verifiable raw artifact evidence; "
                "a zero or failure claim requires preserved raw data",
                "collection_integrity",
            )
        )
    else:
        if status == "success" and any(
            artifact.get("completeness") in _RAW_COMPLETENESS_INCOMPLETE
            for artifact in artifacts
        ):
            issues.append(
                _issue(
                    "COMPLETENESS_INCONSISTENT_WITH_SUCCESS",
                    "/execution/status",
                    "a successful run cannot have partial or missing raw "
                    "artifacts; record the run as partial instead",
                    "collection_integrity",
                )
            )
        if (
            status == "success"
            and execution.get("returned_count") == 0
            and not any(artifact.get("record_count") == 0 for artifact in artifacts)
        ):
            issues.append(
                _issue(
                    "MISSINGNESS_ZERO_WITHOUT_EVIDENCE",
                    "/execution/returned_count",
                    "a zero observation is accepted only with an artifact "
                    "declaring record_count 0; a collection failure must not "
                    "be recorded as zero data",
                    "collection_integrity",
                )
            )

    if status == "failed" and not execution.get("errors"):
        issues.append(
            _issue(
                "COLLECTION_FAILED_WITHOUT_ERROR_EVIDENCE",
                "/execution/errors",
                "a failed run must record at least one error entry",
                "collection_integrity",
            )
        )

    return issues


# ---------------------------------------------------------------------------
# P4-2: registry references
# ---------------------------------------------------------------------------


def _find(items, key, value):
    for item in items:
        if isinstance(item, dict) and item.get(key) == value:
            return item
    return None


@dataclass(frozen=True)
class Registries:
    """Registry documents used for reference checks.

    Construct from registry documents (``config/sources.json`` etc.) or from
    explicit item tuples (tests).  Missing registries simply disable the
    corresponding checks; they never produce false failures.
    """

    sources: tuple = ()
    collectors: tuple = ()
    queries: tuple = ()
    query_variants: tuple = ()
    studies: tuple = ()
    #: G3 absolute window registry (``metadata/windows/*.json``).  An empty
    #: tuple means the registry is absent and the window-registry checks are
    #: disabled (repository convention: missing registries never produce
    #: false failures).
    windows: tuple = ()
    #: G4 artifact registry document (``metadata/artifacts/artifact-registry.json``).
    #: ``None`` disables the reader-dependent storage checks (S7/S8/S9) - the
    #: same convention as the other registries.
    artifact_registry: dict | None = None
    #: ``schema_version`` of the loaded query registry.  Stamped into new-run
    #: provenance (b.md §7) so a run records which registry definition version
    #: produced it.
    query_registry_version: str | None = None

    @classmethod
    def from_documents(
        cls,
        *,
        source_registry=None,
        collector_registry=None,
        query_registry=None,
        query_variants_registry=None,
        study_registry=None,
        window_documents=None,
        artifact_registry=None,
    ) -> "Registries":
        def items(document, key):
            if isinstance(document, dict) and isinstance(document.get(key), list):
                return tuple(document[key])
            return ()

        query_registry_version = None
        if isinstance(query_registry, dict) and isinstance(
            query_registry.get("schema_version"), str
        ):
            query_registry_version = query_registry["schema_version"]

        return cls(
            sources=items(source_registry, "sources"),
            collectors=items(collector_registry, "collectors"),
            queries=items(query_registry, "queries"),
            query_variants=items(query_variants_registry, "variant_sets"),
            studies=items(study_registry, "studies"),
            windows=tuple(window_documents or ()),
            artifact_registry=artifact_registry
            if isinstance(artifact_registry, dict)
            else None,
            query_registry_version=query_registry_version,
        )

    def any(self) -> bool:
        return bool(
            self.sources
            or self.collectors
            or self.queries
            or self.query_variants
            or self.studies
        )


_REGISTERED_HISTORICAL_STATUSES = ("legacy", "deprecated", "unverified")


def check_registry_references(document, registries: Registries) -> list[Issue]:
    """P4-2 / CV-05 / CV-06: source, collector, adapter, query, compound and
    study references must resolve in the provided registries.

    Registered-but-historical collectors/queries (``legacy`` / ``deprecated``
    / ``unverified`` / pending query status) are reported as ``info``: they
    remain valid provenance for past runs (a.md §7.3).
    """
    if not isinstance(document, dict) or not registries.any():
        return []
    issues: list[Issue] = []

    source_id = document.get("source_id")
    if registries.sources and isinstance(source_id, str):
        if _find(registries.sources, "source_id", source_id) is None:
            issues.append(
                _issue(
                    "REFERENCE_SOURCE_UNREGISTERED",
                    "/source_id",
                    "source_id is not registered in the source registry",
                    "registry_reference",
                )
            )

    collector = document.get("collector")
    collector_id = collector.get("collector_id") if isinstance(collector, dict) else None
    if registries.collectors and isinstance(collector_id, str):
        registered = _find(registries.collectors, "collector_id", collector_id)
        if registered is None:
            issues.append(
                _issue(
                    "REFERENCE_COLLECTOR_UNREGISTERED",
                    "/collector/collector_id",
                    "collector_id is not registered in the collector registry",
                    "registry_reference",
                )
            )
        else:
            if isinstance(source_id, str) and registered.get("source_id") not in (None, source_id):
                issues.append(
                    _issue(
                        "REFERENCE_COLLECTOR_SOURCE_MISMATCH",
                        "/collector/collector_id",
                        "registered collector belongs to a different source_id",
                        "registry_reference",
                    )
                )
            adapter_id = collector.get("adapter_id")
            registered_adapter = registered.get("adapter_id")
            if (
                isinstance(adapter_id, str)
                and isinstance(registered_adapter, str)
                and adapter_id != registered_adapter
            ):
                issues.append(
                    _issue(
                        "REFERENCE_ADAPTER_MISMATCH",
                        "/collector/adapter_id",
                        "adapter_id does not match the registered collector",
                        "registry_reference",
                    )
                )
            status = registered.get("status")
            if status in _REGISTERED_HISTORICAL_STATUSES:
                issues.append(
                    _issue(
                        "COLLECTOR_LEGACY_REFERENCE",
                        "/collector/collector_id",
                        f"collector is registered with status '{status}' "
                        "(historical reference allowed)",
                        "registry_reference",
                        severity="info",
                    )
                )
            elif status == "disabled":
                issues.append(
                    _issue(
                        "COLLECTOR_DISABLED_REFERENCE",
                        "/collector/collector_id",
                        "collector is disabled; only historical references are "
                        "expected",
                        "registry_reference",
                        severity="warning",
                    )
                )

    query_provenance = document.get("query_provenance")
    if registries.queries and isinstance(query_provenance, dict):
        query_id = query_provenance.get("query_id")
        if isinstance(query_id, str):
            registered_query = _find(registries.queries, "query_id", query_id)
            if registered_query is None:
                issues.append(
                    _issue(
                        "REFERENCE_QUERY_UNREGISTERED",
                        "/query_provenance/query_id",
                        "query_id is not registered in the query registry",
                        "registry_reference",
                    )
                )
            else:
                compound_id = query_provenance.get("compound_id")
                registered_compound = registered_query.get("compound_id")
                if (
                    isinstance(compound_id, str)
                    and isinstance(registered_compound, str)
                    and compound_id != registered_compound
                ):
                    issues.append(
                        _issue(
                            "REFERENCE_COMPOUND_MISMATCH",
                            "/query_provenance/compound_id",
                            "compound_id does not match the registered query",
                            "registry_reference",
                        )
                    )
                if registered_query.get("status") == "deprecated":
                    issues.append(
                        _issue(
                            "QUERY_DEPRECATED_REFERENCE",
                            "/query_provenance/query_id",
                            "query is registered as deprecated (historical "
                            "reference allowed)",
                            "registry_reference",
                            severity="info",
                        )
                    )

    study_id = document.get("study_id")
    if registries.studies and isinstance(study_id, str):
        if _find(registries.studies, "study_id", study_id) is None:
            issues.append(
                _issue(
                    "REFERENCE_STUDY_UNREGISTERED",
                    "/study_id",
                    "study_id is not registered in the study registry",
                    "registry_reference",
                )
            )

    return issues


# ---------------------------------------------------------------------------
# P4-3: capability gate (a.md §9)
# ---------------------------------------------------------------------------


def _requirement_keys(requirements) -> list[str]:
    if isinstance(requirements, dict):
        return list(requirements.keys())
    return list(requirements)


def eligible_collectors(source_id, requirements, registries: Registries) -> list[dict]:
    """a.md §9 reference implementation: active collectors of ``source_id``
    whose capabilities read ``supported`` for every requirement.

    An empty result means "stop the collection" (fail closed); the caller
    must never auto-select another collector (a.md §9).
    """
    keys = _requirement_keys(requirements)
    matches = []
    for collector in registries.collectors:
        if not isinstance(collector, dict):
            continue
        if collector.get("source_id") != source_id:
            continue
        if collector.get("status") != "active":
            continue
        capabilities = collector.get("capabilities") or {}
        if all(capabilities.get(key) == "supported" for key in keys):
            matches.append(collector)
    return matches


def check_capability_gate(
    source_id,
    requirements,
    registries: Registries,
    *,
    requested_collector_id=None,
) -> list[Issue]:
    """P4-3: refuse a collection when the source has no collector that can
    satisfy the requirements with verified (``supported``) capabilities.

    - a requested collector must be registered and ``active``;
    - ``unknown`` capability must never be auto-selected (it is not support);
    - without an explicit collector, at least one eligible collector must
      exist.
    """
    issues: list[Issue] = []
    keys = _requirement_keys(requirements)
    candidates = [
        collector
        for collector in registries.collectors
        if isinstance(collector, dict) and collector.get("source_id") == source_id
    ]
    if not candidates:
        issues.append(
            _issue(
                "GATE_NO_COLLECTOR_FOR_SOURCE",
                "/collector_id",
                "no collector is registered for this source_id",
                "capability_gate",
            )
        )
        return issues

    if requested_collector_id is not None:
        requested = _find(candidates, "collector_id", requested_collector_id)
        if requested is None:
            issues.append(
                _issue(
                    "GATE_COLLECTOR_UNREGISTERED",
                    "/collector_id",
                    "requested collector is not registered for this source_id",
                    "capability_gate",
                )
            )
            return issues
        if requested.get("status") != "active":
            issues.append(
                _issue(
                    "GATE_COLLECTOR_NOT_ACTIVE",
                    "/collector_id",
                    "requested collector is not active; collection refused",
                    "capability_gate",
                )
            )
        capabilities = requested.get("capabilities") or {}
        for key in keys:
            value = capabilities.get(key)
            if value == "supported":
                continue
            if value in ("unknown", None):
                # A missing capability entry is unverified, not unsupported:
                # the contract forbids inventing a capability state.
                issues.append(
                    _issue(
                        "GATE_CAPABILITY_UNKNOWN",
                        join_pointer("/capabilities", key),
                        "required capability is unverified (unknown); "
                        "automatic selection is not allowed",
                        "capability_gate",
                    )
                )
            else:
                issues.append(
                    _issue(
                        "GATE_CAPABILITY_UNSUPPORTED",
                        join_pointer("/capabilities", key),
                        "required capability is not supported",
                        "capability_gate",
                    )
                )
        return issues

    if not eligible_collectors(source_id, requirements, registries):
        issues.append(
            _issue(
                "GATE_NO_ELIGIBLE_COLLECTOR",
                "/collector_id",
                "no active collector satisfies the requirements; "
                "collection must stop (fail closed)",
                "capability_gate",
            )
        )
    return issues


# ---------------------------------------------------------------------------
# P4-10: secret scan (detection only)
# ---------------------------------------------------------------------------

_SECRET_KEY_NAMES = frozenset(
    {
        "token",
        "secret",
        "password",
        "passwd",
        "passphrase",
        "authorization",
        "auth",
        "bearer",
        "cookie",
        "session",
        "sessionid",
        "credentials",
        "credential",
        "privatekey",
        "secretkey",
        "clientsecret",
        "accesstoken",
        "refreshtoken",
        "apikey",
        "apitoken",
        "apisecret",
    }
)

_SECRET_KEY_SUFFIXES = (
    "token",
    "secret",
    "password",
    "passwd",
    "apikey",
    "apisecret",
    "privatekey",
    "credential",
)

_SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{16,}"),
)


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _is_secret_key(key: str) -> bool:
    normalized = _normalize_key(key)
    if not normalized:
        return False
    if normalized in _SECRET_KEY_NAMES:
        return True
    if normalized.startswith(("apikey", "apisecret")):
        return True
    return normalized.endswith(_SECRET_KEY_SUFFIXES)


def _has_content(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def scan_for_secrets(document) -> list[Issue]:
    """P4-10 / e.md P16 / G5-T14: detect credential-like fields or values.

    Detection only: this check never removes or rewrites anything (the
    storage decision "保存拒否" is made by the caller).  Messages never
    contain the offending value.
    """
    issues: list[Issue] = []

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                child = join_pointer(path, key)
                if isinstance(key, str) and _is_secret_key(key) and _has_content(value):
                    issues.append(
                        _issue(
                            "SECRET_DETECTED",
                            child,
                            "credential-like field with a non-empty value "
                            "(value omitted)",
                            "secret_scan",
                        )
                    )
                if isinstance(value, str):
                    for pattern in _SECRET_VALUE_PATTERNS:
                        if pattern.search(value):
                            issues.append(
                                _issue(
                                    "SECRET_DETECTED",
                                    child,
                                    "value looks like a credential token "
                                    "(value omitted)",
                                    "secret_scan",
                                )
                            )
                            break
                else:
                    walk(value, child)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                child = join_pointer(path, index)
                if isinstance(value, str):
                    for pattern in _SECRET_VALUE_PATTERNS:
                        if pattern.search(value):
                            issues.append(
                                _issue(
                                    "SECRET_DETECTED",
                                    child,
                                    "value looks like a credential token "
                                    "(value omitted)",
                                    "secret_scan",
                                )
                            )
                            break
                else:
                    walk(value, child)

    walk(document, "")
    return issues
