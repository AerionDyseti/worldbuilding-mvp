"""Domain service protocols for the Resonance core."""
from __future__ import annotations

from typing import Protocol, Sequence

from .entities import (
    CostEntry,
    Document,
    DocumentChunk,
    DocumentWithChunks,
    ExtractionResult,
    Relation,
    RoutingDecision,
    WorldEntity,
)


class DocumentRepository(Protocol):
    """Persistence interface used by application use cases."""

    def save_document_with_chunks(
        self, document: Document, chunk_texts: Sequence[str]
    ) -> DocumentWithChunks:
        """Persist a document and its chunk texts, returning stored models."""

    def save_entities(self, entities: Sequence[WorldEntity]) -> Sequence[WorldEntity]:
        """Persist extracted entities and return stored versions (with IDs)."""

    def search_entities(self, query: str, limit: int = 3) -> Sequence[WorldEntity]:
        """Return entities whose text matches the provided query."""

    def save_chunk_embeddings(self, vectors: Sequence[tuple[int, Sequence[float]]]) -> None:
        """Persist embedding vectors for chunk IDs."""

    def save_entity_embeddings(self, vectors: Sequence[tuple[int, Sequence[float]]]) -> None:
        """Persist embedding vectors for entity IDs."""

    def save_relations(self, relations: Sequence[Relation]) -> Sequence[Relation]:
        """Persist relationships between entities."""

    def search_entities_by_embedding(
        self, embedding: Sequence[float], limit: int = 3
    ) -> Sequence[WorldEntity]:
        """Return entities using vector similarity search."""


class Chunker(Protocol):
    """Splits raw text into manageable chunks for extraction/chat."""

    def chunk(self, text: str) -> Sequence[str]:
        """Return an ordered collection of chunk strings."""


class ExtractionService(Protocol):
    """Produces structured entities from document chunks."""

    def extract(
        self, document: Document, chunks: Sequence[DocumentChunk]
    ) -> ExtractionResult:
        """Return discovered entities and their relationships."""


class EmbeddingService(Protocol):
    """Produces dense vector representations for texts."""

    @property
    def dimension(self) -> int:
        """Return the embedding dimensionality."""

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Return a vector per input text."""


class QueryRouter(Protocol):
    """Classifies queries to determine whether to use local or API routes."""

    def classify(self, query: str) -> RoutingDecision:
        """Return a routing decision for the supplied query."""


class CostTracker(Protocol):
    """Tracks API usage costs for reporting and governance."""

    def record(self, entry: CostEntry) -> CostEntry:
        """Persist a new cost entry and return the stored record."""

    def recent(self, limit: int = 20) -> Sequence[CostEntry]:
        """Return recent cost entries for dashboards or summaries."""
