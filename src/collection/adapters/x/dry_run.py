"""X API v2 dry-run adapter (COL-016 safe slice).

Implements the :mod:`collection.core.contracts` shape so it is verified with
the same contract check as every other adapter, but the transport does not
exist yet: :meth:`XApiDryRunAdapter.collect` always returns a ``failed``
result (failure evidence, never zero observations) and
:meth:`XApiDryRunAdapter.extract_observations` returns no rows (per-post
records must never enter the repository, even anonymized — COL-030 §4.1).

Identity is a declared placeholder, not registry evidence: the ``x-api-v2``
collector is not in ``config/collectors.json`` (registering it is
``ISS-20261015-COL-031``), so there is no registry entry to bind to.  The
placeholder values below must equal the future registry entry when that
lands; until then this adapter is deliberately absent from
``collection.adapters._FACTORIES`` (registering a source that cannot collect
would imply an unevidenced capability).

Capabilities stay ``unknown`` across the board: nothing has been measured.
"""

from __future__ import annotations

from collection.adapters.x.request import plan_search_request
from collection.core.contracts import CollectionResult

__all__ = [
    "ADAPTER_ID",
    "COLLECTOR_ID",
    "SOURCE_ID",
    "VERSION",
    "XApiDryRunAdapter",
    "XDryRunError",
    "build_dry_run_adapter",
]

SOURCE_ID = "x"
#: Planned collector id (COL-031).  Not present in ``config/collectors.json``.
COLLECTOR_ID = "x-api-v2"
#: Placeholder identity — must match the registry entry once COL-031 lands.
ADAPTER_ID = "x-api-v2@1"
VERSION = "unregistered"

_CAPABILITIES = {
    "absolute_date_range": "unknown",
    "relative_date_range": "unknown",
    "language_filter": "unknown",
    "geo_filter": "unknown",
    "pagination": "unknown",
    "stable_item_id": "unknown",
}


class XDryRunError(ValueError):
    """An X dry-run input cannot be used (fail closed, nothing is sent)."""


class XApiDryRunAdapter:
    """Request-planning-only adapter for the planned X API v2 collector.

    Dry-run surface: :meth:`plan_request` compiles a collection plan into the
    request parameters (via :mod:`collection.adapters.x.request`) without
    touching the network.  :meth:`collect` refuses — live X requests are
    banned until the live-request control (COL-032) and request-only evidence
    (PRV-033) pass with explicit owner approval (COL-030 U2: live forbidden).
    """

    source_id = SOURCE_ID
    collector_id = COLLECTOR_ID
    adapter_id = ADAPTER_ID
    version = VERSION

    def capabilities(self) -> dict:
        """All ``unknown``: nothing has been measured (a copy is returned)."""
        return dict(_CAPABILITIES)

    def validate_plan(self, plan: dict) -> list:
        """Generic request checks; live parameters come from the plan."""
        violations: list[str] = []
        query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
        text = query.get("text")
        if not isinstance(text, str) or not text.strip():
            violations.append(
                "query.text is required (declared, never inferred from a payload)"
            )
        window = plan.get("window") if isinstance(plan.get("window"), dict) else {}
        if not window.get("start") or not window.get("end_exclusive"):
            violations.append("window.start and window.end_exclusive are required")
        return violations

    def plan_request(self, plan: dict, *, max_results: int | None = None) -> dict:
        """Compile ``plan`` into X API v2 request parameters (nothing sent)."""
        try:
            return plan_search_request(plan, max_results=max_results)
        except Exception as error:  # request facts are declared or refused
            raise XDryRunError(str(error)) from error

    def collect(self, plan: dict) -> CollectionResult:
        """Refuse: live X collection is banned (owner decision, COL-030 U2).

        The failure is recorded as evidence with ``completeness="missing"``;
        it is never converted into zero observations.
        """
        message = (
            "live X collection is not implemented and is currently banned: "
            "repository execution is limited to mock/dry-run until the "
            "live-request control (COL-032) and request-only evidence "
            "(PRV-033) pass with explicit owner approval (COL-030 U2)"
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
        """No row-level extraction: per-post records never enter the repo."""
        return []

    def describe_execution(self) -> dict:
        return {
            "collector_id": self.collector_id,
            "adapter_id": self.adapter_id,
            "collection_mode": "dry_run_only",
            "transport": "no live call is issued",
            "version": self.version,
        }


def build_dry_run_adapter() -> XApiDryRunAdapter:
    """Build the dry-run adapter (no registry binding: none exists yet)."""
    return XApiDryRunAdapter()
