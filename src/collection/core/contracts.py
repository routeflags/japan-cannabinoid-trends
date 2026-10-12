"""Adapter contract for collection adapters (G1 §8).

Contract sources
----------------
- G1 §8.1 (TypeScript reference interface) and §8.2 (responsibilities):
  ``docs/plans/20261013a.md``.  The interface is *not* a language change
  instruction; this module implements the equivalent Python contract.

Every adapter implements:

- identity: ``adapter_id`` / ``source_id`` / ``collector_id`` / ``version``
  (G1 §5 identifier model; the collector registry is the record of truth and
  the pipeline cross-checks these against it);
- ``capabilities()``: three-valued support map (G1 §7.2).  The adapter
  reports what the *registry* records - it must never invent ``supported``;
- ``validate_plan(plan)``: adapter-specific plan validation (returns
  human-readable violation strings; the core turns them into issues);
- ``collect(plan)``: perform the request through the adapter's transport and
  return a :class:`CollectionResult` (raw payload + execution facts).
  Expected transport failures are recorded as ``status="failed"`` results,
  never converted into zero observations;
- ``extract_observations(raw)``: source-specific parsing of the raw payload
  into observation records (``{}``-based dicts; the extraction stays in the
  adapter because only the adapter knows the source schema);
- ``describe_execution()``: non-secret execution fingerprint recorded in the
  run environment (tool / version / transport / collection mode).

Not the adapter's job (G1 §8.2): comparability verdicts, research
interpretation, raw rewriting, publication permission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from validation.schemas.registries import CAPABILITY_VALUES

__all__ = [
    "ADAPTER_CONTRACT_VERSION",
    "SUPPORT_VALUES",
    "CollectionResult",
    "SourceAdapter",
    "TransportError",
    "check_adapter_contract",
]

#: Version of the adapter contract itself (identity / method set / result
#: shape).  Adapter implementations declare their own version separately.
ADAPTER_CONTRACT_VERSION = "1.0.0"

#: Three-valued capability vocabulary (G1 §7.2), reused from the registry
#: schema so the two can never drift.
SUPPORT_VALUES = tuple(CAPABILITY_VALUES)


class TransportError(Exception):
    """A transport call failed (network, rate limit, bad response).

    Adapters catch this and record a ``failed`` :class:`CollectionResult`:
    a collection failure is evidence, not zero observations.
    """


@dataclass
class CollectionResult:
    """Outcome of one ``collect`` call.

    ``raw`` is the payload to be preserved byte-for-byte as a raw artifact
    (JSON-serializable).  ``temporal`` carries the adapter's observed window
    facts (granularity / week_start / window type / observed bounds) that the
    provenance builder merges into ``temporal_provenance``.
    """

    raw: Any
    payload_filename: str = "payload.json"
    payload_schema_id: str = "raw-response-v1"
    artifact_type: str = "raw_response"
    status: str = "success"  # running | success | partial | failed (G5 enum)
    returned_count: int = 0
    errors: list = field(default_factory=list)
    pagination_exhausted: bool | None = True
    completeness: str = "complete"  # complete | partial | missing | unknown
    observations: list = field(default_factory=list)
    submitted_parameters: dict = field(default_factory=dict)
    temporal: dict = field(default_factory=dict)


@runtime_checkable
class SourceAdapter(Protocol):
    """The common contract every collection adapter implements (G1 §8.1)."""

    adapter_id: str
    source_id: str
    collector_id: str
    version: str

    def capabilities(self) -> dict:
        """Three-valued capability map (values from SUPPORT_VALUES)."""
        ...

    def validate_plan(self, plan: dict) -> list:
        """Adapter-specific violations of ``plan`` (empty list = OK)."""
        ...

    def collect(self, plan: dict) -> CollectionResult:
        """Run the request and return the raw payload + execution facts."""
        ...

    def extract_observations(self, raw) -> list:
        """Parse source-specific observations out of ``raw``."""
        ...

    def describe_execution(self) -> dict:
        """Non-secret execution fingerprint for the run environment."""
        ...


def check_adapter_contract(adapter) -> list[str]:
    """Mechanically verify the adapter contract (a.md §15: new adapters get
    the common Contract Test).

    Returns contract violations; an empty list means the adapter satisfies
    the interface shape.  This is a *shape* check: identity values are
    cross-checked against the registry by the pipeline, and capabilities are
    cross-checked against the collector registry by the pipeline.
    """
    violations: list[str] = []

    for attribute in ("adapter_id", "source_id", "collector_id", "version"):
        value = getattr(adapter, attribute, None)
        if not isinstance(value, str) or not value:
            violations.append(f"missing or empty attribute: {attribute}")

    for method in (
        "capabilities",
        "validate_plan",
        "collect",
        "extract_observations",
        "describe_execution",
    ):
        if not callable(getattr(adapter, method, None)):
            violations.append(f"missing method: {method}")

    if callable(getattr(adapter, "capabilities", None)):
        try:
            capabilities = adapter.capabilities()
        except Exception as error:  # noqa: BLE001 - contract check reports it
            violations.append(f"capabilities() raised: {error.__class__.__name__}")
        else:
            if not isinstance(capabilities, dict):
                violations.append("capabilities() must return a dict")
            else:
                for key, value in capabilities.items():
                    if value not in SUPPORT_VALUES:
                        violations.append(
                            f"capability {key!r} has invalid value {value!r} "
                            f"(allowed: {', '.join(SUPPORT_VALUES)})"
                        )
    return violations
