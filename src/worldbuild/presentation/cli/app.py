"""Typer CLI entry point for the worldbuild MVP."""
from __future__ import annotations

from pathlib import Path

import typer

from worldbuild.application.use_cases.chat import ChatUseCase
from worldbuild.application.use_cases.ingest_document import IngestDocumentUseCase
from worldbuild.infrastructure.database.sqlite_repository import SQLAlchemyDocumentRepository
from worldbuild.infrastructure.services.chunkers import SimpleParagraphChunker
from worldbuild.infrastructure.services.extractors import HeuristicExtractor
from worldbuild.infrastructure.services.embeddings import SimpleEmbeddingService

app = typer.Typer(help="Worldbuilding assistant CLI")


def _build_repository() -> SQLAlchemyDocumentRepository:
    project_root = Path(__file__).resolve().parents[4]
    db_path = project_root / "data" / "worldbuild.db"
    return SQLAlchemyDocumentRepository(db_path)


def _build_ingest_use_case() -> IngestDocumentUseCase:
    repository = _build_repository()
    chunker = SimpleParagraphChunker()
    extractor = HeuristicExtractor()
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

