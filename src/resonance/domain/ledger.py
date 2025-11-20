"""Document-level ledger for tracking extracted entities and resolving relations."""
from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Iterable, List, Optional

from .entities import Relation, WorldEntity


class DocumentLedger:
    """Maintains a mapping of canonical entity names to stored entities."""

    def __init__(self) -> None:
        self._entities: "OrderedDict[str, WorldEntity]" = OrderedDict()

    @staticmethod
    def _key(name: str) -> str:
        return name.strip().lower()

    def register_entities(self, entities: Iterable[WorldEntity]) -> list[WorldEntity]:
        """Record newly extracted entities, returning only novel ones."""
        unique: list[WorldEntity] = []
        for entity in entities:
            key = self._key(entity.name)
            if key in self._entities:
                continue
            self._entities[key] = entity
            unique.append(entity)
        return unique

    def update_with_stored(self, entities: Iterable[WorldEntity]) -> None:
        """Store entities that now have database IDs."""
        for entity in entities:
            self._entities[self._key(entity.name)] = entity

    def resolve_relations(self, relations: Iterable[Relation]) -> list[Relation]:
        """Fill in missing subject/object IDs using known entities."""
        resolved: list[Relation] = []
        for relation in relations:
            subject = self._lookup(relation.subject_entity_id, relation.subject_name)
            obj = self._lookup(relation.object_entity_id, relation.object_name)
            resolved.append(
                relation.model_copy(
                    update={
                        "subject_entity_id": subject.id if subject else relation.subject_entity_id,
                        "object_entity_id": obj.id if obj else relation.object_entity_id,
                    }
                )
            )
        return resolved

    def _lookup(self, entity_id: Optional[int], name: Optional[str]) -> Optional[WorldEntity]:
        if entity_id is not None:
            for entity in self._entities.values():
                if entity.id == entity_id:
                    return entity
            return None
        if name:
            return self._entities.get(self._key(name))
        return None
