"""Reader for the rule-based content-classifier specification.

``metadata/taxonomy/classification-rules.yaml`` is the single source of truth for
the rule-based content classifier (``classifier_version`` 1.0.0).  The
specification defines keyword lists per topic/intent concept plus the format rule,
and records the distribution its own 2026-10-02 run produced.

The repository declares exactly one third-party Python dependency (cerberus; see
``pyproject.toml``), so this module reads the documented subset of that file
directly instead of importing a YAML library.  Nothing else in the repository
reads YAML, so the dependency decision stays isolated here.

Two choices are deliberate:

1. The reader is *strict*.  A keyword group that parses to zero entries, a missing
   fallback, or an unparsable format threshold raises :class:`RuleSpecError`
   rather than silently producing a classifier that would mislabel records.
2. :func:`load_content_rules` returns the recorded distribution, so
   :mod:`processing.reproduce` can check the parse + classifier combination
   against the specification's own expected output.

If the repository later adopts a YAML library or moves the specification to JSON,
only :func:`load_content_rules` needs to change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "ContentRules",
    "RuleSpecError",
    "DEFAULT_RULES_PATH",
    "load_content_rules",
]

#: Repository-relative default location of the classifier specification.
DEFAULT_RULES_PATH = "metadata/taxonomy/classification-rules.yaml"

_KEYWORD_GROUPS = ("topic_keywords", "intent_keywords")
_DISTRIBUTION_GROUPS = (
    "topic_distribution",
    "intent_distribution",
    "format_distribution",
)

#: \u300ctext \u306b URL \u3092\u542b\u3080\u300d is operationalized as this literal marker.  It is the
#: minimal marker that reproduces the committed artifact, and the spec phrase alone
#: does not fix an implementation, so the choice is recorded here explicitly.
_URL_MARKER = "http"


class RuleSpecError(ValueError):
    """The classifier specification could not be read as documented."""


@dataclass(frozen=True)
class ContentRules:
    """Parsed content-classifier specification.

    ``topic_keywords`` / ``intent_keywords`` preserve the specification's key
    order.  That order is part of the contract: the classifier breaks keyword-count
    ties by taking the first concept in file order (see
    :mod:`processing.classify`).
    """

    spec_version: str
    classifier_version: str
    topic_keywords: dict[str, tuple[str, ...]]
    intent_keywords: dict[str, tuple[str, ...]]
    topic_fallback: str
    intent_fallback: str
    format_url_marker: str
    format_max_length: int
    format_link_result: str
    format_default_result: str
    recorded_total: int
    recorded_distribution: dict[str, dict[str, int]]


class _Parser:
    """Line-oriented reader for the specification's documented YAML subset."""

    def __init__(self, text: str, origin: str) -> None:
        self._origin = origin
        self.scalars: dict[str, str] = {}
        self.keywords: dict[str, dict[str, list[str]]] = {
            group: {} for group in _KEYWORD_GROUPS
        }
        self.logic: dict[str, dict[str, str]] = {}
        self.format_rules: list[dict[str, str]] = []
        self.recorded_scalars: dict[str, str] = {}
        self.recorded_distribution: dict[str, dict[str, int]] = {}
        self._parse(text)

    def _fail(self, message: str) -> RuleSpecError:
        return RuleSpecError(f"{self._origin}: {message}")

    def _parse(self, text: str) -> None:
        section: str | None = None
        subgroup: str | None = None
        logic_block: str | None = None
        distribution: str | None = None

        for raw in text.splitlines():
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip())
            line = raw.strip()

            if indent == 0:
                subgroup = logic_block = distribution = None
                if line.endswith(":"):
                    section = line[:-1].strip()
                else:
                    section = None
                    key, _, value = line.partition(":")
                    self.scalars[key.strip()] = _unquote(value.strip())
                continue

            if section in _KEYWORD_GROUPS:
                if indent == 2 and line.endswith(":"):
                    subgroup = line[:-1].strip()
                    self.keywords[section][subgroup] = []
                elif indent == 4 and line.startswith("- "):
                    if subgroup is None:
                        raise self._fail(f"keyword outside a group: {line!r}")
                    self.keywords[section][subgroup].append(_unquote(line[2:].strip()))
                continue

            if section == "classification_logic":
                if indent == 2 and line.endswith(":"):
                    logic_block = line[:-1].strip()
                    self.logic[logic_block] = {}
                elif indent == 4 and not line.startswith("- "):
                    if logic_block is None:
                        raise self._fail(f"logic entry outside a block: {line!r}")
                    key, _, value = line.partition(":")
                    self.logic[logic_block][key.strip()] = _unquote(value.strip())
                elif indent == 6 and line.startswith("- "):
                    key, _, value = line[2:].partition(":")
                    self.format_rules.append({key.strip(): _unquote(value.strip())})
                elif indent >= 8:
                    if not self.format_rules:
                        raise self._fail(f"rule attribute without a rule: {line!r}")
                    key, _, value = line.partition(":")
                    self.format_rules[-1][key.strip()] = _unquote(value.strip())
                continue

            if section == "classification_results":
                if indent == 2 and line.endswith(":"):
                    distribution = line[:-1].strip()
                    if distribution in _DISTRIBUTION_GROUPS:
                        self.recorded_distribution[distribution] = {}
                elif indent == 2:
                    key, _, value = line.partition(":")
                    self.recorded_scalars[key.strip()] = _unquote(value.strip())
                elif indent >= 4 and distribution in _DISTRIBUTION_GROUPS:
                    key, _, value = line.partition(":")
                    match = re.search(r"count:\s*(\d+)", value)
                    if match is None:
                        raise self._fail(f"distribution entry without a count: {line!r}")
                    self.recorded_distribution[distribution][_unquote(key.strip())] = int(
                        match.group(1)
                    )
                continue

    def build(self) -> ContentRules:
        for group in _KEYWORD_GROUPS:
            if group not in self.keywords or not self.keywords[group]:
                raise self._fail(f"missing or empty keyword group {group!r}")
            empty = [n for n, words in self.keywords[group].items() if not words]
            if empty:
                raise self._fail(f"keyword groups without keywords in {group}: {empty}")

        for block in ("topic", "intent"):
            if block not in self.logic:
                raise self._fail(f"missing classification_logic.{block}")
            if not self.logic[block].get("fallback"):
                raise self._fail(f"classification_logic.{block} has no fallback")

        link_rule = self._format_rule(link=True)
        default_rule = self._format_rule(link=False)
        condition = link_rule.get("condition", "")
        threshold = re.search(r"text_length\s*<\s*(\d+)", condition)
        if threshold is None:
            raise self._fail(
                f"format rule condition has no 'text_length < N' threshold: {condition!r}"
            )

        missing = [g for g in _DISTRIBUTION_GROUPS if g not in self.recorded_distribution]
        if missing:
            raise self._fail(f"missing recorded distributions: {missing}")

        return ContentRules(
            spec_version=self.scalars.get("version", ""),
            classifier_version=self.scalars.get("classifier_version", ""),
            topic_keywords={n: tuple(w) for n, w in self.keywords["topic_keywords"].items()},
            intent_keywords={n: tuple(w) for n, w in self.keywords["intent_keywords"].items()},
            topic_fallback=self.logic["topic"]["fallback"],
            intent_fallback=self.logic["intent"]["fallback"],
            format_url_marker=_URL_MARKER,
            format_max_length=int(threshold.group(1)),
            format_link_result=link_rule.get("result", ""),
            format_default_result=default_rule.get("result", ""),
            recorded_total=int(self.recorded_scalars.get("total_records", 0)),
            recorded_distribution={
                g: dict(v) for g, v in self.recorded_distribution.items()
            },
        )

    def _format_rule(self, *, link: bool) -> dict[str, str]:
        if not self.format_rules:
            raise self._fail("missing classification_logic.format.rules")
        for rule in self.format_rules:
            result = rule.get("result", "")
            if ("link" in result) is link:
                return rule
        raise self._fail(f"no format rule whose result marks link={link}")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def load_content_rules(
    path: str | Path = DEFAULT_RULES_PATH, *, repo_root: str | Path | None = None
) -> ContentRules:
    """Load and validate the classifier specification.

    ``path`` may be absolute or relative; a relative path resolves against
    ``repo_root`` (then the working directory).  Raises :class:`RuleSpecError`
    when the file does not match the documented structure, and ``OSError`` when it
    cannot be read.
    """

    resolved = Path(path)
    if not resolved.is_absolute():
        base = Path(repo_root) if repo_root is not None else Path.cwd()
        resolved = base / resolved
    if not resolved.is_file():
        raise RuleSpecError(f"classifier specification not found: {resolved}")
    return _Parser(resolved.read_text(encoding="utf-8"), str(resolved)).build()
