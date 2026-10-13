"""Rule-based content classification against the SKOS concept notations.

The classifier is deliberately dumb and deterministic: it counts keyword
occurrences per concept and takes the highest count, falling back to
``unclassified`` when no keyword appears.  AGENTS.md requires classification logic
to be separable from the taxonomy and replaceable (LLM / BERT / SetFit); the only
portable output here is the concept *notation*, never a label or index.

Two behaviours are fixed by the specification and reproduced here exactly:

- matching is case-insensitive substring matching, not token matching;
- ties are broken by the specification's own key order, i.e. the first concept
  declared wins.  The specification does not state a tie rule; this reading is the
  one that reproduces the committed artifact, and it is asserted against the
  specification's recorded distribution in the tests.

Changing either behaviour changes published classifications, so they are stated
here rather than left implicit.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Mapping, Sequence

from processing.rulespec import ContentRules

__all__ = [
    "classify_text",
    "classify_topic",
    "classify_intent",
    "classify_format",
    "distribution",
]


def _count_matches(haystack: str, keywords: Sequence[str]) -> int:
    return sum(1 for keyword in keywords if keyword.lower() in haystack)


def _select_concept(
    text: str, groups: Mapping[str, Sequence[str]], fallback: str
) -> str:
    haystack = text.lower()
    best = fallback
    best_count = 0
    for concept, keywords in groups.items():
        count = _count_matches(haystack, keywords)
        if count > best_count:
            best, best_count = concept, count
    return best


def classify_topic(text: str, rules: ContentRules) -> str:
    """Return the ``topic_id`` concept notation for ``text``."""

    return _select_concept(text, rules.topic_keywords, rules.topic_fallback)


def classify_intent(text: str, rules: ContentRules) -> str:
    """Return the ``intent_id`` concept notation for ``text``."""

    return _select_concept(text, rules.intent_keywords, rules.intent_fallback)


def classify_format(text: str, rules: ContentRules) -> str:
    """Return the ``format_id`` concept notation for ``text``.

    The specification's format rule is \u300ccontains a URL AND is shorter than the
    recorded threshold\u300d.
    """

    if rules.format_url_marker in text and len(text) < rules.format_max_length:
        return rules.format_link_result
    return rules.format_default_result


def classify_text(text: str, rules: ContentRules) -> dict[str, str]:
    """Classify one record's text into the three content dimensions."""

    return {
        "topic_id": classify_topic(text, rules),
        "intent_id": classify_intent(text, rules),
        "format_id": classify_format(text, rules),
    }


def distribution(values: Iterable[str]) -> dict[str, int]:
    """Count concept notations, sorted by descending count then notation."""

    counts = Counter(values)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
