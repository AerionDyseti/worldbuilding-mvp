"""Application use case for ingesting documents."""
from __future__ import annotations

from pathlib import Path

from worldbuild.domain.entities import Document
from worldbuild.domain.ledger import DocumentLedger
from worldbuild.domain.services import (
    Chunker,
    DocumentRepository,
    EmbeddingService,
    ExtractionService,
)


class IngestDocumentUseCase:
    """Coordinates ingestion, chunking, and extraction for a document."""

    def __init__(
        self,
        repository: DocumentRepository,
        chunker: Chunker,
        extractor: ExtractionService,
        embedding_service: EmbeddingService,
    ) -> None:
        self._repository = repository
        self._chunker = chunker
        self._extractor = extractor
        self._embedding = embedding_service

    def execute(self, path: Path) -> dict[str, int]:
        """Ingest the file at `path` and return counts for reporting."""

        text = path.read_text(encoding="utf-8")
        document = Document(path=path, title=path.stem, content=text)

        chunk_texts = self._chunker.chunk(document.content)
        stored = self._repository.save_document_with_chunks(document, chunk_texts)

        # Persist chunk embeddings for downstream semantic recall.
        chunk_vectors = self._embedding.embed([chunk.text for chunk in stored.chunks])
        chunk_payload = [
            (chunk.id, vector)
            for chunk, vector in zip(stored.chunks, chunk_vectors)
            if chunk.id is not None
        ]
        self._repository.save_chunk_embeddings(chunk_payload)

        entities, relations = self._extractor.extract(stored.document, stored.chunks)

        ledger = DocumentLedger()
        novel_entities = ledger.register_entities(entities)
        stored_entities = self._repository.save_entities(novel_entities)
        ledger.update_with_stored(stored_entities)

        entity_vectors = self._embedding.embed([entity.description for entity in stored_entities])
        entity_payload = [
            (entity.id, vector)
            for entity, vector in zip(stored_entities, entity_vectors)
            if entity.id is not None
        ]
        self._repository.save_entity_embeddings(entity_payload)

        resolved_relations = ledger.resolve_relations(relations)
        self._repository.save_relations(resolved_relations)

        return {
            "chunks": len(stored.chunks),
            "entities": len(stored_entities),
            "relations": len(resolved_relations),
        }
