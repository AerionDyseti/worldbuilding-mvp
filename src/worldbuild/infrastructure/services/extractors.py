"""Simple heuristic-based extractor used for the MVP."""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Sequence, Tuple

from worldbuild.domain.entities import Document, DocumentChunk, EntityType, Relation, WorldEntity
from worldbuild.domain.services import ExtractionService


class HeuristicExtractor(ExtractionService):
    """Parses chunk text for label-based entity definitions."""

    def __init__(self) -> None:
        self._label_map: Dict[str, EntityType] = {
            "character": EntityType.CHARACTER,
            "npc": EntityType.CHARACTER,
            "location": EntityType.LOCATION,
            "place": EntityType.LOCATION,
            "organization": EntityType.ORGANIZATION,
            "faction": EntityType.ORGANIZATION,
            "item": EntityType.ITEM,
            "artifact": EntityType.ITEM,
        }
        self._line_pattern = re.compile(r"^(?P<label>[A-Za-z]+)\s*[:\-]\s*(?P<body>.+)$")

    def extract(
        self, document: Document, chunks: Sequence[DocumentChunk]
    ) -> Tuple[Sequence[WorldEntity], Sequence[Relation]]:
        entities: List[WorldEntity] = []
        for chunk in chunks:
            entities.extend(self._extract_from_chunk(chunk))
        return entities, []

    def _extract_from_chunk(self, chunk: DocumentChunk) -> Iterable[WorldEntity]:
        for raw_line in chunk.text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = self._line_pattern.match(line)
            if not match:
                continue
            label = match.group("label").lower()
            entity_type = self._label_map.get(label)
            if not entity_type:
                continue
            body = match.group("body").strip()
            if not body:
                continue
            name, description = self._split_body(body)
            yield WorldEntity(
                chunk_id=chunk.id,
                entity_type=entity_type,
                name=name,
                description=description,
            )

    @staticmethod
    def _split_body(body: str) -> tuple[str, str]:
        if "-" in body:
            name, _, desc = body.partition("-")
            return name.strip(), desc.strip() or "No description provided."
        if ":" in body:
            name, _, desc = body.partition(":")
            return name.strip(), desc.strip() or "No description provided."
        parts = body.split(" ", 1)
        if len(parts) == 2:
            name, desc = parts
            return name.strip(), desc.strip() or "No description provided."
        return body.strip(), "No description provided."

