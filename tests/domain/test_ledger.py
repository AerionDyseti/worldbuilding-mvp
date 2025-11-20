from __future__ import annotations

from resonance.domain.entities import Relation, WorldEntity
from resonance.domain.ledger import DocumentLedger
from resonance.domain.entities import EntityType


def make_entity(name: str, entity_id: int | None = None) -> WorldEntity:
    return WorldEntity(id=entity_id, name=name, description="desc", entity_type=EntityType.LOCATION)


def make_relation(subject: str | None, obj: str | None) -> Relation:
    return Relation(predicate="ally_of", subject_name=subject, object_name=obj)


def test_register_entities_dedupes_by_name() -> None:
    ledger = DocumentLedger()
    saved = ledger.register_entities([make_entity("Alpha"), make_entity("alpha"), make_entity("Beta")])
    assert len(saved) == 2
    assert [entity.name for entity in saved] == ["Alpha", "Beta"]


def test_update_with_stored_overwrites_ids() -> None:
    ledger = DocumentLedger()
    ledger.register_entities([make_entity("Alpha")])
    ledger.update_with_stored([make_entity("Alpha", entity_id=42)])
    resolved = ledger.resolve_relations([make_relation("Alpha", None)])
    assert resolved[0].subject_entity_id == 42


def test_resolve_relations_handles_missing_entities() -> None:
    ledger = DocumentLedger()
    result = ledger.resolve_relations([make_relation(None, None)])
    assert result[0].subject_entity_id is None
    assert result[0].object_entity_id is None
