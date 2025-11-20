"""Chunking strategies for documents."""
from __future__ import annotations

from textwrap import wrap
from typing import Sequence


class SimpleParagraphChunker:
    """Splits text by paragraphs and enforces a soft character limit per chunk."""

    def __init__(self, max_chars: int = 800) -> None:
        self._max_chars = max_chars

    def chunk(self, text: str) -> Sequence[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[str] = []
        for paragraph in paragraphs:
            if len(paragraph) <= self._max_chars:
                chunks.append(paragraph)
            else:
                chunks.extend(wrap(paragraph, self._max_chars))
        return chunks or [text]
