from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

from resonance.infrastructure.database.sqlite_repository import SQLAlchemyDocumentRepository
from resonance.infrastructure.services.embeddings import SimpleEmbeddingService


@pytest.fixture()
def temp_db_path(tmp_path: Path) -> Path:
    db_path = tmp_path / "resonance.db"
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture()
def repository(temp_db_path: Path):
    repo = SQLAlchemyDocumentRepository(temp_db_path)
    try:
        yield repo
    finally:
        repo.dispose()


@pytest.fixture()
def embedding_service() -> SimpleEmbeddingService:
    return SimpleEmbeddingService(dimension=8)
