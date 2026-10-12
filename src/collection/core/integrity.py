"""L1 Collection Integrity assembly for staged runs (G1 §11).

L1 = structure -> semantics -> missingness/completeness -> artifact
integrity, evaluated with the validation framework's own layers (no second
implementation, h.md §6):

1. ``validate_full`` (structure; structural failure short-circuits);
2. ``post_collection_gate`` (semantics + L1-06/07/09 + registry references);

Outcomes: ``catalog`` (adoptable) or ``quarantine`` (raw preserved, not
adopted).  Moving the staged directory is the pipeline's job; this module
only decides (P6-2: gates never move raw data).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from validation.gates import post_collection_gate
from validation.pipeline import validate_full
from validation.reporting import Issue
from validation.semantic import Registries

__all__ = ["L1Decision", "evaluate_l1"]


@dataclass
class L1Decision:
    action: str  # "catalog" | "quarantine"
    valid: bool
    issues: list[Issue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "gate": "L1",
            "action": self.action,
            "valid": self.valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def evaluate_l1(
    document: dict,
    *,
    registries: Registries | None = None,
    base_dir,
) -> L1Decision:
    """Evaluate L1 for a staged run document (read-only).

    ``base_dir`` is the run directory holding ``artifact_manifest.json``,
    the payload files and (for the target string only) the metadata file.
    """
    outcome = validate_full(
        document,
        schema_id="collection-run-v1",
        target=str(base_dir / "run_metadata.json"),
        registries=registries,
        base_dir=base_dir,
        verify_artifacts=False,
    )
    if not outcome.valid:
        # Structural failure short-circuits the semantic layer (P4-11).
        return L1Decision("quarantine", False, sorted(outcome.issues, key=lambda i: i.sort_key()))

    gate = post_collection_gate(
        document,
        registries=registries,
        base_dir=base_dir,
    )
    return L1Decision(gate.action, gate.passed, gate.issues)
