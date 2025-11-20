from __future__ import annotations

import json

from sqlalchemy import text

from resonance.domain.entities import Document, EntityType, Relation, WorldEntity
from resonance.infrastructure.database.sqlite_repository import SQLAlchemyDocumentRepository


def _store_sample_document(repository: SQLAlchemyDocumentRepository) -> tuple[int, list[int]]:
    doc = Document(path="story.md", title="Story", content="Alpha paragraph")
    stored = repository.save_document_with_chunks(doc, ["Alpha paragraph", "Beta paragraph"])
    chunk_ids = [chunk.id for chunk in stored.chunks]
    assert None not in chunk_ids
    return stored.document.id, chunk_ids  # type: ignore[return-value]


def test_save_document_with_chunks_assigns_ids(repository: SQLAlchemyDocumentRepository) -> None:
    doc = Document(path="lore.md", title="Lore", content="Line one", metadata={"tag": "canon"})
    stored = repository.save_document_with_chunks(doc, ["Line one"])
    assert stored.document.id is not None
    assert stored.chunks[0].id is not None
    assert stored.chunks[0].document_id == stored.document.id


def test_save_entities_and_search(repository: SQLAlchemyDocumentRepository) -> None:
    _, chunk_ids = _store_sample_document(repository)
    entity = WorldEntity(
        chunk_id=chunk_ids[0],
        entity_type=EntityType.CHARACTER,
        name="Aelar",
        description="Elf scout",
    )
    stored_entities = repository.save_entities([entity])
    assert stored_entities[0].id is not None

    results = repository.search_entities("aelar", limit=5)
    assert len(results) == 1
    assert results[0].name == "Aelar"


def test_save_relations_persists_records(repository: SQLAlchemyDocumentRepository) -> None:
    _, chunk_ids = _store_sample_document(repository)
    entity = repository.save_entities(
        [
            WorldEntity(
                chunk_id=chunk_ids[0],
                entity_type=EntityType.LOCATION,
                name="Ravenwood",
                description="City",
            ),
            WorldEntity(
                chunk_id=chunk_ids[1],
                entity_type=EntityType.ORGANIZATION,
                name="Highwind",
                description="Nation",
            ),
        ]
    )
    relations = repository.save_relations(
        [
            Relation(
                predicate="part_of",
                subject_entity_id=entity[0].id,
                object_entity_id=entity[1].id,
                description="Ravenwood belongs to Highwind",
            )
        ]
    )
    assert relations[0].id is not None


def test_save_embeddings_upserts_vectors(repository: SQLAlchemyDocumentRepository) -> None:
    _, chunk_ids = _store_sample_document(repository)
    stored_entity = repository.save_entities(
        [
            WorldEntity(
                chunk_id=chunk_ids[0],
                entity_type=EntityType.CHARACTER,
                name="Tester",
                description="For embeddings",
            )
        ]
    )[0]

    repository.save_chunk_embeddings([(chunk_ids[0], [0.1, 0.2])])
    repository.save_entity_embeddings([(stored_entity.id, [0.3, 0.4])])

    with repository._engine.connect() as conn:  # type: ignore[attr-defined]
        chunk_row = conn.execute(
            text("SELECT vector FROM chunk_embeddings WHERE chunk_id = :id"),
            {"id": chunk_ids[0]},
        ).fetchone()
        entity_row = conn.execute(
            text("SELECT vector FROM entity_embeddings WHERE entity_id = :id"),
            {"id": stored_entity.id},
        ).fetchone()

    assert json.loads(chunk_row[0]) == [0.1, 0.2]
    assert json.loads(entity_row[0]) == [0.3, 0.4]
