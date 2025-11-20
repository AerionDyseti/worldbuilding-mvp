"""SQLite-backed repositories for documents and entities via SQLAlchemy."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from sqlalchemy import create_engine, insert, or_, select, text
from sqlalchemy.engine import Engine

from worldbuild.domain.entities import (
    Document,
    DocumentChunk,
    DocumentWithChunks,
    EntityType,
    Relation,
    WorldEntity,
)
from worldbuild.domain.services import DocumentRepository

from . import models


class SQLAlchemyDocumentRepository(DocumentRepository):
    """DocumentRepository implementation backed by SQLAlchemy Core."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine: Engine = create_engine(
            f"sqlite:///{self._db_path}", future=True, echo=False, pool_pre_ping=True
        )
        with self._engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys=ON"))
        # Ensure tables exist for initial runs; Alembic can take over afterward.
        models.metadata_obj.create_all(self._engine)

    def save_document_with_chunks(
        self, document: Document, chunk_texts: Sequence[str]
    ) -> DocumentWithChunks:
        doc_metadata = json.dumps(document.metadata or {})
        with self._engine.begin() as conn:
            doc_result = conn.execute(
                insert(models.documents).values(
                    path=str(document.path),
                    title=document.title,
                    content=document.content,
                    metadata=doc_metadata,
                    ingested_at=document.ingested_at,
                )
            )
            document_id = doc_result.inserted_primary_key[0]
            stored_doc = document.model_copy(update={"id": document_id})

            stored_chunks: list[DocumentChunk] = []
            for index, chunk_text in enumerate(chunk_texts):
                chunk_result = conn.execute(
                    insert(models.chunks).values(
                        document_id=document_id,
                        chunk_index=index,
                        text=chunk_text,
                        metadata=json.dumps({}),
                    )
                )
                chunk_id = chunk_result.inserted_primary_key[0]
                stored_chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        document_id=document_id,
                        chunk_index=index,
                        text=chunk_text,
                    )
                )

        return DocumentWithChunks(document=stored_doc, chunks=stored_chunks)

    def save_entities(self, entities: Sequence[WorldEntity]) -> Sequence[WorldEntity]:
        if not entities:
            return []

        stored_entities: list[WorldEntity] = []
        with self._engine.begin() as conn:
            for entity in entities:
                result = conn.execute(
                    insert(models.entities).values(
                        chunk_id=entity.chunk_id,
                        entity_type=entity.entity_type.value,
                        name=entity.name,
                        description=entity.description,
                        metadata=json.dumps(entity.metadata or {}),
                    )
                )
                entity_id = result.inserted_primary_key[0]
                stored_entities.append(entity.model_copy(update={"id": entity_id}))
        return stored_entities

    def save_relations(self, relations: Sequence[Relation]) -> Sequence[Relation]:
        if not relations:
            return []

        stored_relations: list[Relation] = []
        with self._engine.begin() as conn:
            for relation in relations:
                result = conn.execute(
                    insert(models.relations).values(
                        predicate=relation.predicate,
                        subject_entity_id=relation.subject_entity_id,
                        subject_name=relation.subject_name,
                        object_entity_id=relation.object_entity_id,
                        object_name=relation.object_name,
                        description=relation.description,
                        metadata=json.dumps(relation.metadata or {}),
                    )
                )
                relation_id = result.inserted_primary_key[0]
                stored_relations.append(relation.model_copy(update={"id": relation_id}))
        return stored_relations

    def save_chunk_embeddings(self, vectors: Sequence[tuple[int, Sequence[float]]]) -> None:
        if not vectors:
            return
        with self._engine.begin() as conn:
            for chunk_id, vector in vectors:
                conn.execute(
                    insert(models.chunk_embeddings)
                    .values(chunk_id=chunk_id, vector=json.dumps(list(vector)))
                    .on_conflict_do_update(  # type: ignore[attr-defined]
                        index_elements=[models.chunk_embeddings.c.chunk_id],
                        set_={"vector": json.dumps(list(vector))},
                    )
                )

    def save_entity_embeddings(self, vectors: Sequence[tuple[int, Sequence[float]]]) -> None:
        if not vectors:
            return
        with self._engine.begin() as conn:
            for entity_id, vector in vectors:
                conn.execute(
                    insert(models.entity_embeddings)
                    .values(entity_id=entity_id, vector=json.dumps(list(vector)))
                    .on_conflict_do_update(  # type: ignore[attr-defined]
                        index_elements=[models.entity_embeddings.c.entity_id],
                        set_={"vector": json.dumps(list(vector))},
                    )
                )

    def search_entities(self, query: str, limit: int = 3) -> Sequence[WorldEntity]:
        pattern = f"%{query}%"
        stmt = (
            select(models.entities)
            .where(
                or_(
                    models.entities.c.name.ilike(pattern),
                    models.entities.c.description.ilike(pattern),
                )
            )
            .order_by(models.entities.c.id.desc())
            .limit(limit)
        )
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        return [self._row_to_entity(row) for row in rows]

    def search_entities_by_embedding(
        self, embedding: Sequence[float], limit: int = 3
    ) -> Sequence[WorldEntity]:
        # Placeholder until sqlite_vec integration lands; fall back to recency ordering.
        stmt = select(models.entities).order_by(models.entities.c.id.desc()).limit(limit)
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        return [self._row_to_entity(row) for row in rows]

    def _row_to_entity(self, row) -> WorldEntity:
        metadata = json.loads(row.metadata or "{}")
        return WorldEntity(
            id=row.id,
            chunk_id=row.chunk_id,
            entity_type=EntityType(row.entity_type),
            name=row.name,
            description=row.description,
            metadata=metadata,
        )
