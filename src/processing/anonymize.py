"""X (Twitter) summary -> anonymized summary derivation.

This is the transformation that produced
``datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv``
from the tracked non-anonymized summary
``datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv``.

Scope: the derivation starts at the *deduplicated* summary.  The upstream
``raw -> deduplicated summary`` step (Apify daily collection, dedup by
``tweet_id``) is **not** reproducible from repository contents because
``datasets/cbx-social-trends/data/raw/`` holds only a ``.gitkeep``.  That gap is
declared in :mod:`processing.reproduce`; it is not hidden here.

Rules, each verified against the committed artifact:

===========================  ================================================
Field                        Rule
===========================  ================================================
``tweet_id_hash``           ``sha256(tweet_id).hexdigest()[:16]``
``author_id``               ``author_NNN`` by first appearance in row order
``text_length``             ``len(text)``
``has_text``                ``yes`` when ``text`` is non-empty, else ``no``
``week``                    ``Wn`` for the Monday-anchored week, ``unknown``
                             before the anchor
``topic_id``                :mod:`processing.classify`
``intent_id``               :mod:`processing.classify`
``format_id``               :mod:`processing.classify`
``platform`` / ``language`` constants ``x_twitter`` / ``ja``
===========================  ================================================

Removed fields (privacy): ``username``, ``author_name``, ``url``, ``text``.

``docs/data-dictionary.md`` documents this mapping and is the canonical
description; ``cannabinoid-multi-trends/methodology.md`` §3.3 contradicted it
(claiming ``author_id`` was hashed) and has been corrected to point here.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime

from processing.classify import classify_text
from processing.rulespec import ContentRules

__all__ = [
    "AnonymizeError",
    "WEEK_ANCHOR",
    "ANONYMIZED_COLUMNS",
    "SOURCE_COLUMNS",
    "anonymize_rows",
]

#: Monday that starts ``W1``.  Recovered by fitting the committed artifact's week
#: labels: every row except three on 2026-08-31 matches this anchor exactly.  Those
#: three rows are labelled ``unknown`` in the artifact while this rule yields ``W5``;
#: :mod:`processing.reproduce` records them as a dated known discrepancy instead of
#: pretending the derivation is exact.
WEEK_ANCHOR = date(2026, 8, 3)

#: Column order of the committed anonymized artifact.
ANONYMIZED_COLUMNS: tuple[str, ...] = (
    "tweet_id_hash",
    "createdAt",
    "week",
    "lang",
    "author_id",
    "views",
    "likes",
    "reposts",
    "replies",
    "has_text",
    "text_length",
    "topic_id",
    "intent_id",
    "format_id",
    "platform",
    "language",
)

#: Columns this derivation reads from the non-anonymized summary.
SOURCE_COLUMNS: tuple[str, ...] = (
    "tweet_id",
    "createdAt",
    "lang",
    "username",
    "views",
    "likes",
    "reposts",
    "replies",
    "text",
)

_PLATFORM = "x_twitter"
_LANGUAGE = "ja"
_HASH_CHARS = 16


class AnonymizeError(ValueError):
    """The source rows are not in the state the documented rules assume."""


class _AuthorIndex:
    """Assigns stable sequential pseudonyms in first-appearance order."""

    def __init__(self) -> None:
        self._seen: dict[str, str] = {}

    def pseudonym(self, username: str) -> str:
        existing = self._seen.get(username)
        if existing is not None:
            return existing
        assigned = f"author_{len(self._seen) + 1:03d}"
        self._seen[username] = assigned
        return assigned


def _week_of(created_at: str) -> str:
    stamp = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
    offset = (stamp - WEEK_ANCHOR).days
    if offset < 0:
        return "unknown"
    return f"W{offset // 7 + 1}"


def anonymize_rows(
    rows: list[dict[str, str]], rules: ContentRules
) -> list[dict[str, str]]:
    """Derive the anonymized rows from deduplicated summary ``rows``.

    Row order is preserved.  A repeated ``tweet_id`` raises :class:`AnonymizeError`
    because the source is expected to be already deduplicated; silently keeping the
    first occurrence would hide an upstream regression.
    """

    seen_ids: set[str] = set()
    authors = _AuthorIndex()
    derived: list[dict[str, str]] = []

    for index, row in enumerate(rows):
        missing = [c for c in SOURCE_COLUMNS if c not in row]
        if missing:
            raise AnonymizeError(f"row {index}: missing source columns {missing}")

        tweet_id = row["tweet_id"]
        if tweet_id in seen_ids:
            raise AnonymizeError(
                f"row {index}: duplicate tweet_id {tweet_id!r}; the source summary "
                "is expected to be deduplicated upstream"
            )
        seen_ids.add(tweet_id)

        text = row["text"]
        derived.append(
            {
                "tweet_id_hash": hashlib.sha256(tweet_id.encode("utf-8")).hexdigest()[
                    :_HASH_CHARS
                ],
                "createdAt": row["createdAt"],
                "week": _week_of(row["createdAt"]),
                "lang": row["lang"],
                "author_id": authors.pseudonym(row["username"]),
                "views": row["views"],
                "likes": row["likes"],
                "reposts": row["reposts"],
                "replies": row["replies"],
                "has_text": "yes" if text.strip() else "no",
                "text_length": str(len(text)),
                **classify_text(text, rules),
                "platform": _PLATFORM,
                "language": _LANGUAGE,
            }
        )

    return derived
