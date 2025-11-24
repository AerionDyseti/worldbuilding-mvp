"""Domain models for Resonance documents and entities."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Sequence

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Supported entity categories for the MVP."""

    CHARACTER = "character"
    LOCATION = "location"
    ORGANIZATION = "organization"
    ITEM = "item"
    FACTION = "faction"
    EVENT = "event"
    CONCEPT = "concept"


class DocumentType(str, Enum):
    """Document types for DM's Ark ingestion pipeline."""

    TRANSCRIPT = "transcript"
    SUMMARY = "summary"
    HIGHLIGHTS = "highlights"
    GENERIC = "generic"


class QueryRoute(str, Enum):
    """Routing strategy for query processing."""

    LOCAL = "local"
    API_SUGGESTED = "api_suggested"
    API_FORCED = "api_forced"


class Document(BaseModel):
    """Represents a source file that has been ingested."""

    id: Optional[int] = None
    path: Path
    title: str
    content: str
    document_type: DocumentType = DocumentType.GENERIC
    session_number: Optional[int] = None
    world_id: Optional[str] = None
    metadata: Dict[str, Optional[str]] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    """A chunked slice of a document used for extraction and chat context."""

    id: Optional[int] = None
    document_id: Optional[int] = None
    chunk_index: int
    text: str
    metadata: Dict[str, Optional[str]] = Field(default_factory=dict)


class DocumentWithChunks(BaseModel):
    """Value object bundling a stored document with its chunks."""

    document: Document
    chunks: Sequence[DocumentChunk]


class ExtractionResult(BaseModel):
    """Bundle of entities and relations produced from extraction."""

    entities: Sequence[WorldEntity] = Field(default_factory=list)
    relations: Sequence[Relation] = Field(default_factory=list)


class WorldEntity(BaseModel):
    """Structured entity captured from the world."""

    id: Optional[int] = None
    chunk_id: Optional[int] = None
    entity_type: EntityType
    name: str
    description: str
    metadata: Dict[str, Optional[str]] = Field(default_factory=dict)


class Relation(BaseModel):
    """Directional relationship between two entities (by ID or name)."""

    id: Optional[int] = None
    predicate: str
    subject_entity_id: Optional[int] = None
    subject_name: Optional[str] = None
    object_entity_id: Optional[int] = None
    object_name: Optional[str] = None
    description: str | None = None
    metadata: Dict[str, Optional[str]] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    """Routing decision for query processing with cost estimation."""

    route: QueryRoute
    estimated_cost: Optional[float] = None
    reasoning: str


class CostEntry(BaseModel):
    """Record of API usage costs for tracking and reporting."""

    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_name: str
    input_tokens: int
    output_tokens: int
    total_cost: float
    operation: str  # e.g., "extract_entities", "query_world"
    metadata: Dict[str, Optional[str]] = Field(default_factory=dict)
