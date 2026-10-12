"""Storage policy, git tracking and publication gates (Phase 4, P4-7 / P4-9).

Contract sources
----------------
- G6 §6 (storage policy registry), §8 (git tracking validator + judgment
  table), §10 (publication eligibility gate / publication decision):
  ``docs/plans/20261013f.md``.

Git checks are read-only (f.md §8.1): ``git ls-files --error-unmatch`` and
``git check-ignore -v`` only.  Nothing is added, removed or committed.

The publication gate mirrors f.md §11: approval only counts when the decision
is ``approved``, targets the same artifact and records the same SHA-256.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from validation.reporting import Issue

__all__ = [
    "check_git_tracking",
    "check_publication",
    "git_ignored",
    "git_tracked",
    "select_policy",
]


def _issue(code, path, message, rule, severity="error"):
    return Issue(code=code, path=path, severity=severity, message=message, rule=rule)


# ---------------------------------------------------------------------------
# P4-7: git tracking validator (read-only)
# ---------------------------------------------------------------------------


def _run_git(root, args) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )


def git_tracked(root, path: str) -> bool:
    """True when the path is registered in the current git index."""
    result = _run_git(root, ["ls-files", "--error-unmatch", "--", path])
    return result.returncode == 0


def git_ignored(root, path: str) -> bool:
    """True when the exclude rules would ignore the path.

    ``--no-index`` makes the check purely rule-based: a path that is already
    tracked can still match an ignore rule (the rule just has no effect),
    and the policy check needs to see that combination (f.md §8: "既にGitへ
    登録済みのファイルには、通常``.gitignore``は効かない").  ``.gitignore`` alone
    is never trusted: ``git check-ignore`` is the authoritative check
    (f.md §8: "``.gitignore``に記載されていることだけをもって、追跡されていないと
    判断してはならない").
    """
    result = _run_git(root, ["check-ignore", "--no-index", "-q", "--", path])
    return result.returncode == 0


def check_git_tracking(root, entries, *, policies=None) -> list[Issue]:
    """f.md §8.3 judgment table applied to ``entries``.

    ``entries``: iterable of ``{"path": str, "expected": "tracked" |
    "ignored" | "conditional"}`` (or ``{"path": ..., "policy_id": ...}``
    when ``policies`` maps policy ids to expected git_tracking values).

    Outcomes:
    - expected ignored but tracked -> FAIL (G6-T04/G6-T05);
    - expected tracked but untracked -> FAIL;
    - expected conditional but tracked -> warning (additional review);
    - untracked but not ignored -> warning (G6-T06: future accidental adds).
    """
    issues: list[Issue] = []
    root = Path(root)
    policy_map = policies or {}

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not isinstance(path, str) or not path:
            continue
        expected = entry.get("expected")
        if expected is None and entry.get("policy_id") in policy_map:
            expected = policy_map[entry["policy_id"]]
        pointer = f"/entries/{index}"

        tracked = git_tracked(root, path)
        ignored = git_ignored(root, path)

        if expected == "ignored" and tracked:
            issues.append(
                _issue(
                    "GIT_POLICY_TRACKED_WHEN_IGNORED",
                    pointer,
                    "path is tracked although the policy requires it to be "
                    "ignored",
                    "git_tracking",
                )
            )
        elif expected == "tracked" and not tracked:
            issues.append(
                _issue(
                    "GIT_POLICY_UNTRACKED_WHEN_TRACKED",
                    pointer,
                    "path is expected to be tracked but is not in the index",
                    "git_tracking",
                )
            )
        elif expected == "conditional" and tracked:
            issues.append(
                _issue(
                    "GIT_POLICY_CONDITIONAL_REVIEW",
                    pointer,
                    "path is tracked under a conditional policy; "
                    "additional review required",
                    "git_tracking",
                    severity="warning",
                )
            )

        if not tracked and not ignored:
            issues.append(
                _issue(
                    "GIT_POLICY_UNIGNORED_UNTRACKED",
                    pointer,
                    "path is neither tracked nor ignored; an accidental add "
                    "is possible",
                    "git_tracking",
                    severity="warning",
                )
            )

    return issues


def select_policy(policy_registry, *, artifact_layer=None, source_kind=None):
    """Pick the policy for (artifact_layer, source_kind) from a registry doc.

    ``source_kind == "any"`` is a wildcard; an exact match wins over the
    wildcard.  Returns ``None`` when no policy covers the request.
    """
    if not isinstance(policy_registry, dict):
        return None
    policies = policy_registry.get("policies")
    if not isinstance(policies, list):
        return None
    exact = None
    wildcard = None
    for policy in policies:
        if not isinstance(policy, dict):
            continue
        if artifact_layer is not None and policy.get("artifact_layer") != artifact_layer:
            continue
        kind = policy.get("source_kind")
        if kind == source_kind:
            exact = policy
        elif kind == "any" and wildcard is None:
            wildcard = policy
    return exact or wildcard


# ---------------------------------------------------------------------------
# P4-9 / CV-11: publication gate (f.md §10/§11)
# ---------------------------------------------------------------------------

_PUBLICATION_CRITERIA = ("reviewed_at", "reviewer", "criteria_version", "artifact_sha256")


def can_publish(artifact: dict, decision: dict | None) -> bool:
    """f.md §11 minimal rule: approved + same artifact_id + same sha256."""
    if decision is None:
        return False
    if decision.get("status") != "approved":
        return False
    if decision.get("artifact_id") != artifact.get("artifact_id"):
        return False
    if decision.get("artifact_sha256") != artifact.get("sha256"):
        return False
    return True


def check_publication(artifact: dict, decision: dict | None) -> list[Issue]:
    """P4-9 / CV-11: publication eligibility for one artifact.

    Non-destructive: returns findings, performs no writes.  ``requires_review``
    and ``unknown`` are treated as "publication refused" (f.md §10.1), and an
    approval is invalidated by any artifact change ("Artifactの内容が変更された
    場合は、以前の承認を自動的に引き継がない").
    """
    issues: list[Issue] = []
    if not isinstance(artifact, dict):
        return [
            _issue(
                "PUBLICATION_ARTIFACT_INVALID",
                "/artifact",
                "artifact is not a mapping; publication refused",
                "publication_gate",
            )
        ]

    if decision is None:
        return [
            _issue(
                "PUBLICATION_DECISION_MISSING",
                "/decision",
                "no publication decision exists; publication refused",
                "publication_gate",
            )
        ]

    status = decision.get("status")
    if status != "approved":
        issues.append(
            _issue(
                "PUBLICATION_NOT_APPROVED",
                "/decision/status",
                f"publication decision status '{status}' does not permit "
                "publication",
                "publication_gate",
            )
        )
        # Even a non-approved decision is checked for basic identity drift,
        # but the status alone already refuses publication.
        return issues

    if decision.get("artifact_id") != artifact.get("artifact_id"):
        issues.append(
            _issue(
                "PUBLICATION_ARTIFACT_MISMATCH",
                "/decision/artifact_id",
                "decision targets a different artifact; approval does not "
                "transfer",
                "publication_gate",
            )
        )

    artifact_hash = artifact.get("sha256")
    decision_hash = decision.get("artifact_sha256")
    if isinstance(artifact_hash, str) and decision_hash != artifact_hash:
        issues.append(
            _issue(
                "PUBLICATION_HASH_MISMATCH",
                "/decision/artifact_sha256",
                "artifact content changed after approval; approval is not "
                "inherited",
                "publication_gate",
            )
        )

    for field in _PUBLICATION_CRITERIA:
        if decision.get(field) in (None, ""):
            issues.append(
                _issue(
                    "PUBLICATION_CRITERIA_MISSING",
                    f"/decision/{field}",
                    "an approved decision must record this review criterion",
                    "publication_gate",
                )
            )

    return issues
