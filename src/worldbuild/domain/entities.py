"""Domain models for worldbuilding documents and entities."""
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


class Document(BaseModel):
    """Represents a source file that has been ingested."""

    id: Optional[int] = None
    path: Path
    title: str
    content: str
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
