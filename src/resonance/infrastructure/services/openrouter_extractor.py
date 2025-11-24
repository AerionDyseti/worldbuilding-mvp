"""LLM-powered ExtractionService implementation backed by OpenRouter."""
from __future__ import annotations

import json
import logging
from textwrap import dedent
from typing import Iterable, List, Mapping, MutableMapping, Optional, Sequence

import httpx

from resonance.domain.entities import (
    Document,
    DocumentChunk,
    EntityType,
    ExtractionResult,
    Relation,
    WorldEntity,
)
from resonance.domain.services import ExtractionService


logger = logging.getLogger(__name__)


class OpenRouterExtractionService(ExtractionService):
    """Use OpenRouter's chat completion endpoint to extract entities/relations."""

    DEFAULT_SYSTEM_PROMPT = dedent(
        """
        You are an elite entity extraction engine for TTRPG worldbuilding notes. Given chunks of
        text, identify ALL entities (characters, locations, items, factions, events, concepts)
        and their relationships. Output JSON ONLY matching this schema:

        {
          "entities": [
            {
              "name": "string",
              "type": "character|location|item|organization|faction|event|concept",
              "description": "string",
              "chunk_index": integer,
              "attributes": {"key": "value"},
              "relations": [
                {
                  "predicate": "relationship type",
                  "target": "entity name",
                  "description": "optional"
                }
              ]
            }
          ]
        }

        Be exhaustive but concise. If unsure about a field, omit it. Never include commentary.
        """
    ).strip()

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = "https://openrouter.ai/api/v1",
        referer: Optional[str] = None,
        app_title: Optional[str] = None,
        timeout_seconds: int = 60,
        client: Optional[httpx.Client] = None,
    ) -> None:
        if not api_key:
            raise ValueError("OpenRouterExtractionService requires an API key")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._referer = referer or "https://github.com/AerionDyseti/worldbuilding-mvp"
        self._app_title = app_title or "Resonance"
        self._timeout_seconds = timeout_seconds
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        """Dispose the underlying HTTP client."""

        self._client.close()

    def extract(
        self, document: Document, chunks: Sequence[DocumentChunk]
    ) -> ExtractionResult:
        payload = {
            "model": self._model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self.DEFAULT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": self._build_user_prompt(document, chunks),
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": self._referer,
            "X-Title": self._app_title,
        }

        response = self._client.post(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        content = self._extract_content(data)
        parsed = self._safe_json_loads(content)
        return self._to_result(parsed, chunks)

    def _build_user_prompt(
        self, document: Document, chunks: Sequence[DocumentChunk]
    ) -> str:
        chunk_lines = []
        for idx, chunk in enumerate(chunks):
            header = f"### Chunk {idx}"
            chunk_lines.append(f"{header}\n{chunk.text.strip()}")
        chunk_block = "\n\n".join(chunk_lines)
        meta = f"Document: {document.title}\nWorld: {document.world_id or 'unknown'}"
        return f"{meta}\n\n{chunk_block}"

    def _extract_content(self, payload: Mapping[str, object]) -> str:
        choices = payload.get("choices") or []
        if not choices:
            raise ValueError("OpenRouter response missing choices")
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, list):
            combined = "".join(part.get("text", "") for part in content)  # type: ignore[assignment]
        else:
            combined = content or ""
        return combined

    def _safe_json_loads(self, content: str) -> MutableMapping[str, object]:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`\n")
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode OpenRouter JSON: %s", stripped)
            raise RuntimeError("OpenRouter response was not valid JSON") from exc

    def _to_result(
        self, payload: MutableMapping[str, object], chunks: Sequence[DocumentChunk]
    ) -> ExtractionResult:
        chunk_index_map = {idx: chunk for idx, chunk in enumerate(chunks)}
        raw_entities = payload.get("entities") or []
        entities: List[WorldEntity] = []
        relations: List[Relation] = []

        for entity_data in raw_entities:  # type: ignore[assignment]
            try:
                entity = self._to_entity(entity_data, chunk_index_map)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Skipping malformed entity payload: %s", exc)
                continue
            entities.append(entity)
            relations.extend(
                self._to_relations(entity_data, source_name=entity.name)
            )

        return ExtractionResult(entities=entities, relations=relations)

    def _to_entity(
        self,
        data: Mapping[str, object],
        chunk_index_map: Mapping[int, DocumentChunk],
    ) -> WorldEntity:
        raw_type = str(data.get("type", "concept")).lower()
        entity_type = self._parse_entity_type(raw_type)
        chunk_index = data.get("chunk_index")
        chunk_id = None
        if isinstance(chunk_index, int) and chunk_index in chunk_index_map:
            chunk_id = chunk_index_map[chunk_index].id

        metadata = {}
        attributes = data.get("attributes")
        if isinstance(attributes, dict):
            metadata = attributes

        description = str(data.get("description") or "")
        return WorldEntity(
            chunk_id=chunk_id,
            entity_type=entity_type,
            name=str(data.get("name") or "Unnamed"),
            description=description or "No description provided.",
            metadata=metadata,
        )

    def _parse_entity_type(self, value: str) -> EntityType:
        try:
            return EntityType(value)
        except ValueError:
            fallback_map = {
                "npc": EntityType.CHARACTER,
                "organization": EntityType.ORGANIZATION,
            }
            return fallback_map.get(value, EntityType.CONCEPT)

    def _to_relations(
        self, data: Mapping[str, object], source_name: str
    ) -> Iterable[Relation]:
        rels = data.get("relations") or []
        result: List[Relation] = []
        for rel in rels:  # type: ignore[assignment]
            predicate = str(rel.get("predicate") or rel.get("type") or "related_to")
            target = rel.get("target") or rel.get("name")
            if not target:
                continue
            result.append(
                Relation(
                    predicate=predicate,
                    subject_name=source_name,
                    object_name=str(target),
                    description=str(rel.get("description") or ""),
                )
            )
        return result
