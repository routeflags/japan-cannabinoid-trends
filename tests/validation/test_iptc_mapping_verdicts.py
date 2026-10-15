"""IPTC subjects attach to the topic dimension only; nothing else gets one.

Contract sources: ``ISS-20261015-TAX-025`` (resolved 2026-10-15),
``metadata/taxonomy/iptc-mapping.yaml`` (coverage declaration),
``metadata/taxonomy/content-taxonomy.skos.jsonld`` (topic/intent/format are
separate schemes), ``docs/specs/standards-compliance-analysis.md`` section 4.3
(only ``topic`` maps to ``schema:about``; intent/format are custom).

The rule: IPTC Media Topics is a news-subject vocabulary, so only the topic
dimension (``jptr:topic-*``) may carry an ``iptc_topic_id``.  Intent
(poster intent) and format (expression form) are different dimensions: mapping
them to IPTC subjects would conflate dimensions, the same violation TAX-026
prohibits for route versus chemical class.  The coverage declaration therefore
records intent/format as ``not_applicable`` with a reason, and this test pins
that verdict so a guessed mapping fails loudly instead of silently landing.

Like ``test_taxonomy_consistency.py``, the declaration is read textually
because this repository deliberately has no YAML dependency.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IPTC_MAPPING = REPO_ROOT / "metadata/taxonomy/iptc-mapping.yaml"

INTENT_CONCEPTS = {
    "jptr:intent-commercial",
    "jptr:intent-experiential",
    "jptr:intent-harm-report",
    "jptr:intent-informational",
}

FORMAT_CONCEPTS = {
    "jptr:format-image",
    "jptr:format-link",
    "jptr:format-text",
    "jptr:format-video",
}


def _entries_with_iptc_subjects(text: str) -> dict[str, str]:
    """``skos_id -> iptc_topic_id`` for entries that declare an IPTC subject."""

    out: dict[str, str] = {}
    for block in text.split("- skos_id:")[1:]:
        skos_id = re.match(r'\s*"([^"]+)"', block)
        topic_id = re.search(r'iptc_topic_id:\s*"([^"]+)"', block)
        if skos_id and topic_id:
            out[skos_id.group(1)] = topic_id.group(1)
    return out


def _not_applicable(text: str) -> set[str]:
    assert "\n  not_applicable:" in text, "coverage lost its not_applicable section"
    chunk = text.split("\n  not_applicable:", 1)[1]
    chunk = chunk.split("\nlimitations:", 1)[0]
    return set(re.findall(r'"(jptr:[^"]+)"', chunk))


def test_only_topic_dimension_concepts_carry_iptc_subjects() -> None:
    text = IPTC_MAPPING.read_text(encoding="utf-8")
    entries = _entries_with_iptc_subjects(text)
    assert entries, "no IPTC subject mapping left in the file"
    for skos_id in entries:
        assert skos_id.startswith("jptr:topic-"), (
            f"{skos_id} carries an IPTC subject but is not in the topic dimension"
        )


def test_intent_and_format_are_declared_out_of_scope() -> None:
    """The TAX-025 verdict: intent/format have no IPTC counterpart by dimension."""

    text = IPTC_MAPPING.read_text(encoding="utf-8")
    entries = _entries_with_iptc_subjects(text)
    declared = _not_applicable(text)
    for concept in INTENT_CONCEPTS | FORMAT_CONCEPTS:
        assert concept in declared, f"{concept} is no longer declared not_applicable"
        assert concept not in entries, f"{concept} gained a guessed IPTC subject"
