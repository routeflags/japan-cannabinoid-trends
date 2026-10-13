"""Content-classifier specification and classifier tests.

Contract sources: ``metadata/taxonomy/classification-rules.yaml`` (the
specification), ``docs/data-dictionary.md`` sections 3-4 (schema + notations),
AGENTS.md (classifier-agnostic taxonomy, Concept IDs, executable transformations).

The decisive test is :func:`test_classifier_reproduces_recorded_distribution`: it
runs the classifier over the committed X texts and requires the result to equal the
distribution the specification itself records from its 2026-10-02 run.  A parser or
classifier regression therefore fails against the specification's own expected
output, not against a hand-copied constant.
"""

from pathlib import Path

import pytest

from processing.classify import classify_format, classify_text, distribution
from processing.rulespec import (
    ContentRules,
    RuleSpecError,
    load_content_rules,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ANONYMIZED = (
    REPO_ROOT
    / "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv"
)
#: The non-anonymized summary carries X identities and is deliberately not
#: published (see ``processing.reproduce.WITHDRAWN``).  It is present only in a
#: checkout that holds the non-published copy, so tests that need it skip in CI.
PRIVATE_SOURCE = (
    REPO_ROOT / "datasets/cbx-social-trends/data/private/x_cbx_202608_summary.csv"
)
requires_private_source = pytest.mark.skipif(
    not PRIVATE_SOURCE.is_file(),
    reason="non-published X summary not present in this checkout",
)


@pytest.fixture(scope="module")
def rules() -> ContentRules:
    return load_content_rules(repo_root=REPO_ROOT)


def test_spec_is_read_as_documented(rules: ContentRules) -> None:
    assert rules.spec_version == "1.0.0"
    assert rules.classifier_version == "1.0.0"
    assert rules.topic_fallback == "unclassified"
    assert rules.intent_fallback == "unclassified"
    assert rules.format_link_result == "format_link"
    assert rules.format_default_result == "format_text"
    assert rules.format_max_length == 100
    assert len(rules.topic_keywords["topic_ingredient"]) == 16
    assert len(rules.intent_keywords["intent_commercial"]) == 14
    assert rules.recorded_total == 147


def test_declared_concepts_exist_in_the_skos_taxonomy(rules: ContentRules) -> None:
    """AGENTS.md: classification must map to the controlled vocabulary.

    Every concept the rules can emit must be a notation of
    ``content-taxonomy.skos.jsonld``.  ``unclassified`` is a fallback and is
    deliberately absent from the taxonomy, so it is excluded here.
    """

    import json

    taxonomy = REPO_ROOT / "metadata/taxonomy/content-taxonomy.skos.jsonld"
    document = json.loads(taxonomy.read_text(encoding="utf-8"))
    notations: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if "notation" in key:
                    notations.add(str(value))
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(document)
    declared = set(rules.topic_keywords) | set(rules.intent_keywords) | {
        rules.format_link_result,
        rules.format_default_result,
    }
    assert declared <= notations, sorted(declared - notations)
    assert rules.topic_fallback == rules.intent_fallback == "unclassified"
    assert "unclassified" not in notations


def test_ties_break_on_specification_order() -> None:
    """The specification states no tie rule; the first declared concept wins."""

    tie = ContentRules(
        spec_version="test",
        classifier_version="test",
        topic_keywords={"topic_first": ("alpha",), "topic_second": ("alpha",)},
        intent_keywords={"intent_only": ("alpha",)},
        topic_fallback="unclassified",
        intent_fallback="unclassified",
        format_url_marker="http",
        format_max_length=100,
        format_link_result="format_link",
        format_default_result="format_text",
        recorded_total=0,
        recorded_distribution={},
    )
    assert classify_text("alpha", tie)["topic_id"] == "topic_first"


def test_fallback_when_no_keyword_matches(rules: ContentRules) -> None:
    result = classify_text("zzzz no keyword here zzzz", rules)
    assert result["topic_id"] == "unclassified"
    assert result["intent_id"] == "unclassified"
    assert result["format_id"] == "format_text"


def test_format_rule_needs_both_url_and_short_text(rules: ContentRules) -> None:
    assert classify_format("see http://example.com", rules) == "format_link"
    assert classify_format("http://example.com " + "x" * 200, rules) == "format_text"
    assert classify_format("no link at all", rules) == "format_text"


def test_matching_is_case_insensitive(rules: ContentRules) -> None:
    assert classify_text("CBD liquid", rules)["topic_id"] == classify_text(
        "cbd liquid", rules
    )["topic_id"]


def test_classifier_reproduces_recorded_distribution(rules: ContentRules) -> None:
    """The committed artifact's classifications must equal the recorded run.

    This reads the published anonymized summary, so it holds in any checkout: the
    classification columns are published even though the source text is not.
    """

    import csv

    with ANONYMIZED.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == rules.recorded_total
    for dimension, recorded in (
        ("topic_id", "topic_distribution"),
        ("intent_id", "intent_distribution"),
        ("format_id", "format_distribution"),
    ):
        produced = distribution(row[dimension] for row in rows)
        assert produced == rules.recorded_distribution[recorded], dimension


@requires_private_source
def test_classifier_reproduces_the_source_texts(rules: ContentRules) -> None:
    """End-to-end check that needs the non-published source text."""

    import csv

    with PRIVATE_SOURCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    results = [classify_text(row["text"], rules) for row in rows]

    assert len(results) == rules.recorded_total
    for dimension, recorded in (
        ("topic_id", "topic_distribution"),
        ("intent_id", "intent_distribution"),
        ("format_id", "format_distribution"),
    ):
        produced = distribution(row[dimension] for row in results)
        assert produced == rules.recorded_distribution[recorded], dimension


def test_no_topic_store_is_ever_assigned(rules: ContentRules) -> None:
    """``topic_store`` is declared but absent from the recorded distribution.

    If a specification edit makes it reachable, the recorded distribution must be
    updated in the same change; this test makes that obligation visible.
    """

    assert "topic_store" in rules.topic_keywords
    assert "topic_store" not in rules.recorded_distribution["topic_distribution"]


def _write(tmp_path: Path, body: str) -> Path:
    target = tmp_path / "rules.yaml"
    target.write_text(body, encoding="utf-8")
    return target


_VALID_BODY = """
version: "1.0.0"
classifier_version: "1.0.0"

topic_keywords:
  topic_ingredient:
    - "成分"

intent_keywords:
  intent_informational:
    - "情報"

classification_logic:
  topic:
    method: "keyword_matching"
    fallback: "unclassified"
  intent:
    method: "keyword_matching"
    fallback: "unclassified"
  format:
    method: "rule_based"
    rules:
      - condition: "text に URL を含む AND text_length < 100"
        result: "format_link"
      - condition: "上記以外"
        result: "format_text"

classification_results:
  total_records: 1
  topic_distribution:
    topic_ingredient: { count: 1, percentage: 100.0 }
  intent_distribution:
    intent_informational: { count: 1, percentage: 100.0 }
  format_distribution:
    format_text: { count: 1, percentage: 100.0 }
"""


def test_minimal_valid_spec_loads(tmp_path: Path) -> None:
    parsed = load_content_rules(_write(tmp_path, _VALID_BODY))
    assert parsed.topic_keywords == {"topic_ingredient": ("成分",)}
    assert parsed.format_max_length == 100


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda body: body.replace('    fallback: "unclassified"\n  intent:', "  intent:"), "fallback"),
        (lambda body: body.replace('    - "成分"\n', ""), "without keywords"),
        (lambda body: body.replace("text_length < 100", "text_length < many"), "threshold"),
    ],
)
def test_malformed_spec_is_rejected(tmp_path: Path, mutation, expected: str) -> None:
    """A spec that cannot be read faithfully must fail loudly, not classify."""

    broken = mutation(_VALID_BODY)
    assert broken != _VALID_BODY, "mutation did not apply; the fixture drifted"
    with pytest.raises(RuleSpecError) as error:
        load_content_rules(_write(tmp_path, broken))
    assert expected in str(error.value)


def test_missing_spec_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(RuleSpecError):
        load_content_rules(tmp_path / "absent.yaml")
