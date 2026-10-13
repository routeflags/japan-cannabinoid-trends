"""G6 §10 publication eligibility gate (record-only, read-only).

Contract sources
----------------
- G6 instruction §10 (eligibility states, PUB-01..PUB-10) and §11
  (``can_publish`` minimal rule): ``docs/plans/20261013f.md``.
- AGENTS.md Publication Gate wins on any conflict.

Scope
-----
``evaluate_eligibility`` runs the ten §10.2 checks against one real
artifact and returns a record-only verdict:

- ``SUPPORTED`` - every check passes and an ``approved`` decision pins the
  exact artifact hash;
- ``CONDITIONAL`` - publication is not refused but reviewer action remains
  (warnings only);
- ``BLOCKED`` - at least one refusing check failed (fail closed, P5).

The gate never publishes, releases or registers a DOI.  A ``BLOCKED``
verdict records an artifact problem, never a gate failure.

The minimal §11 rule (approved + same artifact_id + same sha256) is reused
from ``validation.storage_policy`` (``can_publish`` / ``check_publication``);
secrets reuse ``validation.semantic.scan_for_secrets``.  ``cerberus`` is not
imported here (only ``validation.core`` may import it).
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from validation.semantic import scan_for_secrets
from validation.storage_policy import can_publish, check_publication

__all__ = ["PUB_CHECKS", "evaluate_eligibility"]

PUB_CHECKS = (
    ("PUB-01", "provenance exists"),
    ("PUB-02", "artifact integrity passes"),
    ("PUB-03", "publication schema valid"),
    ("PUB-04", "personal-data review"),
    ("PUB-05", "secret scan"),
    ("PUB-06", "source terms confirmed"),
    ("PUB-07", "redistribution conditions confirmed"),
    ("PUB-08", "copyright / contract constraints confirmed"),
    ("PUB-09", "anonymization / aggregation applied"),
    ("PUB-10", "publication approval recorded"),
)

_VERDICTS = ("SUPPORTED", "CONDITIONAL", "BLOCKED")


def _result(check_id: str, title: str, *, status: str, detail: str) -> dict:
    assert status in ("PASS", "WARNING", "FAIL")
    return {"id": check_id, "title": title, "status": status, "detail": detail}


def evaluate_eligibility(
    artifact: dict,
    decision: dict | None,
    *,
    evidence: dict | None = None,
) -> dict:
    """Evaluate §10.2 for one artifact (no writes, no publication)."""
    evidence = deepcopy(evidence) if isinstance(evidence, dict) else {}
    artifact = deepcopy(artifact) if isinstance(artifact, dict) else artifact
    decision = deepcopy(decision) if isinstance(decision, dict) else decision
    checks: list[dict] = []
    # PUB-01: provenance exists (run metadata / evidence reference supplied).
    if evidence.get("provenance_present") is True:
        checks.append(_result("PUB-01", PUB_CHECKS[0][1], status="PASS", detail="provenance reference supplied"))
    elif evidence.get("provenance_present") is False:
        checks.append(_result("PUB-01", PUB_CHECKS[0][1], status="FAIL", detail="provenance missing; publication refused"))
    else:
        checks.append(_result("PUB-01", PUB_CHECKS[0][1], status="WARNING", detail="provenance presence unknown; reviewer must confirm"))
    # PUB-02: artifact integrity (hash recorded and verifiable).
    integrity = evidence.get("integrity")
    if integrity == "verified":
        checks.append(_result("PUB-02", PUB_CHECKS[1][1], status="PASS", detail="artifact hash verified"))
    elif integrity == "failed":
        checks.append(_result("PUB-02", PUB_CHECKS[1][1], status="FAIL", detail="artifact integrity failed; publication refused"))
    else:
        checks.append(_result("PUB-02", PUB_CHECKS[1][1], status="WARNING", detail="integrity not verified in this slice; reviewer must confirm"))
    # PUB-03: publication schema valid (datapackage / schema review supplied).
    if evidence.get("schema_valid") is True:
        checks.append(_result("PUB-03", PUB_CHECKS[2][1], status="PASS", detail="publication schema reviewed"))
    elif evidence.get("schema_valid") is False:
        checks.append(_result("PUB-03", PUB_CHECKS[2][1], status="FAIL", detail="publication schema invalid; publication refused"))
    else:
        checks.append(_result("PUB-03", PUB_CHECKS[2][1], status="WARNING", detail="schema review not recorded; reviewer must confirm"))
    # PUB-04: personal-data review (must be reviewed before publication).
    if evidence.get("personal_data_reviewed") is True:
        checks.append(_result("PUB-04", PUB_CHECKS[3][1], status="PASS", detail="personal-data review recorded"))
    else:
        checks.append(_result("PUB-04", PUB_CHECKS[3][1], status="FAIL", detail="personal-data review missing; publication refused (G6-T11)"))
    # PUB-05: secret scan over the decision + evidence envelope (values never
    # emitted; secret-bearing artifacts are refused).
    secret_issues = []
    for document in (decision, evidence):
        if isinstance(document, dict):
            secret_issues.extend(scan_for_secrets(document))
    # Also scan the artifact descriptor itself (ids / hashes only; the gate
    # never reads raw record values).
    if isinstance(artifact, dict):
        secret_issues.extend(scan_for_secrets({"artifact_id": artifact.get("artifact_id"), "notes": artifact.get("notes", "")}))
    if secret_issues:
        checks.append(_result("PUB-05", PUB_CHECKS[4][1], status="FAIL", detail=f"secret scan found {len(secret_issues)} finding(s); publication refused (values omitted)"))
    else:
        checks.append(_result("PUB-05", PUB_CHECKS[4][1], status="PASS", detail="no credential-like fields or values in the review envelope"))
    # PUB-06..PUB-08: terms / redistribution / copyright confirmations.
    for index, key in ((5, "source_terms_confirmed"), (6, "redistribution_confirmed"), (7, "copyright_confirmed")):
        check_id, title = PUB_CHECKS[index]
        if evidence.get(key) is True:
            checks.append(_result(check_id, title, status="PASS", detail="confirmation recorded"))
        elif evidence.get(key) is False:
            checks.append(_result(check_id, title, status="FAIL", detail="confirmation explicitly missing; publication refused"))
        else:
            checks.append(_result(check_id, title, status="WARNING", detail="confirmation not recorded; reviewer must confirm"))
    # PUB-09: anonymization / aggregation for person-level sources.
    if evidence.get("anonymization_applied") is True:
        checks.append(_result("PUB-09", PUB_CHECKS[8][1], status="PASS", detail="anonymization / aggregation recorded"))
    elif evidence.get("anonymization_applied") is False:
        checks.append(_result("PUB-09", PUB_CHECKS[8][1], status="FAIL", detail="required anonymization missing; publication refused"))
    else:
        checks.append(_result("PUB-09", PUB_CHECKS[8][1], status="WARNING", detail="anonymization state unknown; reviewer must confirm"))
    # PUB-10: approval recorded and pinned to this exact artifact (§11).
    pub_issues = check_publication(artifact if isinstance(artifact, dict) else {}, decision)
    if isinstance(artifact, dict) and can_publish(artifact, decision):
        checks.append(_result("PUB-10", PUB_CHECKS[9][1], status="PASS", detail="approved decision pins this artifact hash"))
    elif decision is None:
        checks.append(_result("PUB-10", PUB_CHECKS[9][1], status="FAIL", detail="no publication decision; publication refused (G6-T07)"))
    else:
        codes = sorted({issue.code for issue in pub_issues})
        checks.append(_result("PUB-10", PUB_CHECKS[9][1], status="FAIL", detail=f"approval missing or invalid ({', '.join(codes) if codes else 'not approved'}); publication refused"))
    failed = [check for check in checks if check["status"] == "FAIL"]
    warned = [check for check in checks if check["status"] == "WARNING"]
    verdict = "BLOCKED" if failed else ("CONDITIONAL" if warned else "SUPPORTED")
    assert verdict in _VERDICTS
    artifact_id = artifact.get("artifact_id") if isinstance(artifact, dict) else None
    artifact_sha = artifact.get("sha256") if isinstance(artifact, dict) else None
    decision_id = decision.get("decision_id") if isinstance(decision, dict) else None
    return {
        "gate": "publication_eligibility",
        "criteria": "G6 §10.2 (PUB-01..PUB-10)",
        "artifact_id": artifact_id,
        "artifact_sha256": artifact_sha,
        "decision_id": decision_id,
        "verdict": verdict,
        "checks": checks,
        "failed": [check["id"] for check in failed],
        "warnings": [check["id"] for check in warned],
    }
