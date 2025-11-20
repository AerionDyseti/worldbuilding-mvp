"""Application use case for answering questions about the world."""
from __future__ import annotations

from resonance.domain.services import DocumentRepository, EmbeddingService


class ChatUseCase:
    """Simple retrieval + template responder."""

    def __init__(
        self, repository: DocumentRepository, embedding_service: EmbeddingService
    ) -> None:
        self._repository = repository
        self._embedding = embedding_service

    def answer(self, query: str, limit: int = 3) -> str:
        matches = self._search(query, limit)
        if not matches:
            return "I couldn't find anything about that yet. Try ingesting more documents."

        lines = ["Here's what I know:"]
        for entity in matches:
            lines.append(f"- [{entity.entity_type.value}] {entity.name}: {entity.description}")
        return "\n".join(lines)

    def _search(self, query: str, limit: int) -> list:
        query_vec = self._embedding.embed([query])[0]
        matches = list(self._repository.search_entities_by_embedding(query_vec, limit=limit))
        if matches:
            return matches
        return list(self._repository.search_entities(query, limit=limit))
