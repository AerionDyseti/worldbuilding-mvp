"""SQLAlchemy Core models backing the worldbuild storage layer."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata_obj = MetaData()


documents = Table(
    "documents",
    metadata_obj,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("path", Text, nullable=False),
    Column("title", String(255), nullable=False),
    Column("content", Text, nullable=False),
    Column("metadata", Text, nullable=False, default="{}"),
    Column("ingested_at", DateTime, nullable=False, default=datetime.utcnow),
)


chunks = Table(
    "chunks",
    metadata_obj,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
    Column("chunk_index", Integer, nullable=False),
    Column("text", Text, nullable=False),
    Column("metadata", Text, nullable=False, default="{}"),
    UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_index"),
)


entities = Table(
    "entities",
    metadata_obj,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("chunk_id", Integer, ForeignKey("chunks.id", ondelete="SET NULL")),
    Column("entity_type", String(64), nullable=False),
    Column("name", String(255), nullable=False),
    Column("description", Text, nullable=False),
    Column("metadata", Text, nullable=False, default="{}"),
)


relations = Table(
    "relations",
    metadata_obj,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("predicate", String(128), nullable=False),
    Column("subject_entity_id", Integer, ForeignKey("entities.id", ondelete="SET NULL")),
    Column("subject_name", String(255)),
    Column("object_entity_id", Integer, ForeignKey("entities.id", ondelete="SET NULL")),
    Column("object_name", String(255)),
    Column("description", Text),
    Column("metadata", Text, nullable=False, default="{}"),
)


chunk_embeddings = Table(
    "chunk_embeddings",
    metadata_obj,
    Column("chunk_id", Integer, ForeignKey("chunks.id", ondelete="CASCADE"), primary_key=True),
    Column("vector", Text, nullable=False),
)


entity_embeddings = Table(
    "entity_embeddings",
    metadata_obj,
    Column("entity_id", Integer, ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
    Column("vector", Text, nullable=False),
)


