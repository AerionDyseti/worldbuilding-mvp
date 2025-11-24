"""Typer CLI entry point for the Resonance MVP."""
from __future__ import annotations

from pathlib import Path

import typer

from config.settings import get_settings
from resonance.application.use_cases.chat import ChatUseCase
from resonance.application.use_cases.ingest_document import IngestDocumentUseCase
from resonance.infrastructure.database.sqlite_repository import SQLAlchemyDocumentRepository
from resonance.infrastructure.services.chunkers import SimpleParagraphChunker
from resonance.infrastructure.services.embeddings import SimpleEmbeddingService
from resonance.infrastructure.services.extractors import HeuristicExtractor
from resonance.infrastructure.services.openrouter_extractor import (
    OpenRouterExtractionService,
)

settings = get_settings()

app = typer.Typer(help="Resonance worldbuilding assistant CLI")


def _build_repository() -> SQLAlchemyDocumentRepository:
    db_path = settings.sqlite_path
    if not db_path.is_absolute():
        project_root = Path(__file__).resolve().parents[4]
        db_path = (project_root / db_path).resolve()
    return SQLAlchemyDocumentRepository(db_path)


def _build_extractor():
    if settings.openrouter_api_key:
        return OpenRouterExtractionService(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
            timeout_seconds=settings.request_timeout_seconds,
        )
    return HeuristicExtractor()


def _build_ingest_use_case() -> IngestDocumentUseCase:
    repository = _build_repository()
    chunker = SimpleParagraphChunker()
    extractor = _build_extractor()
    embedding = SimpleEmbeddingService()
    return IngestDocumentUseCase(repository, chunker, extractor, embedding)


def _build_chat_use_case() -> ChatUseCase:
    repository = _build_repository()
    embedding = SimpleEmbeddingService()
    return ChatUseCase(repository, embedding)


@app.command()
def ingest(path: Path = typer.Argument(..., exists=True, readable=True, resolve_path=True)) -> None:
    """Ingest a Markdown/plain-text file into the world model."""

    use_case = _build_ingest_use_case()
    stats = use_case.execute(path)
    typer.secho(
        f"Ingested '{path.name}' -> {stats['chunks']} chunks, {stats['entities']} entities.",
        fg=typer.colors.GREEN,
    )


@app.command()
def chat(limit: int = typer.Option(3, help="Number of entities to reference per answer")) -> None:
    """Start a simple REPL for asking world questions."""

    use_case = _build_chat_use_case()
    typer.echo("Enter questions about your world (blank line to exit).\n")
    while True:
        query = typer.prompt("You")
        if not query.strip():
            typer.echo("Goodbye!")
            break
        answer = use_case.answer(query, limit=limit)
        typer.echo(answer)


if __name__ == "__main__":
    app()

