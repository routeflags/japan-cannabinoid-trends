"""G4 storage reader contract (d.md §8 reader contract / §9 reference reader).

A reader turns one stored artifact into records *without changing it*
("Readerは保存されたArtifactを読み取る。rawファイルを書き換えてはならない。").

Contract notes recorded for review
----------------------------------
- ``ArtifactDescriptor`` mirrors the §8 interface fields (artifact id /
  artifact type / format / schema id / path) plus the manifest facts a reader
  may need (layer / completeness / record count / contains_full_timeseries).
- ``read`` requires a *known* meaning: a mode the reader does not implement
  raises ``UnsupportedRead`` instead of returning an approximation.  Reading a
  ``summary`` as a full timeseries is therefore refused, never reconstructed
  (d.md §12 / P8).
- ``validate`` returns human-readable violations (the same convention as the
  G1 adapter ``validate_plan``); ``validation.storage_contract`` maps them to
  stable issue codes.
- ``count`` returns the record count this reader can actually determine, or
  ``None``.  It never returns a guessed number: a summary's declared
  ``data_points`` is not a record count, and a database's row count belongs to
  a table, not to the file (d.md §6.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "ArtifactDescriptor",
    "ReaderError",
    "StorageReader",
    "UnsupportedRead",
]


@dataclass(frozen=True)
class ArtifactDescriptor:
    """The subset of a manifest artifact entry a reader needs (d.md §8).

    ``path`` is already resolved by the caller (absolute for local reads,
    or ``base_dir / manifest.path`` built by the validation layer).
    """

    artifact_id: str
    artifact_type: str | None
    format: str
    schema_id: str | None
    path: str
    layer: str | None = None
    completeness: str | None = None
    record_count: int | None = None
    contains_full_timeseries: bool | None = None

    @classmethod
    def from_manifest_artifact(cls, artifact: dict, base_dir) -> "ArtifactDescriptor":
        """Build a descriptor from a manifest artifact entry (read-only)."""
        base = Path(base_dir)
        return cls(
            artifact_id=str(artifact.get("artifact_id")),
            artifact_type=artifact.get("artifact_type"),
            format=artifact.get("format"),
            schema_id=artifact.get("schema_id"),
            path=str(base / str(artifact.get("path"))),
            layer=artifact.get("layer"),
            completeness=artifact.get("completeness"),
            record_count=artifact.get("record_count"),
            contains_full_timeseries=artifact.get("contains_full_timeseries"),
        )

    def resolve(self) -> Path:
        """The artifact path as given (callers resolve base directories)."""
        return Path(self.path)


class ReaderError(Exception):
    """A read could not be completed (I/O failure, malformed content)."""


class UnsupportedRead(ReaderError):
    """The requested read mode is not part of this reader's contract.

    Raised instead of approximating: a series that is not stored must never
    be reconstructed (d.md §12 / P8).
    """


class StorageReader:
    """Base class for storage readers (d.md §8).

    Subclasses declare their identity (``reader_id`` / ``reader_version``),
    the formats / artifact types they cover and the read modes they
    implement.  All methods are read-only.
    """

    reader_id = ""
    reader_version = "0.0.0"
    formats: tuple[str, ...] = ()
    artifact_types: tuple[str, ...] = ()
    read_modes: tuple[str, ...] = ()
    #: True / False when the contract decides whether the artifact carries
    #: per-bucket values; None when the question does not apply (d.md §12).
    contains_full_timeseries: bool | None = None

    def supports(self, artifact: ArtifactDescriptor) -> bool:
        """True when this reader can be asked to read ``artifact``."""
        if artifact.format not in self.formats:
            return False
        if artifact.artifact_type is not None:
            return artifact.artifact_type in self.artifact_types
        return True

    def validate(self, artifact: ArtifactDescriptor) -> list[str]:
        """Return human-readable violations (empty list = conforms)."""
        return []

    def read(
        self,
        artifact: ArtifactDescriptor,
        *,
        mode: str | None = None,
        limit: int | None = None,
        table: str | None = None,
    ):
        """Yield normalized records; unknown modes raise ``UnsupportedRead``.

        ``table`` applies to database readers only (d.md §13); other readers
        ignore it and overrides without the keyword fail loudly rather than
        silently dropping it.
        """
        raise UnsupportedRead(
            f"{self.reader_id} does not implement read mode {mode!r}"
        )

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        """Record count this reader can determine, or None (never guessed)."""
        return None
