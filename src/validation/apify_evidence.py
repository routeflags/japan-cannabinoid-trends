"""Offline validation for the Apify cloud evidence request list (PRV-013).

The request list (``metadata/provenance/apify-cloud-evidence-requests.json``)
enumerates the adopted YouTube runs from the staging declaration and records,
per run, which cloud fields still need owner retrieval.  This module is
read-only and offline: it never calls Apify, Zenodo, GitHub or any other
external API.  It checks three things:

1. the request list covers exactly the declaration's runs (no invented or
dropped run IDs);
2. every required field is present with an honest status, and a field
marked ``missing`` carries a null value (no fabrication);
3. every non-null value is transcribed verbatim from the declaration
(no invented actor run IDs, dataset IDs, inputs, timestamps or URLs).

Collector capabilities are deliberately out of scope here: this milestone
must not promote them, and the contract test pins them as ``unknown`` /
``unverified`` separately.
"""

from __future__ import annotations

__all__ = [
    "AUDIT_VERSION",
    "REQUEST_SCHEMA_VERSION",
    "REQUIRED_FIELDS",
    "STATUSES",
    "audit_apify_evidence",
    "declaration_values",
    "validate_request_list",
]

REQUEST_SCHEMA_VERSION = "1.0.0"

#: Version of the read-only blocked-state report built by
#: :func:`audit_apify_evidence`.
AUDIT_VERSION = "1.0.0"

#: Cloud fields every adopted run must eventually evidence (task order).
REQUIRED_FIELDS = (
    "actor_run_id",
    "apify_dataset_id",
    "actor_input",
    "started_at",
    "finished_at",
    "status",
    "evidence_source",
)

#: Honest per-field states.  ``observed`` is reserved for the future closed
#: state (value corroborated against cloud evidence and registered); this
#: revision uses only ``pending`` and ``missing``.
STATUSES = ("pending", "missing", "observed")

#: Request-list field -> (declaration section, declaration key) for the
#: fields transcribed from the declaration.  ``None`` means the field has no
#: declaration counterpart and must stay null until the owner retrieves it.
_DECLARATION_MAP = {
    "actor_run_id": ("environment", "actor_run_id"),
    "apify_dataset_id": ("environment", "apify_dataset_id"),
    "actor_input": None,
    "started_at": ("timestamps", "started_at"),
    "finished_at": ("timestamps", "finished_at"),
    "status": ("execution", "status"),
    "evidence_source": None,
}


def declaration_values(declaration: dict) -> dict:
    """Map ``run_id`` -> ``{field: declared value}`` for the transcribed fields."""
    values: dict[str, dict] = {}
    runs = declaration.get("runs") if isinstance(declaration, dict) else None
    if not isinstance(runs, list):
        return values
    for run in runs:
        if not isinstance(run, dict):
            continue
        run_id = run.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            continue
        entry: dict = {}
        for field, location in _DECLARATION_MAP.items():
            if location is None:
                entry[field] = None
                continue
            section, key = location
            block = run.get(section)
            entry[field] = block.get(key) if isinstance(block, dict) else None
        values[run_id] = entry
    return values


def validate_request_list(requests_document: dict, declaration: dict) -> list[str]:
    """Validate the request list against the declaration (read-only)."""
    violations: list[str] = []
    if not isinstance(requests_document, dict):
        return ["request list is not a JSON object"]
    if requests_document.get("schema_version") != REQUEST_SCHEMA_VERSION:
        violations.append(
            f"schema_version must be {REQUEST_SCHEMA_VERSION!r}"
        )
    declared = declaration_values(declaration)
    if not declared:
        violations.append("declaration carries no runs to enumerate")
        return violations
    requests = requests_document.get("requests")
    if not isinstance(requests, list):
        return violations + ["requests must be a list, one entry per adopted run"]
    seen: list[str] = []
    for index, request in enumerate(requests):
        prefix = f"/requests/{index}"
        if not isinstance(request, dict):
            violations.append(f"{prefix} is not an object")
            continue
        run_id = request.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            violations.append(f"{prefix}/run_id is required")
            continue
        seen.append(run_id)
        if run_id not in declared:
            violations.append(
                f"{prefix}/run_id {run_id!r} is not in the source declaration "
                "(run IDs are never invented)"
            )
            continue
        fields = request.get("fields")
        if not isinstance(fields, list):
            violations.append(f"{prefix}/fields must be a list")
            continue
        by_name = {
            item.get("field"): item
            for item in fields
            if isinstance(item, dict) and isinstance(item.get("field"), str)
        }
        for required in REQUIRED_FIELDS:
            item_prefix = f"{prefix}/fields/{required}"
            item = by_name.get(required)
            if item is None:
                violations.append(f"{item_prefix} is required")
                continue
            if item.get("required") is not True:
                violations.append(f"{item_prefix}/required must be true")
            status = item.get("status")
            if status not in STATUSES:
                violations.append(
                    f"{item_prefix}/status must be one of {sorted(STATUSES)}"
                )
                continue
            value = item.get("value")
            if status == "missing" and value is not None:
                violations.append(
                    f"{item_prefix}/value must be null while status is 'missing' "
                    "(unknown external values are never filled)"
                )
            if status in ("pending", "observed"):
                expected = declared[run_id].get(required)
                if expected is None:
                    violations.append(
                        f"{item_prefix}/value has no declaration counterpart; "
                        "it must stay missing (null) until the owner retrieves it"
                    )
                elif value != expected:
                    violations.append(
                        f"{item_prefix}/value does not match the declaration "
                        "(values are transcribed, never invented)"
                    )
    if sorted(seen) != sorted(declared):
        missing = sorted(set(declared) - set(seen))
        extra = sorted(set(seen) - set(declared))
        if missing:
            violations.append(
                "request list omits declaration runs: " + ", ".join(missing)
            )
        if extra:
            violations.append(
                "request list invents runs outside the declaration: " + ", ".join(extra)
            )
    # No URLs are fabricated: evidence_source has no declaration counterpart,
    # so every entry must still be missing/null in this revision.
    for index, request in enumerate(requests):
        if not isinstance(request, dict):
            continue
        for item in request.get("fields") or []:
            if (
                isinstance(item, dict)
                and item.get("field") == "evidence_source"
                and item.get("value") is not None
            ):
                violations.append(
                    f"/requests/{index}/fields/evidence_source/value must stay "
                    "null until the owner records a retrieval (no URLs invented)"
                )
    return violations


def audit_apify_evidence(requests_document: dict, declaration: dict) -> dict:
    """Build the read-only blocked-state report for the request list.

    The report is the machine-readable form of the PRV-013 owner checklist:
    per adopted run, which cloud fields are ``pending`` (transcribed from the
    declaration, still awaiting cloud corroboration) and which are ``missing``
    (no value anywhere in the repository, owner retrieval required).  It is
    derived entirely from the two committed documents, so the checklist the
    owner works from cannot drift from the validated request list.

    Honesty, not completeness, decides the verdict: ``violations`` is empty
    exactly when the list transcribes the declaration without invention.
    ``cloud_evidence_obtained`` stays false until every required field of
    every run reaches ``observed`` (corroborated against cloud evidence and
    registered), and ``collector_promotion_allowed`` follows it, so neither
    this milestone nor any caller can promote collector capabilities early.
    """
    violations = validate_request_list(requests_document, declaration)
    blocked: list[dict] = []
    pending_count = 0
    missing_count = 0
    observed_count = 0
    run_count = 0
    requests = (
        requests_document.get("requests")
        if isinstance(requests_document, dict)
        else None
    )
    if isinstance(requests, list):
        for request in requests:
            if not isinstance(request, dict):
                continue
            run_count += 1
            fields = request.get("fields")
            items = (
                [item for item in fields if isinstance(item, dict)]
                if isinstance(fields, list)
                else []
            )
            pending = sorted(
                item["field"]
                for item in items
                if item.get("status") == "pending"
                and isinstance(item.get("field"), str)
            )
            missing = sorted(
                item["field"]
                for item in items
                if item.get("status") == "missing"
                and isinstance(item.get("field"), str)
            )
            observed = sorted(
                item["field"]
                for item in items
                if item.get("status") == "observed"
                and isinstance(item.get("field"), str)
            )
            pending_count += len(pending)
            missing_count += len(missing)
            observed_count += len(observed)
            blocked.append(
                {
                    "run_id": request.get("run_id"),
                    "pending": pending,
                    "missing": missing,
                    "observed": observed,
                }
            )
    cloud_evidence_obtained = (
        not violations
        and run_count > 0
        and missing_count == 0
        and pending_count == 0
        and observed_count == run_count * len(REQUIRED_FIELDS)
    )
    return {
        "audit_version": AUDIT_VERSION,
        "issue": (
            requests_document.get("issue")
            if isinstance(requests_document, dict)
            else None
        ),
        "collector_id": (
            requests_document.get("collector_id")
            if isinstance(requests_document, dict)
            else None
        ),
        "run_count": run_count,
        "violations": violations,
        "blocked": blocked,
        "pending_count": pending_count,
        "missing_count": missing_count,
        "observed_count": observed_count,
        "cloud_evidence_obtained": cloud_evidence_obtained,
        # Capability promotion is gated on corroborated, registered cloud
        # evidence; while any field is pending/missing this is False.
        "collector_promotion_allowed": cloud_evidence_obtained,
    }
