"""G6 §14 storage backend contract (local filesystem only for this slice).

Contract sources
----------------
- G6 instruction §14 (``StorageBackend`` with ``putImmutable`` refusing
  overwrites): ``docs/plans/20261013f.md``.
- AGENTS.md pipeline (``raw/`` -> ``interim/`` -> ``processed/``) is unchanged;
  the backend only declares *where* bytes live, never what they mean.

Scope
-----
``LocalFilesystemBackend`` implements the §14 contract for one root
directory: ``put_immutable`` refuses to overwrite an existing artifact id
(G6-T18), ``verify`` recomputes SHA-256 read-only, and missing artifacts
are reported as missing, never as zero content (P8).  Cloud / object
storage backends are future work and are not introduced here.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

__all__ = ["BackendOverwriteRefused", "LocalFilesystemBackend"]


class BackendOverwriteRefused(Exception):
    """Raised when ``put_immutable`` targets an existing artifact id."""


class LocalFilesystemBackend:
    """Local-filesystem §14 backend (one artifact id -> one file)."""

    def __init__(self, root) -> None:
        self._root = Path(root)
        self.backend_id = "local-filesystem"

    @property
    def root(self) -> Path:
        return self._root

    def _target(self, artifact_id: str) -> Path:
        if not artifact_id or not isinstance(artifact_id, str):
            raise ValueError("artifact_id must be a non-empty string")
        candidate = Path(artifact_id)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("artifact_id must stay inside the backend root")
        return self._root / candidate

    def put_immutable(self, artifact_id: str, data: bytes) -> str:
        """Store ``data`` once; refuse overwrites (G6-T18)."""
        target = self._target(artifact_id)
        if target.exists():
            raise BackendOverwriteRefused(f"artifact already stored: {artifact_id}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    def get(self, artifact_id: str) -> bytes:
        return self._target(artifact_id).read_bytes()

    def exists(self, artifact_id: str) -> bool:
        return self._target(artifact_id).is_file()

    def verify(self, artifact_id: str, sha256: str) -> bool:
        target = self._target(artifact_id)
        if not target.is_file():
            return False
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        return digest == sha256
