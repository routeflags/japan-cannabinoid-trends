"""Common-scale comparison declarations and gates (ISS-20261105-GT-030).

Why this exists
---------------
A Google Trends single-term series is normalized to its own peak (0-100), so
two compounds measured in separate ``interest_over_time`` calls cannot be
compared: a value of 30 in one series and 60 in another says nothing about
their relative demand.  A ``compare_terms`` request measures several terms on
one shared scale and is therefore the only Google Trends measurement that can
support a cross-compound comparison.

That property is not automatic: the request must contain the study's declared
anchors (for this study CBD and THC), and the compared sets must share the
request conditions (geo / timeframe / window / locale).  The study declares
the rule in ``datasets/<study>/metadata/query-design.json`` under
``comparison_scales``; a plan repeats the declaration in its ``comparison``
block so a run can be checked after the fact.

Three layers, one rule
----------------------
- ``check_comparison_design``: the study declaration is well formed, its
  anchor query ids resolve, and the declared request conditions are
  consistent (run by the design gate and the audit).
- ``check_plan_comparison``: before collection.  A common-scale plan must
  declare the anchors and include them in the same ``compare_terms`` request;
  geo / timeframe / window / locale must match the study policy; a multi-term
  plan without a declaration is refused (fail closed).  A single-series plan
  stays allowed but is marked non-comparable.
- ``check_run_comparison``: after collection / at adoption.  A declared run
  must carry the anchors in both the recorded request and the comparison
  artifact, and the recorded geo / timeframe / window / locale must match the
  declaration.  An undeclared comparison-shaped run is a legacy warning (raw
  is never rejected or rewritten for being old) and is reported as
  ``legacy_undeclared`` by the audit.

Historical runs
---------------
Runs collected before this rule carry no ``comparison`` block.  They are not
backfilled (AGENTS.md raw data rule) and are never treated as newly compliant.
The audit separates them by what can still be concluded: a run whose request
conditions match the policy but lacks an anchor is ``legacy_missing_anchor`` and
is not comparable; a run whose conditions match and whose anchors are present is
``legacy_undeclared_anchored`` (comparable, but undeclared) and, when it
substantively covers a compound, counts as ``legacy_covered`` rather than
``complete``; a run on another geo / timeframe / window is ``legacy_out_of_scope``
and is neither comparable nor missing for this policy.

The module is source-agnostic: a policy names its source, anchors and request
constraints; another study or source can declare its own anchors in the same
shape.  The Google Trends specifics (the comparison artifact shape) are read
only through the recorded artifact, never assumed from the source name.
"""

from __future__ import annotations

import json
from pathlib import Path

from validation.reporting import Issue
from validation.schemas.comparison import (
    COMMON_SCALE,
    COMPARISON_SCALES,
    SINGLE_SERIES,
)
from validation.windows import find_window

__all__ = [
    "AUDIT_VERSION",
    "COMPARISON_POLICIES_KEY",
    "build_comparison_scale_audit",
    "check_comparison_design",
    "check_plan_comparison",
    "check_run_comparison",
    "load_study_comparison_policies",
]

AUDIT_VERSION = "1.0.0"

#: Top-level key of the study declaration (``query-design.json``).
COMPARISON_POLICIES_KEY = "comparison_scales"

_RULE = "comparison_scale"

#: Run statuses used by the audit.  ``legacy_*`` statuses never mean the run
#: is invalid; they mean it predates the declaration and cannot claim the new
#: contract (AGENTS.md: do not rewrite historical records).
STATUS_COMPLIANT = "compliant"
STATUS_INCOMPLETE = "incomplete"
STATUS_LEGACY_ANCHORED = "legacy_undeclared_anchored"
STATUS_LEGACY_MISSING_ANCHOR = "legacy_missing_anchor"
STATUS_LEGACY_UNKNOWN = "legacy_unknown"
STATUS_LEGACY_OUT_OF_SCOPE = "legacy_out_of_scope"
STATUS_SINGLE_SERIES = "single_series"
STATUS_UNREADABLE = "unreadable"

_LEGACY_COMPARISON_STATUSES = (
    STATUS_LEGACY_ANCHORED,
    STATUS_LEGACY_MISSING_ANCHOR,
    STATUS_LEGACY_UNKNOWN,
    STATUS_LEGACY_OUT_OF_SCOPE,
)


def _issue(code, path, message, severity="error", rule=_RULE):
    return Issue(code=code, path=path, severity=severity, message=message, rule=rule)


def _load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _strings(value):
    """A list of non-empty strings, or ``None`` when the value is not a list."""

    if not isinstance(value, list):
        return None
    return [item for item in value if isinstance(item, str) and item]


def _query_index(queries):
    index = {}
    for query in queries or ():
        if isinstance(query, dict) and isinstance(query.get("query_id"), str):
            index[query["query_id"]] = query
    return index


def _term_index(queries, query_variants):
    """Map an exact query text (canonical or variant) to its query entry."""

    index = {}
    by_id = _query_index(queries)
    for query in queries or ():
        if not isinstance(query, dict):
            continue
        text = query.get("canonical_text")
        if isinstance(text, str) and text and text not in index:
            index[text] = query
    for block in query_variants or ():
        if not isinstance(block, dict):
            continue
        base = by_id.get(block.get("query_id"))
        if base is None:
            continue
        for variant in block.get("variants") or ():
            if not isinstance(variant, dict):
                continue
            text = variant.get("text")
            if isinstance(text, str) and text and text not in index:
                index[text] = base
    return index


def _policies_from_document(document):
    if not isinstance(document, dict):
        return []
    policies = document.get(COMPARISON_POLICIES_KEY)
    if not isinstance(policies, list):
        return []
    return [policy for policy in policies if isinstance(policy, dict)]


def _policy_anchors(policy):
    return (
        _strings(policy.get("anchor_query_ids")) or [],
        _strings(policy.get("anchor_terms")) or [],
    )


def _request_block(policy):
    request = policy.get("request")
    return request if isinstance(request, dict) else {}


def _is_common_scale(policy):
    return policy.get("comparison_scale") == COMMON_SCALE


# ---------------------------------------------------------------------------
# Study declaration
# ---------------------------------------------------------------------------


def _check_policy(
    policy, index, *, queries, query_variants, windows, seen_ids
) -> list[Issue]:
    prefix = f"/{COMPARISON_POLICIES_KEY}/{index}"
    issues: list[Issue] = []

    scale_id = policy.get("scale_id")
    if not isinstance(scale_id, str) or not scale_id:
        issues.append(
            _issue(
                "COMPARISON_POLICY_ID_MISSING",
                f"{prefix}/scale_id",
                "comparison policy needs a non-empty scale_id",
            )
        )
    elif scale_id in seen_ids:
        issues.append(
            _issue(
                "COMPARISON_POLICY_ID_DUPLICATE",
                f"{prefix}/scale_id",
                "scale_id is declared more than once",
            )
        )
    else:
        seen_ids.add(scale_id)

    if not isinstance(policy.get("source_id"), str) or not policy.get("source_id"):
        issues.append(
            _issue(
                "COMPARISON_POLICY_SOURCE_MISSING",
                f"{prefix}/source_id",
                "comparison policy needs a non-empty source_id",
            )
        )

    mode = policy.get("comparison_scale")
    if mode not in COMPARISON_SCALES:
        issues.append(
            _issue(
                "COMPARISON_SCALE_INVALID",
                f"{prefix}/comparison_scale",
                "comparison_scale is not a declared comparison scale",
            )
        )

    for field_name in ("rationale", "decided", "decided_by"):
        if not isinstance(policy.get(field_name), str) or not policy.get(field_name):
            issues.append(
                _issue(
                    "COMPARISON_POLICY_DECISION_MISSING",
                    f"{prefix}/{field_name}",
                    "a canonical comparison policy records its rationale and "
                    "decision (rationale / decided / decided_by)",
                )
            )

    anchor_ids, anchor_terms = _policy_anchors(policy)
    request = _request_block(policy)
    if mode == SINGLE_SERIES:
        if anchor_ids or anchor_terms:
            issues.append(
                _issue(
                    "COMPARISON_POLICY_ANCHORS_ON_SINGLE_SERIES",
                    f"{prefix}/anchor_terms",
                    "a single_series policy cannot declare common-scale anchors",
                )
            )
    elif mode == COMMON_SCALE:
        if not anchor_ids:
            issues.append(
                _issue(
                    "COMPARISON_ANCHOR_SET_INCOMPLETE",
                    f"{prefix}/anchor_query_ids",
                    "a common_scale policy declares at least one anchor query",
                )
            )
        if not anchor_terms:
            issues.append(
                _issue(
                    "COMPARISON_ANCHOR_SET_INCOMPLETE",
                    f"{prefix}/anchor_terms",
                    "a common_scale policy declares the required anchor terms",
                )
            )

    resolved_anchor_terms = []
    anchor_languages = set()
    query_index = _query_index(queries)
    for position, anchor_id in enumerate(anchor_ids):
        entry = query_index.get(anchor_id)
        if queries and entry is None:
            issues.append(
                _issue(
                    "COMPARISON_ANCHOR_QUERY_UNREGISTERED",
                    f"{prefix}/anchor_query_ids/{position}",
                    "anchor query id is not registered in the query registry",
                )
            )
            continue
        if entry is None:
            continue
        canonical = entry.get("canonical_text")
        if not isinstance(canonical, str) or canonical not in anchor_terms:
            issues.append(
                _issue(
                    "COMPARISON_ANCHOR_TERM_UNDECLARED",
                    f"{prefix}/anchor_terms",
                    "an anchor query's canonical_text is not among the declared "
                    "anchor terms",
                )
            )
        else:
            resolved_anchor_terms.append(canonical)
        language = entry.get("language")
        if isinstance(language, str) and language:
            anchor_languages.add(language)

    if len(anchor_languages) > 1:
        issues.append(
            _issue(
                "COMPARISON_LOCALE_MISMATCH",
                f"{prefix}/anchor_query_ids",
                "anchor queries do not share one locale",
            )
        )
    declared_locale = request.get("locale")
    if declared_locale and anchor_languages and declared_locale not in anchor_languages:
        issues.append(
            _issue(
                "COMPARISON_LOCALE_MISMATCH",
                f"{prefix}/request/locale",
                "declared locale does not match the anchor query locale",
            )
        )
    if queries and resolved_anchor_terms and set(resolved_anchor_terms) != set(anchor_terms):
        issues.append(
            _issue(
                "COMPARISON_ANCHOR_TERM_UNDECLARED",
                f"{prefix}/anchor_terms",
                "anchor terms do not correspond exactly to the anchor queries",
            )
        )

    if "request" in policy and not isinstance(policy.get("request"), dict):
        issues.append(
            _issue(
                "COMPARISON_REQUEST_FIELD_INVALID",
                f"{prefix}/request",
                "request must be an object when declared",
            )
        )
    for field_name in ("tool", "geo", "locale", "timeframe", "window_id"):
        value = request.get(field_name)
        if value is not None and (not isinstance(value, str) or not value):
            issues.append(
                _issue(
                    "COMPARISON_REQUEST_FIELD_INVALID",
                    f"{prefix}/request/{field_name}",
                    "request constraint must be a non-empty string when declared",
                )
            )
    window_id = request.get("window_id")
    if isinstance(window_id, str) and window_id and windows:
        if find_window(windows, window_id) is None:
            issues.append(
                _issue(
                    "COMPARISON_WINDOW_UNREGISTERED",
                    f"{prefix}/request/window_id",
                    "declared window_id is not registered in metadata/windows",
                )
            )

    compound_set = policy.get("compound_set")
    if compound_set is not None:
        if not isinstance(compound_set, dict):
            issues.append(
                _issue(
                    "COMPARISON_COMPOUND_SET_INVALID",
                    f"{prefix}/compound_set",
                    "compound_set must be an object when declared",
                )
            )
        else:
            if not isinstance(compound_set.get("authority"), str) or not compound_set.get("authority"):
                issues.append(
                    _issue(
                        "COMPARISON_COMPOUND_SET_INVALID",
                        f"{prefix}/compound_set/authority",
                        "compound_set records the authority that defines the "
                        "required compounds",
                    )
                )
            excluded_compounds = compound_set.get("excluded_compound_ids")
            if excluded_compounds is not None and not isinstance(excluded_compounds, list):
                issues.append(
                    _issue(
                        "COMPARISON_COMPOUND_SET_INVALID",
                        f"{prefix}/compound_set/excluded_compound_ids",
                        "excluded_compound_ids must be a list when declared",
                    )
                )
            known_compounds = {
                query.get("compound_id")
                for query in queries or ()
                if isinstance(query, dict) and query.get("compound_id")
            }
            for position, item in enumerate(excluded_compounds or ()):
                if not isinstance(item, dict) or not isinstance(item.get("compound_id"), str) or not item.get("compound_id"):
                    issues.append(
                        _issue(
                            "COMPARISON_COMPOUND_SET_INVALID",
                            f"{prefix}/compound_set/excluded_compound_ids/{position}",
                            "an exclusion names a compound_id",
                        )
                    )
                    continue
                if not isinstance(item.get("reason"), str) or not item.get("reason"):
                    issues.append(
                        _issue(
                            "COMPARISON_COMPOUND_SET_INVALID",
                            f"{prefix}/compound_set/excluded_compound_ids/{position}/reason",
                            "an exclusion records why the compound is left out",
                        )
                    )
                if queries and item["compound_id"] not in known_compounds:
                    issues.append(
                        _issue(
                            "COMPARISON_COMPOUND_QUERY_UNREGISTERED",
                            f"{prefix}/compound_set/excluded_compound_ids/{position}/compound_id",
                            "excluded compound is not present in the query registry",
                        )
                    )
            excluded = compound_set.get("excluded_query_ids")
            if excluded is not None and not isinstance(excluded, list):
                issues.append(
                    _issue(
                        "COMPARISON_COMPOUND_SET_INVALID",
                        f"{prefix}/compound_set/excluded_query_ids",
                        "excluded_query_ids must be a list when declared",
                    )
                )
            for position, item in enumerate(excluded or ()):
                if not isinstance(item, dict) or not isinstance(item.get("query_id"), str) or not item.get("query_id"):
                    issues.append(
                        _issue(
                            "COMPARISON_COMPOUND_SET_INVALID",
                            f"{prefix}/compound_set/excluded_query_ids/{position}",
                            "an exclusion names a query_id",
                        )
                    )
                    continue
                if not isinstance(item.get("reason"), str) or not item.get("reason"):
                    issues.append(
                        _issue(
                            "COMPARISON_COMPOUND_SET_INVALID",
                            f"{prefix}/compound_set/excluded_query_ids/{position}/reason",
                            "an exclusion records why the compound is left out",
                        )
                    )
                if queries and item["query_id"] not in query_index:
                    issues.append(
                        _issue(
                            "COMPARISON_COMPOUND_QUERY_UNREGISTERED",
                            f"{prefix}/compound_set/excluded_query_ids/{position}/query_id",
                            "excluded query id is not registered in the query registry",
                        )
                    )

    return issues


def check_comparison_design(
    document, *, queries=(), query_variants=(), windows=()
) -> list[Issue]:
    """Validate the study's ``comparison_scales`` declaration (read-only)."""

    if not isinstance(document, dict):
        return [
            _issue(
                "COMPARISON_DESIGN_INVALID",
                "",
                "comparison design is not a JSON object",
            )
        ]
    policies = document.get(COMPARISON_POLICIES_KEY)
    if policies is None:
        return []
    if not isinstance(policies, list):
        return [
            _issue(
                "COMPARISON_DESIGN_INVALID",
                f"/{COMPARISON_POLICIES_KEY}",
                "comparison_scales must be a list",
            )
        ]
    issues: list[Issue] = []
    seen_ids: set[str] = set()
    for index, policy in enumerate(policies):
        if not isinstance(policy, dict):
            issues.append(
                _issue(
                    "COMPARISON_DESIGN_INVALID",
                    f"/{COMPARISON_POLICIES_KEY}/{index}",
                    "each comparison policy must be an object",
                )
            )
            continue
        issues.extend(
            _check_policy(
                policy,
                index,
                queries=queries,
                query_variants=query_variants,
                windows=windows,
                seen_ids=seen_ids,
            )
        )
    return issues


def load_study_comparison_policies(
    datasets_root, study_id, *, queries=(), query_variants=(), windows=()
):
    """Load and validate ``<study>/metadata/query-design.json`` policies.

    Returns ``(policies, issues)``.  A study without a design file yields
    ``([], [])`` (the generic rule then rests on the plan's own declaration).
    A malformed file raises ``ValueError`` so the caller can map it to a
    configuration error; an invalid declaration yields error-severity issues
    and no policies (fail closed).
    """

    if not isinstance(study_id, str) or not study_id:
        return [], []
    path = Path(datasets_root) / study_id / "metadata" / "query-design.json"
    if not path.is_file():
        return [], []
    document = _load_json(path)
    if not isinstance(document, dict):
        raise ValueError(f"query design cannot be read as JSON: {path}")
    if document.get("study_id") != study_id:
        raise ValueError(
            f"query design study_id does not match {study_id!r}: {path}"
        )
    issues = check_comparison_design(
        document,
        queries=queries,
        query_variants=query_variants,
        windows=windows,
    )
    if any(issue.severity == "error" for issue in issues):
        return [], issues
    return _policies_from_document(document), issues


# ---------------------------------------------------------------------------
# Pre-collection plan checks
# ---------------------------------------------------------------------------


def _policy_matches_plan(policy, plan):
    request = _request_block(policy)
    query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
    window = plan.get("window") if isinstance(plan.get("window"), dict) else {}
    if request.get("geo") and query.get("geo") != request["geo"]:
        return False
    if request.get("timeframe") and query.get("timeframe") != request["timeframe"]:
        return False
    if request.get("window_id") and window.get("window_id") != request["window_id"]:
        return False
    return True


def _select_policy(plan, policies, issues):
    """Resolve the policy a plan is declaring, or record why it cannot."""

    comparison = plan.get("comparison")
    source_id = plan.get("source_id")
    source_policies = [
        policy
        for policy in policies
        if policy.get("source_id") == source_id and _is_common_scale(policy)
    ]
    policy_id = comparison.get("policy_id") if isinstance(comparison, dict) else None
    if policy_id:
        if not policies:
            # No study declaration was supplied: the plan's own anchors remain
            # the rule.  A declared policy id is a cross-check, so it is only
            # resolved when the caller loaded the declaration.
            return None
        matches = [policy for policy in policies if policy.get("scale_id") == policy_id]
        if len(matches) != 1:
            issues.append(
                _issue(
                    "COMPARISON_POLICY_UNKNOWN",
                    "/comparison/policy_id",
                    "policy_id does not resolve to exactly one declared comparison "
                    "policy",
                )
            )
            return None
        policy = matches[0]
        if policy.get("source_id") != source_id:
            issues.append(
                _issue(
                    "COMPARISON_POLICY_SOURCE_MISMATCH",
                    "/comparison/policy_id",
                    "the declared policy belongs to a different source",
                )
            )
            return None
        return policy
    if not source_policies:
        return None
    applicable = [
        policy for policy in source_policies if _policy_matches_plan(policy, plan)
    ]
    if len(applicable) == 1:
        return applicable[0]
    if len(applicable) > 1:
        issues.append(
            _issue(
                "COMPARISON_POLICY_AMBIGUOUS",
                "/comparison/policy_id",
                "more than one declared comparison policy matches this request; "
                "name policy_id explicitly",
            )
        )
        return None
    issues.append(
        _issue(
            "COMPARISON_POLICY_UNDECLARED",
            "/comparison/policy_id",
            "this source declares comparison anchors, but no declared policy "
            "matches the request; a common-scale plan must reference the "
            "study declaration",
        )
    )
    return None


def _check_common_scale_plan(
    plan, comparison, *, policies, queries, query_variants, windows
) -> list[Issue]:
    issues: list[Issue] = []
    query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
    window = plan.get("window") if isinstance(plan.get("window"), dict) else {}
    terms = query.get("terms")
    terms = terms if isinstance(terms, list) else []
    term_index = _term_index(queries, query_variants)
    anchor_ids = _strings(comparison.get("anchor_query_ids")) or []
    anchor_terms = _strings(comparison.get("anchor_terms")) or []

    if not anchor_ids:
        issues.append(
            _issue(
                "COMPARISON_ANCHOR_SET_INCOMPLETE",
                "/comparison/anchor_query_ids",
                "a common_scale plan declares the anchor query ids",
            )
        )
    if not anchor_terms:
        issues.append(
            _issue(
                "COMPARISON_ANCHOR_SET_INCOMPLETE",
                "/comparison/anchor_terms",
                "a common_scale plan declares the anchor terms",
            )
        )

    if len(terms) < 2:
        issues.append(
            _issue(
                "COMPARISON_REQUEST_NOT_MULTI_TERM",
                "/query/terms",
                "a common_scale plan names at least two terms in one "
                "compare_terms request",
            )
        )
    if not isinstance(query.get("text"), str) or not query.get("text"):
        issues.append(
            _issue(
                "COMPARISON_REQUEST_TEXT_MISSING",
                "/query/text",
                "a common_scale plan records the submitted query text",
            )
        )

    by_id = _query_index(queries)
    for position, anchor_id in enumerate(anchor_ids):
        entry = by_id.get(anchor_id)
        if queries and entry is None:
            issues.append(
                _issue(
                    "COMPARISON_ANCHOR_QUERY_UNREGISTERED",
                    f"/comparison/anchor_query_ids/{position}",
                    "anchor query id is not registered in the query registry",
                )
            )
            continue
        if entry is None:
            continue
        canonical = entry.get("canonical_text")
        if not isinstance(canonical, str) or canonical not in anchor_terms:
            issues.append(
                _issue(
                    "COMPARISON_ANCHOR_TERM_UNDECLARED",
                    "/comparison/anchor_terms",
                    "an anchor query's canonical_text is not among the declared "
                    "anchor terms",
                )
            )
            continue
        if canonical not in terms:
            issues.append(
                _issue(
                    "COMPARISON_ANCHOR_NOT_IN_REQUEST",
                    "/query/terms",
                    f"anchor term {canonical!r} is not in the same compare_terms "
                    "request",
                )
            )
    for anchor_term in anchor_terms:
        if anchor_term not in terms:
            issues.append(
                _issue(
                    "COMPARISON_ANCHOR_NOT_IN_REQUEST",
                    "/query/terms",
                    f"anchor term {anchor_term!r} is not in the same "
                    "compare_terms request",
                )
            )

    languages = set()
    for position, term in enumerate(terms):
        if not isinstance(term, str) or not term:
            issues.append(
                _issue(
                    "COMPARISON_TERM_INVALID",
                    f"/query/terms/{position}",
                    "every compared term is a non-empty string",
                )
            )
            continue
        entry = term_index.get(term)
        if queries and entry is None:
            issues.append(
                _issue(
                    "COMPARISON_TERM_UNREGISTERED",
                    f"/query/terms/{position}",
                    "compared term is not registered as a canonical query or "
                    "variant",
                )
            )
            continue
        language = entry.get("language") if entry else None
        if isinstance(language, str) and language:
            languages.add(language)
    if len(languages) > 1:
        issues.append(
            _issue(
                "COMPARISON_LOCALE_MISMATCH",
                "/query/terms",
                "compared terms do not share one locale",
            )
        )

    geo = query.get("geo")
    if not isinstance(geo, str) or not geo:
        issues.append(
            _issue(
                "COMPARISON_GEO_MISSING",
                "/query/geo",
                "a common_scale plan states the geo the shared scale was "
                "requested for",
            )
        )
    declared_geo = comparison.get("geo")
    if declared_geo and geo and declared_geo != geo:
        issues.append(
            _issue(
                "COMPARISON_GEO_MISMATCH",
                "/comparison/geo",
                "declared comparison geo does not match query.geo",
            )
        )
    timeframe = query.get("timeframe")
    if not isinstance(timeframe, str) or not timeframe:
        issues.append(
            _issue(
                "COMPARISON_TIMEFRAME_MISSING",
                "/query/timeframe",
                "a common_scale plan states the requested timeframe",
            )
        )
    if not window.get("window_id") and not (
        window.get("start") and window.get("end_exclusive")
    ):
        issues.append(
            _issue(
                "COMPARISON_WINDOW_MISSING",
                "/window",
                "a common_scale plan states the requested window",
            )
        )

    declared_locale = comparison.get("locale")
    if declared_locale and languages and declared_locale not in languages:
        issues.append(
            _issue(
                "COMPARISON_LOCALE_MISMATCH",
                "/comparison/locale",
                "declared locale does not match the compared terms' locale",
            )
        )

    policy = _select_policy(plan, policies, issues)
    if policy is None:
        return issues

    policy_anchor_ids, policy_anchor_terms = _policy_anchors(policy)
    missing_ids = [item for item in policy_anchor_ids if item not in anchor_ids]
    missing_terms = [item for item in policy_anchor_terms if item not in anchor_terms]
    if missing_ids or missing_terms:
        issues.append(
            _issue(
                "COMPARISON_ANCHOR_SET_INCOMPLETE",
                "/comparison/anchor_terms",
                "the plan does not include every anchor required by the "
                "declared comparison policy",
            )
        )
    request = _request_block(policy)
    if request.get("geo") and geo != request["geo"]:
        issues.append(
            _issue(
                "COMPARISON_GEO_MISMATCH",
                "/query/geo",
                "query.geo does not match the declared comparison policy",
            )
        )
    if request.get("timeframe") and timeframe != request["timeframe"]:
        issues.append(
            _issue(
                "COMPARISON_TIMEFRAME_MISMATCH",
                "/query/timeframe",
                "query.timeframe does not match the declared comparison policy",
            )
        )
    if request.get("window_id") and window.get("window_id") != request["window_id"]:
        issues.append(
            _issue(
                "COMPARISON_WINDOW_MISMATCH",
                "/window/window_id",
                "window_id does not match the declared comparison policy",
            )
        )
    if request.get("window_id") and windows:
        if find_window(windows, request["window_id"]) is None:
            issues.append(
                _issue(
                    "COMPARISON_WINDOW_UNREGISTERED",
                    "/window/window_id",
                    "the policy's window_id is not registered in metadata/windows",
                )
            )
    if request.get("locale") and declared_locale and declared_locale != request["locale"]:
        issues.append(
            _issue(
                "COMPARISON_LOCALE_MISMATCH",
                "/comparison/locale",
                "declared locale does not match the comparison policy",
            )
        )
    if request.get("locale") and languages and request["locale"] not in languages:
        issues.append(
            _issue(
                "COMPARISON_LOCALE_MISMATCH",
                "/query/terms",
                "compared terms are not in the policy locale",
            )
        )
    return issues


def check_plan_comparison(
    plan, *, policies=(), queries=(), query_variants=(), windows=()
) -> list[Issue]:
    """Pre-collection comparison checks for one ``collection-plan-v1``.

    Fail closed for a common-scale declaration; a single-term exploratory plan
    stays allowed and is marked non-comparable (info).  A multi-term plan with
    no declaration is refused: without the declaration there is no anchor
    guarantee, so it cannot be treated as a cross-compound comparison.
    """

    if not isinstance(plan, dict):
        return []
    comparison = plan.get("comparison")
    query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
    terms = query.get("terms")
    multi_term = isinstance(terms, list) and len(terms) > 1

    if comparison is None:
        if multi_term:
            return [
                _issue(
                    "COMPARISON_SCALE_UNDECLARED",
                    "/comparison",
                    "a multi-term compare_terms plan must declare "
                    "comparison_scale and its anchors; without that declaration "
                    "the request cannot be treated as a common-scale comparison",
                )
            ]
        return []

    if not isinstance(comparison, dict):
        return [
            _issue(
                "COMPARISON_SCALE_INVALID",
                "/comparison",
                "comparison declaration must be an object",
            )
        ]

    mode = comparison.get("comparison_scale")
    if mode == SINGLE_SERIES:
        issues: list[Issue] = []
        if multi_term:
            issues.append(
                _issue(
                    "COMPARISON_SINGLE_SERIES_MULTI_TERM",
                    "/comparison/comparison_scale",
                    "a single_series plan cannot request multiple terms",
                )
            )
        anchor_ids, anchor_terms = _policy_anchors(comparison)
        if anchor_ids or anchor_terms:
            issues.append(
                _issue(
                    "COMPARISON_ANCHORS_ON_SINGLE_SERIES",
                    "/comparison/anchor_terms",
                    "a single_series plan declares no common-scale anchors",
                )
            )
        issues.append(
            _issue(
                "COMPARISON_NOT_COMPARABLE",
                "/comparison/comparison_scale",
                "single_series runs are normalized to their own peak and are "
                "not comparable across compounds",
                severity="info",
            )
        )
        return issues

    if mode != COMMON_SCALE:
        return [
            _issue(
                "COMPARISON_SCALE_INVALID",
                "/comparison/comparison_scale",
                "comparison_scale is not a declared comparison scale",
            )
        ]

    return _check_common_scale_plan(
        plan,
        comparison,
        policies=policies,
        queries=queries,
        query_variants=query_variants,
        windows=windows,
    )


# ---------------------------------------------------------------------------
# Post-collection / adoption checks
# ---------------------------------------------------------------------------


def _comparison_artifact_entries(manifest, base_dir):
    """Artifact entries that are comparison documents (read-only)."""

    entries = []
    if isinstance(manifest, dict) and isinstance(manifest.get("artifacts"), list):
        for artifact in manifest["artifacts"]:
            if not isinstance(artifact, dict):
                continue
            if artifact.get("artifact_type") == "comparison" or str(
                artifact.get("schema_id", "")
            ).endswith("comparison-v1"):
                entries.append(artifact)
    if entries:
        return entries
    if base_dir is not None:
        root = Path(base_dir)
        if root.is_dir():
            for path in sorted(root.glob("comparison*.json")):
                entries.append({"path": path.name, "artifact_type": "comparison"})
    return entries


def _artifact_documents(entries, base_dir):
    """Read comparison artifacts: ``(entry, document_or_None)`` pairs."""

    documents = []
    for entry in entries:
        path = Path(base_dir) / str(entry.get("path")) if base_dir is not None else None
        document = _load_json(path) if path is not None else None
        documents.append((entry, document))
    return documents


def _artifact_anchor_state(entries, base_dir, anchors):
    """Per-artifact anchor state: ``(present|missing|unknown, missing_terms, sets)``.

    The comparison artifact is the measurement itself.  A JSON comparison
    document carries its term columns in ``terms``; the weekly rows carry one
    column per term (``date`` is the axis).  A document that cannot be read in
    either form is ``unknown`` and fails closed at adoption, because the
    declared anchors cannot be confirmed.
    """

    sets = []
    worst = "present"
    missing: set[str] = set()
    for entry, document in _artifact_documents(entries, base_dir):
        record = {
            "path": entry.get("path"),
            "terms": [],
            "geo": None,
            "timeframe": None,
            "anchor_state": "unknown",
            "missing_anchor_terms": [],
        }
        if not isinstance(document, dict):
            sets.append(record)
            worst = "unknown" if worst == "present" else worst
            continue
        terms = _strings(document.get("terms")) or []
        if not terms and isinstance(document.get("data"), list) and document["data"]:
            first = document["data"][0]
            if isinstance(first, dict):
                terms = [key for key in first if key != "date"]
        record["terms"] = terms
        record["geo"] = document.get("geo")
        record["timeframe"] = document.get("timeframe")
        if not terms:
            sets.append(record)
            worst = "unknown" if worst == "present" else worst
            continue
        absent = sorted(term for term in anchors if term not in terms)
        record["missing_anchor_terms"] = absent
        if absent:
            record["anchor_state"] = "missing"
            missing.update(absent)
            worst = "missing"
        else:
            record["anchor_state"] = "present"
        sets.append(record)
    return worst, sorted(missing), sets


def _legacy_terms(document):
    """Comparison terms recorded in a legacy run metadata shape (no guessing)."""

    terms = []
    queries = document.get("queries")
    if isinstance(queries, list):
        for query in queries:
            if isinstance(query, dict):
                terms.extend(_strings(query.get("terms")) or [])
    terms.extend(_strings(document.get("terms")) or [])
    seen = set()
    ordered = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            ordered.append(term)
    return ordered


def _request_metadata(document):
    temporal = document.get("temporal_provenance")
    temporal = temporal if isinstance(temporal, dict) else {}
    request = temporal.get("submitted_parameters")
    request = request if isinstance(request, dict) else {}
    return temporal, request


def _unique_terms(*term_lists):
    """Stable union of term lists (request first, artifact terms after)."""

    seen = set()
    ordered = []
    for terms in term_lists:
        for term in terms or ():
            if isinstance(term, str) and term and term not in seen:
                seen.add(term)
                ordered.append(term)
    return ordered


def _scope_state(policy, temporal, request, artifact_sets):
    """Is this run inside the policy's request conditions?

    ``in_scope`` / ``out_of_scope`` / ``unknown``.  A missing observed field is
    ``unknown`` (never assumed to match).
    """

    constraints = _request_block(policy)
    observed = {
        "geo": request.get("geo"),
        "timeframe": request.get("timeframe"),
        "window_id": temporal.get("window_id"),
    }
    if not observed["geo"] or not observed["timeframe"]:
        for artifact in artifact_sets:
            if not observed["geo"] and artifact.get("geo"):
                observed["geo"] = artifact.get("geo")
            if not observed["timeframe"] and artifact.get("timeframe"):
                observed["timeframe"] = artifact.get("timeframe")
    unknown = False
    for field_name in ("geo", "timeframe", "window_id"):
        expected = constraints.get(field_name)
        if not expected:
            continue
        actual = observed.get(field_name)
        if not actual:
            unknown = True
            continue
        if actual != expected:
            return "out_of_scope"
    return "unknown" if unknown else "in_scope"


def _check_common_scale_run(
    document, comparison, *, policies, queries, query_variants, windows, base_dir, manifest
) -> list[Issue]:
    issues: list[Issue] = []
    temporal, request = _request_metadata(document)
    terms = _strings(request.get("terms")) or []
    anchor_ids = _strings(comparison.get("anchor_query_ids")) or []
    anchor_terms = _strings(comparison.get("anchor_terms")) or []

    if not anchor_ids or not anchor_terms:
        issues.append(
            _issue(
                "COMPARISON_ANCHOR_SET_INCOMPLETE",
                "/comparison/anchor_terms",
                "a declared common_scale run records its anchor query ids and "
                "anchor terms",
            )
        )
    if comparison.get("cross_compound_comparable") is not True:
        issues.append(
            _issue(
                "COMPARISON_COMPARABILITY_FLAG_MISMATCH",
                "/comparison/cross_compound_comparable",
                "a common_scale run is marked cross-compound comparable",
            )
        )
    if len(terms) < 2:
        issues.append(
            _issue(
                "COMPARISON_REQUEST_TERMS_MISSING",
                "/temporal_provenance/submitted_parameters/terms",
                "the recorded request does not carry the compared terms; the "
                "anchors cannot be confirmed",
            )
        )
    else:
        for anchor in anchor_terms:
            if anchor not in terms:
                issues.append(
                    _issue(
                        "COMPARISON_ARTIFACT_ANCHOR_MISSING",
                        "/temporal_provenance/submitted_parameters/terms",
                        f"anchor term {anchor!r} is not in the recorded request",
                    )
                )

    # The declaration and the recorded request must agree on the scale
    # identity (geo / timeframe).  A missing recorded field is an error for a
    # declared common-scale run: the comparison cannot be verified.
    for field_name in ("geo", "timeframe"):
        declared = comparison.get(field_name)
        recorded = request.get(field_name)
        if declared and recorded and declared != recorded:
            issues.append(
                _issue(
                    "COMPARISON_ARTIFACT_REQUEST_MISMATCH",
                    "/comparison/%s" % field_name,
                    f"declared comparison {field_name} does not match the "
                    "recorded request",
                )
            )
        if not recorded:
            issues.append(
                _issue(
                    "COMPARISON_REQUEST_FIELD_MISSING",
                    "/temporal_provenance/submitted_parameters/%s" % field_name,
                    f"the recorded request has no {field_name}; the shared scale "
                    "cannot be identified",
                )
            )

    policy = _select_run_policy(document, policies, issues)
    if policy is not None:
        policy_anchor_ids, policy_anchor_terms = _policy_anchors(policy)
        if any(item not in anchor_ids for item in policy_anchor_ids) or any(
            item not in anchor_terms for item in policy_anchor_terms
        ):
            issues.append(
                _issue(
                    "COMPARISON_ANCHOR_SET_INCOMPLETE",
                    "/comparison/anchor_terms",
                    "the run does not include every anchor required by the "
                    "declared comparison policy",
                )
            )
        constraints = _request_block(policy)
        if constraints.get("geo") and request.get("geo") and request["geo"] != constraints["geo"]:
            issues.append(
                _issue(
                    "COMPARISON_GEO_MISMATCH",
                    "/temporal_provenance/submitted_parameters/geo",
                    "recorded geo does not match the declared comparison policy",
                )
            )
        if constraints.get("timeframe") and request.get("timeframe") and request["timeframe"] != constraints["timeframe"]:
            issues.append(
                _issue(
                    "COMPARISON_TIMEFRAME_MISMATCH",
                    "/temporal_provenance/submitted_parameters/timeframe",
                    "recorded timeframe does not match the declared comparison "
                    "policy",
                )
            )
        if constraints.get("window_id") and temporal.get("window_id") != constraints["window_id"]:
            issues.append(
                _issue(
                    "COMPARISON_WINDOW_MISMATCH",
                    "/temporal_provenance/window_id",
                    "recorded window_id does not match the declared comparison "
                    "policy",
                )
            )
        if constraints.get("window_id") and windows:
            registered = find_window(windows, constraints["window_id"])
            if registered is None:
                issues.append(
                    _issue(
                        "COMPARISON_WINDOW_UNREGISTERED",
                        "/temporal_provenance/window_id",
                        "the policy's window_id is not registered in "
                        "metadata/windows",
                    )
                )
            else:
                for run_field, window_field in (
                    ("requested_start", "start"),
                    ("requested_end_exclusive", "end_exclusive"),
                ):
                    recorded = temporal.get(run_field)
                    expected = registered.get(window_field)
                    if recorded and expected and recorded != expected:
                        issues.append(
                            _issue(
                                "COMPARISON_WINDOW_MISMATCH",
                                f"/temporal_provenance/{run_field}",
                                "recorded window bound does not match the "
                                "registered comparison window",
                            )
                        )
        if constraints.get("tool"):
            tool = request.get("tool")
            if not tool:
                issues.append(
                    _issue(
                        "COMPARISON_REQUEST_TOOL_MISSING",
                        "/temporal_provenance/submitted_parameters/tool",
                        "the recorded request has no tool; the comparison request "
                        "cannot be confirmed",
                    )
                )
            elif tool != constraints["tool"]:
                issues.append(
                    _issue(
                        "COMPARISON_REQUEST_TOOL_MISMATCH",
                        "/temporal_provenance/submitted_parameters/tool",
                        "recorded tool does not match the declared comparison "
                        "policy",
                    )
                )
        if constraints.get("locale"):
            declared_locale = comparison.get("locale")
            if declared_locale and declared_locale != constraints["locale"]:
                issues.append(
                    _issue(
                        "COMPARISON_LOCALE_MISMATCH",
                        "/comparison/locale",
                        "declared locale does not match the comparison policy",
                    )
                )
            term_index = _term_index(queries, query_variants)
            languages = set()
            for term in terms:
                entry = term_index.get(term)
                language = entry.get("language") if entry else None
                if isinstance(language, str) and language:
                    languages.add(language)
            if queries and languages and constraints["locale"] not in languages:
                issues.append(
                    _issue(
                        "COMPARISON_LOCALE_MISMATCH",
                        "/temporal_provenance/submitted_parameters/terms",
                        "recorded terms are not in the policy locale",
                    )
                )

    entries = _comparison_artifact_entries(manifest, base_dir)
    if not entries:
        issues.append(
            _issue(
                "COMPARISON_ARTIFACT_MISSING",
                "/artifact_manifest",
                "a declared common_scale run carries a comparison artifact; "
                "the anchors cannot be confirmed without it",
            )
        )
        return issues
    anchor_state, missing_terms, artifact_sets = _artifact_anchor_state(
        entries, base_dir, anchor_terms
    )
    if anchor_state == "unknown":
        issues.append(
            _issue(
                "COMPARISON_ARTIFACT_UNVERIFIABLE",
                "/artifact_manifest",
                "the comparison artifact does not record its terms; the "
                "declared anchors cannot be verified",
            )
        )
    elif anchor_state == "missing":
        issues.append(
            _issue(
                "COMPARISON_ARTIFACT_ANCHOR_MISSING",
                "/artifact_manifest",
                "the comparison artifact is missing anchor term(s): "
                + ", ".join(missing_terms),
            )
        )
    for artifact in artifact_sets:
        for field_name in ("geo", "timeframe"):
            recorded = artifact.get(field_name)
            expected = request.get(field_name)
            if recorded and expected and recorded != expected:
                issues.append(
                    _issue(
                        "COMPARISON_ARTIFACT_REQUEST_MISMATCH",
                        "/artifact_manifest",
                        f"comparison artifact {field_name} does not match the "
                        "recorded request",
                    )
                )
    return issues


def _select_run_policy(document, policies, issues):
    comparison = document.get("comparison")
    policy_id = comparison.get("policy_id") if isinstance(comparison, dict) else None
    source_id = document.get("source_id")
    source_policies = [
        policy
        for policy in policies
        if policy.get("source_id") == source_id and _is_common_scale(policy)
    ]
    if policy_id:
        if not policies:
            return None
        matches = [policy for policy in policies if policy.get("scale_id") == policy_id]
        if len(matches) != 1:
            issues.append(
                _issue(
                    "COMPARISON_POLICY_UNKNOWN",
                    "/comparison/policy_id",
                    "policy_id does not resolve to exactly one declared comparison "
                    "policy",
                )
            )
            return None
        policy = matches[0]
        if policy.get("source_id") != source_id:
            issues.append(
                _issue(
                    "COMPARISON_POLICY_SOURCE_MISMATCH",
                    "/comparison/policy_id",
                    "the declared policy belongs to a different source",
                )
            )
            return None
        return policy
    if source_policies:
        issues.append(
            _issue(
                "COMPARISON_POLICY_UNDECLARED",
                "/comparison/policy_id",
                "the study declares comparison anchors, but the run does not "
                "reference the policy it was collected under",
            )
        )
    return None


def check_run_comparison(
    document,
    *,
    policies=(),
    queries=(),
    query_variants=(),
    windows=(),
    base_dir=None,
    manifest=None,
) -> list[Issue]:
    """Post-collection comparison checks for one ``collection-run-v1``.

    A declared ``common_scale`` run must carry the anchors in the recorded
    request and in a comparison artifact, and its geo / timeframe / window /
    locale must match the declaration.  A ``single_series`` run is allowed and
    marked non-comparable.  An undeclared comparison-shaped run is a legacy
    warning (adoption is not refused for being historical; the audit reports
    it as ``legacy_undeclared``).
    """

    if not isinstance(document, dict):
        return []
    comparison = document.get("comparison")
    temporal, request = _request_metadata(document)
    terms = _strings(request.get("terms")) or []
    legacy_terms = _legacy_terms(document)
    entries = _comparison_artifact_entries(manifest, base_dir)
    comparison_shaped = (
        len(terms) > 1 or len(legacy_terms) > 1 or bool(entries)
    )

    if comparison is None:
        if comparison_shaped:
            return [
                _issue(
                    "COMPARISON_LEGACY_UNDECLARED",
                    "/comparison",
                    "comparison-shaped run carries no comparison declaration; it "
                    "is preserved as legacy provenance and cannot claim the "
                    "declared common scale",
                    severity="warning",
                )
            ]
        return []

    if not isinstance(comparison, dict):
        return [
            _issue(
                "COMPARISON_SCALE_INVALID",
                "/comparison",
                "comparison declaration must be an object",
            )
        ]

    mode = comparison.get("comparison_scale")
    if mode == SINGLE_SERIES:
        issues: list[Issue] = []
        if comparison_shaped:
            issues.append(
                _issue(
                    "COMPARISON_SINGLE_SERIES_MULTI_TERM",
                    "/comparison/comparison_scale",
                    "a single_series run records one term; multiple terms or a "
                    "comparison artifact contradict the declaration",
                )
            )
        if comparison.get("cross_compound_comparable") is not False:
            issues.append(
                _issue(
                    "COMPARISON_COMPARABILITY_FLAG_MISMATCH",
                    "/comparison/cross_compound_comparable",
                    "a single_series run is marked not cross-compound comparable",
                )
            )
        issues.append(
            _issue(
                "COMPARISON_NOT_COMPARABLE",
                "/comparison/comparison_scale",
                "single_series runs are normalized to their own peak and are "
                "not comparable across compounds",
                severity="info",
            )
        )
        return issues

    if mode != COMMON_SCALE:
        return [
            _issue(
                "COMPARISON_SCALE_INVALID",
                "/comparison/comparison_scale",
                "comparison_scale is not a declared comparison scale",
            )
        ]

    return _check_common_scale_run(
        document,
        comparison,
        policies=policies,
        queries=queries,
        query_variants=query_variants,
        windows=windows,
        base_dir=base_dir,
        manifest=manifest,
    )


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def _required_compound_queries(policy, queries):
    """The policy's required compound queries and its recorded exclusions."""

    compound_set = policy.get("compound_set")
    compound_set = compound_set if isinstance(compound_set, dict) else None
    excluded = []
    excluded_ids = set()
    excluded_compounds = set()
    if compound_set is not None:
        for item in compound_set.get("excluded_compound_ids") or ():
            if isinstance(item, dict) and isinstance(item.get("compound_id"), str):
                excluded_compounds.add(item["compound_id"])
                excluded.append(
                    {
                        "compound_id": item["compound_id"],
                        "reason": item.get("reason"),
                    }
                )
        for item in compound_set.get("excluded_query_ids") or ():
            if isinstance(item, dict) and isinstance(item.get("query_id"), str):
                excluded_ids.add(item["query_id"])
                excluded.append(
                    {
                        "query_id": item["query_id"],
                        "reason": item.get("reason"),
                    }
                )
    required = []
    for query in queries or ():
        if not isinstance(query, dict):
            continue
        if query.get("intent_id") != "compound_general":
            continue
        if query.get("status") != "active":
            continue
        if query.get("query_id") in excluded_ids:
            continue
        if query.get("compound_id") in excluded_compounds:
            continue
        if not isinstance(query.get("canonical_text"), str) or not query["canonical_text"]:
            continue
        required.append(query)
    required.sort(key=lambda item: str(item.get("query_id")))
    return required, excluded


def _evaluate_run(
    run_dir,
    document,
    policy,
    *,
    policies,
    queries,
    query_variants,
    windows,
):
    """One run's audit record (read-only)."""

    manifest = _load_json(Path(run_dir) / "artifact-manifest.json")
    temporal, request = _request_metadata(document)
    entries = _comparison_artifact_entries(manifest, run_dir)
    anchor_ids, anchor_terms = _policy_anchors(policy)
    anchor_state, missing_terms, artifact_sets = _artifact_anchor_state(
        entries, run_dir, anchor_terms
    )
    request_terms = _strings(request.get("terms")) or _legacy_terms(document)
    if not entries and request_terms:
        absent = sorted(term for term in anchor_terms if term not in request_terms)
        anchor_state = "missing" if absent else "present"
        missing_terms = absent
    if not request_terms and not entries:
        anchor_state = "unknown"
    scope = _scope_state(policy, temporal, request, artifact_sets)
    declared = document.get("comparison")
    declared = declared if isinstance(declared, dict) else None
    artifact_terms = [
        term for artifact in artifact_sets for term in artifact.get("terms") or ()
    ]
    terms = _unique_terms(request_terms, artifact_terms)
    record = {
        "run_id": document.get("run_id"),
        "path": str(Path(run_dir)),
        "declared": declared is not None,
        "comparison_scale": declared.get("comparison_scale") if declared else None,
        "policy_id": declared.get("policy_id") if declared else None,
        "in_scope": scope,
        "anchor_state": anchor_state,
        "missing_anchor_terms": missing_terms,
        "terms": terms,
        "geo": request.get("geo"),
        "timeframe": request.get("timeframe"),
        "window_id": temporal.get("window_id"),
        "artifact_count": len(entries),
        "artifact_sets": artifact_sets,
        "reasons": [],
        "status": STATUS_SINGLE_SERIES,
    }

    comparison_shaped = len(request_terms) > 1 or bool(entries)
    record["comparison_shaped"] = comparison_shaped
    if declared is None:
        if not comparison_shaped:
            record["status"] = STATUS_SINGLE_SERIES
        elif scope == "out_of_scope":
            record["status"] = STATUS_LEGACY_OUT_OF_SCOPE
        elif anchor_state == "present":
            record["status"] = STATUS_LEGACY_ANCHORED
        elif anchor_state == "missing":
            record["status"] = STATUS_LEGACY_MISSING_ANCHOR
        else:
            record["status"] = STATUS_LEGACY_UNKNOWN
        return record

    issues = check_run_comparison(
        document,
        policies=policies,
        queries=queries,
        query_variants=query_variants,
        windows=windows,
        base_dir=run_dir,
        manifest=manifest,
    )
    record["reasons"] = sorted({issue.code for issue in issues})
    record["comparison_shaped"] = declared.get("comparison_scale") == COMMON_SCALE
    if declared.get("comparison_scale") == SINGLE_SERIES:
        record["status"] = STATUS_SINGLE_SERIES
    elif any(issue.severity == "error" for issue in issues):
        record["status"] = STATUS_INCOMPLETE
    else:
        record["status"] = STATUS_COMPLIANT
    return record


def _source_raw_root(datasets_root, study_id, source_id):
    """Resolve ``data/raw/<source>/`` without depending on production code.

    The repository's catalog layout uses the source slug
    (``google-trends`` -> ``google_trends``), while older studies may use the
    source id verbatim.  The audit checks the verbatim directory first, then
    the slug; a source with neither is reported as absent (never guessed).
    """

    if not isinstance(source_id, str) or not source_id:
        return None
    base = Path(datasets_root) / study_id / "data" / "raw"
    direct = base / source_id
    if direct.is_dir():
        return direct
    slug = source_id.strip().replace("-", "_").lower()
    candidate = base / slug
    if candidate.is_dir():
        return candidate
    return direct


def _policy_report(
    policy,
    *,
    datasets_root,
    study_id,
    queries,
    query_variants,
    windows,
    all_policies,
):
    source_id = policy.get("source_id")
    raw_root = _source_raw_root(datasets_root, study_id, source_id)
    runs = []
    if raw_root is not None and raw_root.is_dir():
        for run_dir in sorted(raw_root.iterdir(), key=lambda item: item.name):
            metadata_path = run_dir / "run_metadata.json"
            if not metadata_path.is_file():
                continue
            document = _load_json(metadata_path)
            if not isinstance(document, dict):
                runs.append(
                    {
                        "run_id": run_dir.name,
                        "path": str(run_dir),
                        "declared": False,
                        "comparison_scale": None,
                        "policy_id": None,
                        "in_scope": "unknown",
                        "anchor_state": "unknown",
                        "missing_anchor_terms": [],
                        "terms": [],
                        "geo": None,
                        "timeframe": None,
                        "window_id": None,
                        "artifact_count": 0,
                        "artifact_sets": [],
                        "reasons": ["COMPARISON_RUN_UNREADABLE"],
                        "status": STATUS_UNREADABLE,
                    }
                )
                continue
            runs.append(
                _evaluate_run(
                    run_dir,
                    document,
                    policy,
                    policies=all_policies,
                    queries=queries,
                    query_variants=query_variants,
                    windows=windows,
                )
            )

    compliant = [
        run
        for run in runs
        if run["status"] == STATUS_COMPLIANT
        and run["policy_id"] == policy.get("scale_id")
    ]
    legacy_anchored = [
        run
        for run in runs
        if run["status"] == STATUS_LEGACY_ANCHORED and run["in_scope"] == "in_scope"
    ]
    missing_anchor_sets = [
        {
            "run_id": run["run_id"],
            "policy_id": policy.get("scale_id"),
            "missing_anchor_terms": run["missing_anchor_terms"],
            "anchor_state": run["anchor_state"],
            "artifact_sets": [
                artifact
                for artifact in run["artifact_sets"]
                if artifact["anchor_state"] != "present"
            ],
        }
        for run in runs
        if run.get("comparison_shaped")
        and run["in_scope"] == "in_scope"
        and run["anchor_state"] != "present"
    ]
    not_comparable = [
        {"run_id": run["run_id"], "status": run["status"]}
        for run in runs
        if run["status"]
        in (
            STATUS_INCOMPLETE,
            STATUS_LEGACY_MISSING_ANCHOR,
            STATUS_LEGACY_UNKNOWN,
        )
        or (run["status"] == STATUS_SINGLE_SERIES and run["declared"])
    ]
    out_of_scope = [
        {
            "run_id": run["run_id"],
            "status": run["status"],
            "in_scope": run["in_scope"],
            "timeframe": run["timeframe"],
            "window_id": run["window_id"],
            "anchor_state": run["anchor_state"],
        }
        for run in runs
        if run["status"] == STATUS_LEGACY_OUT_OF_SCOPE
    ]
    legacy_undeclared = [
        {"run_id": run["run_id"], "status": run["status"]}
        for run in runs
        if run["status"] == STATUS_LEGACY_ANCHORED
    ]
    legacy_missing_anchor_sets = [
        {
            "run_id": run["run_id"],
            "in_scope": run["in_scope"],
            "missing_anchor_terms": run["missing_anchor_terms"],
            "artifact_sets": [
                artifact
                for artifact in run["artifact_sets"]
                if artifact["anchor_state"] != "present"
            ],
        }
        for run in runs
        if not run["declared"]
        and run.get("comparison_shaped")
        and run["anchor_state"] == "missing"
    ]

    required, excluded = _required_compound_queries(policy, queries)
    compound_coverage = []
    for query in required:
        term = query["canonical_text"]
        declared_runs = [
            run["run_id"] for run in compliant if term in run["terms"]
        ]
        legacy_runs = [
            run["run_id"] for run in legacy_anchored if term in run["terms"]
        ]
        if declared_runs:
            state = "complete"
        elif legacy_runs:
            state = "legacy_covered"
        else:
            state = "missing"
        compound_coverage.append(
            {
                "compound_id": query.get("compound_id"),
                "query_id": query.get("query_id"),
                "canonical_text": term,
                "state": state,
                "run_ids": sorted(declared_runs),
                "legacy_run_ids": sorted(legacy_runs),
            }
        )
    missing_compounds = [
        item for item in compound_coverage if item["state"] == "missing"
    ]
    legacy_covered = [
        item for item in compound_coverage if item["state"] == "legacy_covered"
    ]
    return {
        "scale_id": policy.get("scale_id"),
        "source_id": policy.get("source_id"),
        "comparison_scale": policy.get("comparison_scale"),
        "anchor_query_ids": _policy_anchors(policy)[0],
        "anchor_terms": _policy_anchors(policy)[1],
        "request": _request_block(policy),
        "raw_root": str(raw_root) if raw_root is not None else None,
        "raw_root_present": bool(raw_root is not None and raw_root.is_dir()),
        "run_count": len(runs),
        "declared_run_count": sum(1 for run in runs if run["declared"]),
        "compliant_run_count": len(compliant),
        "incomplete_run_count": sum(
            1 for run in runs if run["status"] == STATUS_INCOMPLETE
        ),
        "legacy_comparison_run_count": sum(
            1 for run in runs if run["status"] in _LEGACY_COMPARISON_STATUSES
        ),
        "legacy_missing_anchor_run_count": sum(
            1 for run in runs if run["status"] == STATUS_LEGACY_MISSING_ANCHOR
        ),
        "single_series_run_count": sum(
            1 for run in runs if run["status"] == STATUS_SINGLE_SERIES
        ),
        "runs": runs,
        "required_compound_query_count": len(required),
        "excluded_compound_queries": excluded,
        "compound_coverage": compound_coverage,
        "missing_compounds": missing_compounds,
        "legacy_covered_compounds": legacy_covered,
        "missing_anchor_sets": missing_anchor_sets,
        "legacy_missing_anchor_sets": legacy_missing_anchor_sets,
        "not_comparable_runs": not_comparable,
        "out_of_scope_runs": out_of_scope,
        "legacy_undeclared_runs": legacy_undeclared,
    }


def build_comparison_scale_audit(
    study_id,
    *,
    query_design_path,
    query_registry_path,
    query_variants_path=None,
    windows_dir=None,
    datasets_root="datasets",
    policy_id=None,
    require_complete=False,
    design_only=False,
):
    """Build the read-only common-scale audit for one study (deterministic).

    The report lists every declared policy, every comparison-shaped run with
    its status, the missing anchor sets and the per-compound coverage.  Runs
    that cannot be compared (``not_comparable_runs``), runs outside the
    policy's request conditions (``out_of_scope_runs``) and runs that are
    comparable but predate the declaration (``legacy_undeclared_runs``) are
    separate lists: they support different conclusions.  A ``legacy_*`` status
    is not a data error; the run is reported, never rewritten or promoted.
    """

    design_path = Path(query_design_path)
    design = _load_json(design_path)
    if not isinstance(design, dict):
        raise ValueError(f"query design is missing or unreadable: {design_path}")
    if design.get("study_id") != study_id:
        raise ValueError(
            f"query design study_id {design.get('study_id')!r} does not match "
            f"{study_id!r}"
        )

    registry = _load_json(Path(query_registry_path))
    if not isinstance(registry, dict):
        raise ValueError(f"query registry is missing or unreadable: {query_registry_path}")
    queries = registry.get("queries") if isinstance(registry.get("queries"), list) else []
    query_variants = []
    if query_variants_path:
        variants_document = _load_json(Path(query_variants_path))
        if isinstance(variants_document, dict) and isinstance(
            variants_document.get("variant_sets"), list
        ):
            query_variants = variants_document["variant_sets"]
    windows = []
    if windows_dir:
        window_root = Path(windows_dir)
        if window_root.is_dir():
            for path in sorted(window_root.glob("*.json")):
                document = _load_json(path)
                if isinstance(document, dict):
                    windows.append(document)

    design_issues = check_comparison_design(
        design,
        queries=queries,
        query_variants=query_variants,
        windows=windows,
    )
    policies = _policies_from_document(design)
    if policy_id:
        policies = [policy for policy in policies if policy.get("scale_id") == policy_id]
        if not policies:
            raise ValueError(f"comparison policy is not declared: {policy_id}")

    report = {
        "audit_version": AUDIT_VERSION,
        "study_id": study_id,
        "design_path": str(design_path),
        "design_only": bool(design_only),
        "valid": not any(issue.severity == "error" for issue in design_issues),
        "design_issues": [issue.to_dict() for issue in design_issues],
        "policy_count": len(policies),
        "policies": [],
        "run_count": 0,
        "declared_run_count": 0,
        "compliant_run_count": 0,
        "incomplete_run_count": 0,
        "legacy_comparison_run_count": 0,
        "legacy_missing_anchor_run_count": 0,
        "single_series_run_count": 0,
        "not_comparable_run_count": 0,
        "out_of_scope_run_count": 0,
        "legacy_undeclared_run_count": 0,
        "missing_anchor_set_count": 0,
        "legacy_missing_anchor_set_count": 0,
        "missing_compound_count": 0,
        "missing_compounds": [],
        "failure_count": len(
            [issue for issue in design_issues if issue.severity == "error"]
        ),
        "require_complete": bool(require_complete),
    }
    if not report["valid"] or design_only:
        report["policies"] = [
            {
                "scale_id": policy.get("scale_id"),
                "source_id": policy.get("source_id"),
                "comparison_scale": policy.get("comparison_scale"),
                "anchor_query_ids": _policy_anchors(policy)[0],
                "anchor_terms": _policy_anchors(policy)[1],
                "request": _request_block(policy),
            }
            for policy in policies
        ]
        return report

    policy_reports = []
    for policy in policies:
        if not _is_common_scale(policy):
            continue
        policy_reports.append(
            _policy_report(
                policy,
                datasets_root=datasets_root,
                study_id=study_id,
                queries=queries,
                query_variants=query_variants,
                windows=windows,
                all_policies=policies,
            )
        )
    report["policies"] = policy_reports
    report["run_count"] = sum(item["run_count"] for item in policy_reports)
    report["declared_run_count"] = sum(
        item["declared_run_count"] for item in policy_reports
    )
    report["compliant_run_count"] = sum(
        item["compliant_run_count"] for item in policy_reports
    )
    report["incomplete_run_count"] = sum(
        item["incomplete_run_count"] for item in policy_reports
    )
    report["legacy_comparison_run_count"] = sum(
        item["legacy_comparison_run_count"] for item in policy_reports
    )
    report["legacy_missing_anchor_run_count"] = sum(
        item["legacy_missing_anchor_run_count"] for item in policy_reports
    )
    report["single_series_run_count"] = sum(
        item["single_series_run_count"] for item in policy_reports
    )
    report["not_comparable_run_count"] = sum(
        len(item["not_comparable_runs"]) for item in policy_reports
    )
    report["out_of_scope_run_count"] = sum(
        len(item["out_of_scope_runs"]) for item in policy_reports
    )
    report["legacy_undeclared_run_count"] = sum(
        len(item["legacy_undeclared_runs"]) for item in policy_reports
    )
    report["missing_anchor_set_count"] = sum(
        len(item["missing_anchor_sets"]) for item in policy_reports
    )
    report["legacy_missing_anchor_set_count"] = sum(
        len(item["legacy_missing_anchor_sets"]) for item in policy_reports
    )
    missing_compounds = [
        {"scale_id": item["scale_id"], **compound}
        for item in policy_reports
        for compound in item["missing_compounds"]
    ]
    report["missing_compounds"] = missing_compounds
    report["missing_compound_count"] = len(missing_compounds)
    report["failure_count"] = (
        report["incomplete_run_count"] + report["missing_compound_count"]
    )
    return report
