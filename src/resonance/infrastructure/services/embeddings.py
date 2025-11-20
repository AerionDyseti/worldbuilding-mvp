"""Simple embedding service stub for MVP."""
from __future__ import annotations

import hashlib
import random
from typing import Sequence

from resonance.domain.services import EmbeddingService


class SimpleEmbeddingService(EmbeddingService):
    """Generates deterministic pseudo-random embeddings via hashing."""

    def __init__(self, dimension: int = 64) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:  # pragma: no cover - simple getter
        return self._dimension

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest(), "big")
            rng = random.Random(seed)
            vectors.append([rng.random() for _ in range(self._dimension)])
        return vectors

