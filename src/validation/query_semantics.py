"""G2 query semantics: registry consistency, Stage-1 classification and the
Query Comparability gate (b.md §5, §8, §9, §13).

Contract sources
----------------
- G2 instruction ``docs/plans/20261013b.md``: §4 (the compound taxonomy is
  the canonical source of compound concepts), §5 (registry / variants), §8
  (Stage-1 deterministic classification, ``relevant`` / ``irrelevant`` /
  ``ambiguous`` / ``unknown``), §9 (comparability Q1-Q7), §11 (machine
  guarantees) and §13 (legacy run inventory states).
- Exclusion-rule evidence (this repository): ``docs/collection-gap-analysis.md``
  cause G2 ("X旧runには英語ノイズ混入実例あり（Durban CBD）") and b.md §8 (the
  CBD ambiguity diagram: Cannabidiol vs Central Business District).

Design rules
------------
- Pure functions over plain documents: no Cerberus import (the structural
  layer owns shape), no document mutation (AGENTS.md Raw Data Rule).
- Source-agnostic: no platform names appear here (G1 P1); platform syntax
  equality is compared at the run level by ``validation.comparability`` and is
  not re-implemented.
- Multi-value strings are compared **normalized** (NFKC + casefold +
  whitespace collapse): case and full-width differences are absorbed by
  normalization, not by variant entries (b.md §5.3: variants cannot guarantee
  equivalence, so mechanical duplicates are refused).
- Missing auxiliary documents (taxonomy / sibling registry) disable the
  corresponding cross-checks instead of producing false failures - the same
  convention as ``validation.semantic.Registries``.
- The Stage-1 classifier is machinery, not a production content classifier:
  b.md §8.3 requires labelled evaluation data before production adoption and
  this slice does not provide any (recorded in
  ``docs/specs/validation-framework.md`` §15).
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from validation.comparability import ComparabilityResult
from validation.reporting import Issue, join_pointer

__all__ = [
    "CompoundVocabulary",
    "EXCLUSION_RULES",
    "ExclusionRule",
    "build_query_inventory",
    "check_query_registry",
    "check_query_variants",
    "classify_collected_query",
    "classify_query_text",
    "compare_query_definitions",
    "extract_query_strings",
    "load_compound_vocabulary",
    "normalize_query_text",
    "resolve_query_text",
]


# ---------------------------------------------------------------------------
# normalization
# ---------------------------------------------------------------------------


def normalize_query_text(text):
    """NFKC + casefold + whitespace collapse; ``None`` for non-strings.

    This is the comparison form only.  Raw collected strings are never
    rewritten (P4: the submitted query is preserved as-is by provenance).
    """
    if not isinstance(text, str):
        return None
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or None


def _squeeze_text(text):
    """Loose form that also drops all whitespace (space-notation drift only).

    Used solely for the ``semantic_match_candidate`` inventory state: a
    whitespace/width-only difference is a *candidate* for correspondence and
    is never adopted automatically (b.md §13).
    """
    normalized = normalize_query_text(text)
    if normalized is None:
        return None
    return normalized.replace(" ", "")


# ---------------------------------------------------------------------------
# Stage 1 - deterministic exclusion rules (b.md §8)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExclusionRule:
    """One explicit noise phrase with its recorded rationale and evidence.

    Rules are *phrases*, not single words, and every rule carries where it
    came from - nothing is excluded without a recorded reason (b.md §8.3:
    "単一の除外語だけで検索結果全体を除外する設計は避ける" - classification
    is per text, never per collection).
    """

    rule_id: str
    phrase: str  # matched against the normalized text (substring)
    rationale: str
    evidence: str


EXCLUSION_RULES = (
    ExclusionRule(
        rule_id="non-compound-durban-cbd",
        phrase="durban cbd",
        rationale=(
            "'Durban CBD' is a recorded noise example from the old X runs: a "
            "geographic/street-district reading of the abbreviation, not "
            "cannabidiol."
        ),
        evidence=(
            "docs/collection-gap-analysis.md (cause G2: 'X旧runには英語ノイズ混入"
            "実例あり（Durban CBD）'); docs/plans/20261013b.md §8.3"
        ),
    ),
    ExclusionRule(
        rule_id="non-compound-central-business-district",
        phrase="central business district",
        rationale=(
            "Spelled-out district reading of the 'CBD' abbreviation (b.md §8 "
            "ambiguity diagram); cannot be a cannabinoid query."
        ),
        evidence="docs/plans/20261013b.md §8 (CBD -> Central Business District)",
    ),
)


def _matching_exclusion_rule(normalized_text):
    if not normalized_text:
        return None
    for rule in EXCLUSION_RULES:
        if rule.phrase in normalized_text:
            return rule
    return None


# ---------------------------------------------------------------------------
# Compound vocabulary (loaded from the existing SKOS taxonomy)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompoundVocabulary:
    """Compound reference data taken from ``compound-taxonomy.skos.jsonld``.

    ``notations`` are the portable Concept IDs (AGENTS.md) of concepts that
    sit *below* the scheme's top categories (``skos:broader`` present); the
    top categories themselves are not compounds.  ``tokens`` are the short
    labels used by the Stage-1 classifier to detect that a text *mentions* a
    compound even when the text itself is not registered.
    """

    notations: frozenset
    tokens: frozenset


_PARENTHETICAL = re.compile(r"\(([A-Za-z][A-Za-z0-9-]{1,14})\)\s*$")


def _label_values(value) -> list:
    """Normalize a JSON-LD label field (dict or list of dicts) to strings."""
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return []
    return [
        item["@value"]
        for item in value
        if isinstance(item, dict) and isinstance(item.get("@value"), str)
    ]


def load_compound_vocabulary(path) -> CompoundVocabulary:
    """Read the compound taxonomy (JSON-LD) into a :class:`CompoundVocabulary`.

    The repository file uses repeated JSON keys (a JSON-LD compact-frame
    artifact), so the English ``prefLabel`` may be lost on load; the
    ``altLabel`` lists carry the short codes and remain intact.  Only labels
    that are actually present are used - nothing is inferred.
    """
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    graph = document.get("@graph") if isinstance(document, dict) else None
    notations = set()
    tokens = set()
    for node in graph if isinstance(graph, list) else []:
        if not isinstance(node, dict):
            continue
        notation = node.get("skos:notation")
        if not isinstance(notation, str) or not notation:
            continue
        if "skos:broader" in node:
            notations.add(notation)
        for label in _label_values(node.get("skos:altLabel")):
            normalized = normalize_query_text(label)
            if normalized:
                tokens.add(normalized)
        for label in _label_values(node.get("skos:prefLabel")):
            match = _PARENTHETICAL.search(label)
            if match:
                normalized = normalize_query_text(match.group(1))
                if normalized:
                    tokens.add(normalized)
    return CompoundVocabulary(
        notations=frozenset(notations), tokens=frozenset(tokens)
    )


def _contains_token(text: str, token: str) -> bool:
    """Word-boundary match for ASCII tokens, substring for the rest.

    Prevents e.g. 'THC' matching inside 'THCV' (the longer token exists) while
    still matching Japanese compound names without boundaries.
    """
    if token.isascii():
        pattern = r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return token in text


# ---------------------------------------------------------------------------
# resolution / classification
# ---------------------------------------------------------------------------


def _items(document, key):
    if isinstance(document, dict) and isinstance(document.get(key), list):
        return document[key]
    return ()


def resolve_query_text(text, *, query_registry=None, variant_registry=None):
    """Resolve a text against the registry: canonical text or variant text.

    Returns ``{"match", "query_id", "variant_id", "status"}`` or ``None``.
    Comparison is normalized; the raw text is never rewritten.
    """
    normalized = normalize_query_text(text)
    if not normalized:
        return None
    for query in _items(query_registry, "queries"):
        if not isinstance(query, dict):
            continue
        if normalize_query_text(query.get("canonical_text")) == normalized:
            return {
                "match": "canonical",
                "query_id": query.get("query_id"),
                "variant_id": None,
                "status": query.get("status"),
                "query_status": query.get("status"),
            }
    for block in _items(variant_registry, "variant_sets"):
        if not isinstance(block, dict):
            continue
        for variant in _items(block, "variants"):
            if not isinstance(variant, dict):
                continue
            if normalize_query_text(variant.get("text")) == normalized:
                query_status = None
                for candidate in _items(query_registry, "queries"):
                    if (
                        isinstance(candidate, dict)
                        and candidate.get("query_id") == block.get("query_id")
                    ):
                        query_status = candidate.get("status")
                        break
                return {
                    "match": "variant",
                    "query_id": block.get("query_id"),
                    "variant_id": variant.get("variant_id"),
                    "status": variant.get("status"),
                    "query_status": query_status,
                }
    return None


def classify_query_text(
    text, *, query_registry=None, variant_registry=None, vocabulary=None
) -> dict:
    """Stage-1 deterministic classification of one query string (b.md §8).

    Order of decision (each step records its reason):

    1. an exclusion rule fires -> ``irrelevant`` (rule id, rationale and
       evidence are carried in the result);
    2. the text resolves to a registered canonical text or variant ->
       ``relevant``;
    3. the text mentions a compound (taxonomy label token) without being
       registered -> ``ambiguous`` (never silently adopted);
    4. otherwise -> ``unknown``.

    With no vocabulary loaded, step 3 cannot run and such texts fall through
    to ``unknown`` (uncertainty is preserved, nothing is guessed).
    """
    result = {
        "text": text if isinstance(text, str) else None,
        "normalized": normalize_query_text(text),
        "classification": "unknown",
        "query_id": None,
        "variant_id": None,
        "match": None,
        "status": None,
        "query_status": None,
        "rule_id": None,
        "rationale": None,
        "evidence": None,
        "matched_tokens": [],
        "reasons": [],
    }
    if result["normalized"] is None:
        result["reasons"] = ["empty_text"]
        return result

    rule = _matching_exclusion_rule(result["normalized"])
    if rule is not None:
        result["classification"] = "irrelevant"
        result["rule_id"] = rule.rule_id
        result["rationale"] = rule.rationale
        result["evidence"] = rule.evidence
        result["reasons"] = [f"exclusion_rule:{rule.rule_id}"]
        return result

    match = resolve_query_text(
        text, query_registry=query_registry, variant_registry=variant_registry
    )
    if match is not None:
        result["classification"] = "relevant"
        result["query_id"] = match["query_id"]
        result["variant_id"] = match["variant_id"]
        result["match"] = match["match"]
        result["status"] = match["status"]
        result["query_status"] = match.get("query_status")
        result["reasons"] = [f"registered_{match['match']}"]
        return result

    if vocabulary is not None:
        matched = sorted(
            token
            for token in vocabulary.tokens
            if _contains_token(result["normalized"], token)
        )
        if matched:
            result["classification"] = "ambiguous"
            result["matched_tokens"] = matched
            result["reasons"] = ["compound_token_without_registered_query"]
            return result

    result["reasons"] = ["no_compound_token"]
    return result


# ---------------------------------------------------------------------------
# registry consistency checks (structure stays with Cerberus)
# ---------------------------------------------------------------------------


def _issue(code, path, message, rule, severity="error"):
    return Issue(
        code=code,
        path=path,
        severity=severity,
        message=message,
        rule=rule,
        schema_version="",
    )


def check_query_registry(document, *, vocabulary=None) -> list:
    """Semantic checks for one query-registry document.

    - duplicate ``query_id`` (G2-T02: query ID uniqueness);
    - duplicate normalized ``canonical_text`` (two concepts must not claim
      the same search string);
    - ``compound_id`` must be a compound concept of the taxonomy when a
      vocabulary is available (G2-T01 / b.md §11 "Taxonomy参照整合性");
    - a registered text must not match an exclusion rule (the registry would
      adopt a string the classifier classifies as irrelevant).

    Messages never contain the offending values (h.md §14).
    """
    issues: list = []
    if not isinstance(document, dict):
        return issues
    queries = document.get("queries")
    if not isinstance(queries, list):
        return issues
    seen_ids = set()
    seen_texts = set()
    for index, query in enumerate(queries):
        if not isinstance(query, dict):
            continue
        path = f"/queries/{index}"
        query_id = query.get("query_id")
        if isinstance(query_id, str) and query_id:
            if query_id in seen_ids:
                issues.append(
                    _issue(
                        "QUERY_DUPLICATE_ID",
                        join_pointer(path, "query_id"),
                        "query_id is registered more than once",
                        "query_uniqueness",
                    )
                )
            else:
                seen_ids.add(query_id)
        normalized = normalize_query_text(query.get("canonical_text"))
        if normalized:
            if normalized in seen_texts:
                issues.append(
                    _issue(
                        "QUERY_DUPLICATE_TEXT",
                        join_pointer(path, "canonical_text"),
                        "canonical_text duplicates another registered query "
                        "text (after normalization)",
                        "query_uniqueness",
                    )
                )
            else:
                seen_texts.add(normalized)
            rule = _matching_exclusion_rule(normalized)
            if rule is not None:
                issues.append(
                    _issue(
                        "QUERY_TEXT_EXCLUDED",
                        join_pointer(path, "canonical_text"),
                        "registered text matches an exclusion rule "
                        f"({rule.rule_id}); the registry must not adopt a "
                        "non-compound string",
                        "query_text",
                    )
                )
        compound = query.get("compound_id")
        if (
            vocabulary is not None
            and isinstance(compound, str)
            and compound
            and compound not in vocabulary.notations
        ):
            issues.append(
                _issue(
                    "QUERY_COMPOUND_UNREGISTERED",
                    join_pointer(path, "compound_id"),
                    "compound_id is not a compound concept of the taxonomy",
                    "query_compound",
                )
            )
    return issues


def check_query_variants(document, *, query_registry=None, vocabulary=None) -> list:
    """Semantic checks for one query-variants bundle document.

    - duplicate variant-set ``query_id``;
    - every set references a registered query (when the registry is loaded);
    - exactly one ``primary`` variant per set, equal to the registered
      ``canonical_text``;
    - variant IDs unique across the document (G2-T04);
    - variant texts unique across the document after normalization, and no
      alternative text may duplicate any registered canonical text;
    - variant texts must not match an exclusion rule.
    """
    issues: list = []
    if not isinstance(document, dict):
        return issues
    variant_sets = document.get("variant_sets")
    if not isinstance(variant_sets, list):
        return issues

    registry_available = False
    canonical_by_id = {}
    canonical_texts = set()
    if isinstance(query_registry, dict) and isinstance(query_registry.get("queries"), list):
        for query in query_registry["queries"]:
            if not isinstance(query, dict):
                continue
            query_id = query.get("query_id")
            normalized = normalize_query_text(query.get("canonical_text"))
            if isinstance(query_id, str) and query_id:
                registry_available = True
                if normalized:
                    canonical_by_id[query_id] = normalized
            if normalized:
                canonical_texts.add(normalized)

    seen_set_ids = set()
    seen_variant_ids = set()
    seen_texts = {}
    for set_index, block in enumerate(variant_sets):
        if not isinstance(block, dict):
            continue
        set_path = f"/variant_sets/{set_index}"
        query_id = block.get("query_id")
        if isinstance(query_id, str) and query_id:
            if query_id in seen_set_ids:
                issues.append(
                    _issue(
                        "VARIANT_SET_DUPLICATE",
                        join_pointer(set_path, "query_id"),
                        "query_id has more than one variant set",
                        "variant_uniqueness",
                    )
                )
            else:
                seen_set_ids.add(query_id)
            if registry_available and query_id not in canonical_by_id:
                issues.append(
                    _issue(
                        "VARIANT_QUERY_UNREGISTERED",
                        join_pointer(set_path, "query_id"),
                        "variant set references a query_id that is not in the "
                        "query registry",
                        "variant_reference",
                    )
                )
        variants = block.get("variants")
        if not isinstance(variants, list):
            continue
        primaries = [
            variant
            for variant in variants
            if isinstance(variant, dict) and variant.get("status") == "primary"
        ]
        if len(primaries) != 1:
            issues.append(
                _issue(
                    "VARIANT_PRIMARY_COUNT",
                    join_pointer(set_path, "variants"),
                    "exactly one primary variant is required per query",
                    "variant_primary",
                )
            )
        for variant_index, variant in enumerate(variants):
            if not isinstance(variant, dict):
                continue
            variant_path = f"{set_path}/variants/{variant_index}"
            variant_id = variant.get("variant_id")
            if isinstance(variant_id, str) and variant_id:
                if variant_id in seen_variant_ids:
                    issues.append(
                        _issue(
                            "VARIANT_DUPLICATE_ID",
                            join_pointer(variant_path, "variant_id"),
                            "variant_id is used more than once",
                            "variant_uniqueness",
                        )
                    )
                else:
                    seen_variant_ids.add(variant_id)
            normalized = normalize_query_text(variant.get("text"))
            if not normalized:
                continue
            status = variant.get("status")
            if (
                status == "primary"
                and isinstance(query_id, str)
                and query_id in canonical_by_id
                and normalized != canonical_by_id[query_id]
            ):
                issues.append(
                    _issue(
                        "VARIANT_PRIMARY_MISMATCH",
                        join_pointer(variant_path, "text"),
                        "the primary variant text must equal the registered "
                        "canonical_text of its query",
                        "variant_primary",
                    )
                )
            if status == "alternative" and (
                normalized in canonical_texts
                or normalized == canonical_by_id.get(query_id)
            ):
                issues.append(
                    _issue(
                        "VARIANT_TEXT_CONFLICTS_CANONICAL",
                        join_pointer(variant_path, "text"),
                        "an alternative variant text duplicates a registered "
                        "canonical text",
                        "variant_uniqueness",
                    )
                )
            if normalized in seen_texts:
                issues.append(
                    _issue(
                        "VARIANT_DUPLICATE_TEXT",
                        join_pointer(variant_path, "text"),
                        "variant text duplicates another variant "
                        "(after normalization)",
                        "variant_uniqueness",
                    )
                )
            else:
                seen_texts[normalized] = variant_path
            rule = _matching_exclusion_rule(normalized)
            if rule is not None:
                issues.append(
                    _issue(
                        "VARIANT_TEXT_EXCLUDED",
                        join_pointer(variant_path, "text"),
                        "variant text matches an exclusion rule "
                        f"({rule.rule_id})",
                        "variant_text",
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Query Comparability gate (b.md §9 subset; consistent with G1 C1)
# ---------------------------------------------------------------------------


def compare_query_definitions(
    a,
    b,
    *,
    submitted_a=None,
    submitted_b=None,
    registry_version_a=None,
    registry_version_b=None,
) -> ComparabilityResult:
    """Definition-level comparability of two registered queries (Q1-Q7).

    The verdict can never be stronger than G1 L2 C1 (the run-level
    authority):

    - different ``query_id`` -> ``not_comparable`` with ``q1``..``q5``
      reason codes (C1 reports ``c1_query_mismatch`` for the same pair);
    - same ``query_id`` -> ``conditional`` at best, and ``not_comparable``
      (``q5_submitted_query_mismatch``) when both submitted texts are given
      and differ - exactly the C1 behaviour;
    - ``comparable`` is never produced: coverage / sampling / platform
      reviews are out of scope (the same ceiling as the other gates).

    ``q6`` (semantic filter) is recorded as absent and ``q7`` (registry
    version) as a review note when the versions differ; neither is treated as
    a silent pass.  Missing metadata yields ``unknown``.
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        return ComparabilityResult("unknown", ["insufficient_metadata"])
    if not a.get("query_id") or not b.get("query_id"):
        return ComparabilityResult("unknown", ["insufficient_metadata"])
    if (submitted_a is None) != (submitted_b is None):
        return ComparabilityResult("unknown", ["insufficient_metadata"])

    if a["query_id"] != b["query_id"]:
        reasons = []
        if a.get("compound_id") != b.get("compound_id"):
            reasons.append("q1_compound_mismatch")
        if a.get("intent_id") != b.get("intent_id"):
            reasons.append("q2_intent_mismatch")
        if normalize_query_text(a.get("canonical_text")) != normalize_query_text(
            b.get("canonical_text")
        ):
            reasons.append("q3_text_mismatch")
        if a.get("language") != b.get("language"):
            reasons.append("q4_language_mismatch")
        if submitted_a is not None and normalize_query_text(
            submitted_a
        ) != normalize_query_text(submitted_b):
            reasons.append("q5_submitted_query_mismatch")
        if not reasons:
            # C1 flags any differing (query_id, submitted_query) identity; the
            # definition gate mirrors that with an identity fallback.
            reasons.append("q_identity_mismatch")
        return ComparabilityResult("not_comparable", sorted(reasons))

    if submitted_a is not None and normalize_query_text(
        submitted_a
    ) != normalize_query_text(submitted_b):
        return ComparabilityResult("not_comparable", ["q5_submitted_query_mismatch"])

    conditionals = ["q5_platform_syntax_review_required", "q6_semantic_filter_absent"]
    if (
        registry_version_a is not None
        and registry_version_b is not None
        and registry_version_a != registry_version_b
    ):
        conditionals.append("q7_registry_version_differs")
    return ComparabilityResult("conditional", sorted(conditionals))


# ---------------------------------------------------------------------------
# legacy run inventory (b.md §13) - extraction and state mapping
# ---------------------------------------------------------------------------

_INVENTORY_STATES = (
    "exact_match",
    "variant_match",
    "semantic_match_candidate",
    "ambiguous",
    "unmapped",
)

_STATE_NOTES = {
    "exact_match": "the collected text equals a registered canonical_text",
    "variant_match": "the collected text equals a registered variant text",
    "semantic_match_candidate": (
        "texts differ only in spacing/width; a candidate for review, never "
        "adopted automatically"
    ),
    "ambiguous": (
        "a compound token (or exclusion rule) is present without a registered "
        "correspondence; human review required"
    ),
    "unmapped": "no registered correspondence and no compound token",
}


def extract_query_strings(document) -> list:
    """Extract collected query strings from a run metadata document.

    Recognized fields (read-only; the source field is recorded per string):

    - ``queries[].term`` / ``queries[].terms[]`` (the standard G1-era shape);
    - top-level ``terms[]`` and ``keyword`` (used by single-term legacy runs);
    - ``compounds_collected[]`` - compound identifiers recorded by the
      collector; kept as transparent candidates (``source_field``), not as a
      verified submitted query.

    Strings are de-duplicated by normalized form; every contributing source
    field is kept.  No value is ever rewritten.
    """
    if not isinstance(document, dict):
        return []
    pairs = []
    queries = document.get("queries")
    if isinstance(queries, list):
        for index, query in enumerate(queries):
            if not isinstance(query, dict):
                continue
            term = query.get("term")
            if isinstance(term, str) and term:
                pairs.append((term, f"queries[{index}].term"))
            terms = query.get("terms")
            if isinstance(terms, list):
                for term_index, item in enumerate(terms):
                    if isinstance(item, str) and item:
                        pairs.append((item, f"queries[{index}].terms[{term_index}]"))
    terms = document.get("terms")
    if isinstance(terms, list):
        for index, item in enumerate(terms):
            if isinstance(item, str) and item:
                pairs.append((item, f"terms[{index}]"))
    keyword = document.get("keyword")
    if isinstance(keyword, str) and keyword:
        pairs.append((keyword, "keyword"))
    compounds = document.get("compounds_collected")
    if isinstance(compounds, list):
        for index, item in enumerate(compounds):
            if isinstance(item, str) and item:
                pairs.append((item, f"compounds_collected[{index}]"))

    merged: dict = {}
    order: list = []
    for text, field in pairs:
        normalized = normalize_query_text(text)
        if normalized is None:
            continue
        if normalized not in merged:
            merged[normalized] = {"text": text, "source_fields": [field]}
            order.append(normalized)
        elif field not in merged[normalized]["source_fields"]:
            merged[normalized]["source_fields"].append(field)
    return [merged[key] for key in order]


def classify_collected_query(
    text, *, query_registry, variant_registry=None, vocabulary=None
) -> dict:
    """Map one collected string to the b.md §13 correspondence state.

    ``semantic_match_candidate`` is a *candidate* (space/width-only
    difference); it is never treated as the same query automatically.
    Excluded strings and unregistered compound-token strings become
    ``ambiguous`` (cannot be adopted as a compound query without review).
    """
    entry = {
        "text": text,
        "state": "unmapped",
        "classification": "unknown",
        "query_id": None,
        "variant_id": None,
        "detail": None,
    }
    match = resolve_query_text(
        text, query_registry=query_registry, variant_registry=variant_registry
    )
    if match is not None:
        entry["classification"] = "relevant"
        entry["query_id"] = match["query_id"]
        entry["variant_id"] = match["variant_id"]
        if match["match"] == "canonical":
            entry["state"] = "exact_match"
            entry["detail"] = "registered_canonical"
        else:
            entry["state"] = "variant_match"
            entry["detail"] = f"registered_variant:{match['variant_id']}"
        return entry

    loose = _squeeze_text(text)
    loose_targets = set()
    for query in _items(query_registry, "queries"):
        if isinstance(query, dict):
            target = _squeeze_text(query.get("canonical_text"))
            if target:
                loose_targets.add(target)
    for block in _items(variant_registry, "variant_sets"):
        if isinstance(block, dict):
            for variant in _items(block, "variants"):
                if isinstance(variant, dict):
                    target = _squeeze_text(variant.get("text"))
                    if target:
                        loose_targets.add(target)
    if loose and loose in loose_targets:
        entry["state"] = "semantic_match_candidate"
        entry["classification"] = "ambiguous"
        entry["detail"] = "loose_text_match_not_auto_adopted"
        return entry

    classification = classify_query_text(
        text,
        query_registry=query_registry,
        variant_registry=variant_registry,
        vocabulary=vocabulary,
    )
    entry["classification"] = classification["classification"]
    if classification["classification"] == "irrelevant":
        entry["state"] = "ambiguous"
        entry["detail"] = f"excluded_by_rule:{classification['rule_id']}"
    elif classification["classification"] == "ambiguous":
        entry["state"] = "ambiguous"
        entry["detail"] = "compound_token_without_registered_query"
    else:
        entry["state"] = "unmapped"
        entry["detail"] = "no_registered_correspondence"
    return entry


def build_query_inventory(
    run_entries, *, query_registry, variant_registry=None, vocabulary=None
) -> dict:
    """Build the non-destructive b.md §13 inventory over run metadata files.

    ``run_entries`` is an iterable of ``{"path", "document", "sha256",
    "sha256_after", "unchanged"}`` mappings (reading files is the caller's
    job, so the builder stays pure and testable).  The output is
    deterministic: runs are sorted by path and strings keep document order.
    """
    runs = []
    summary = {state: 0 for state in _INVENTORY_STATES}
    query_count = 0
    raw_modified = False
    for entry in sorted(run_entries, key=lambda item: str(item.get("path", ""))):
        document = entry.get("document")
        records = []
        for extracted in extract_query_strings(document):
            record = classify_collected_query(
                extracted["text"],
                query_registry=query_registry,
                variant_registry=variant_registry,
                vocabulary=vocabulary,
            )
            record["source_fields"] = list(extracted["source_fields"])
            summary[record["state"]] += 1
            query_count += 1
            records.append(record)
        if entry.get("unchanged") is False:
            raw_modified = True
        runs.append(
            {
                "run_id": document.get("run_id") if isinstance(document, dict) else None,
                "path": str(entry.get("path")),
                "status": "read" if isinstance(document, dict) else "unreadable",
                "sha256": entry.get("sha256"),
                "sha256_after": entry.get("sha256_after"),
                "unchanged": entry.get("unchanged"),
                "extracted_query_count": len(records),
                "queries": records,
            }
        )
    registry_version = None
    if isinstance(query_registry, dict):
        registry_version = query_registry.get("schema_version")
    return {
        "audit_version": "1.0.0",
        "profile": "g2_query_inventory",
        "schema_id": "query-registry-v1",
        "registry_version": registry_version,
        "target_glob": "datasets/**/run_metadata.json",
        "count": len(runs),
        "query_count": query_count,
        "raw_modified": raw_modified,
        "states": dict(_STATE_NOTES),
        "summary": summary,
        "runs": runs,
    }
