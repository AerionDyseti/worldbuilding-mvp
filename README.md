## Resonance MVP

Minimal CLI-first assistant that ingests Markdown/plain-text documents, extracts key world entities, stores them in SQLite, and exposes a simple chat loop for retrieval.

### Features (current slice)

1. `resonance ingest <path>` – reads a file, stores it, chunks content, runs a heuristic extractor (Characters/Locations/Organizations/Items), and persists results.
2. `resonance chat` – opens a REPL where you can ask questions; responses reference the most relevant stored entities.

### Getting started

```bash
pip install -e .
resonance ingest path/to/file.md
resonance chat
```

The SQLite database is stored under `data/resonance.db`. Delete the file to reset the catalog.

### Architecture notes

- **Domain**: value objects + service interfaces for ingestion/extraction/chat.
- **Application**: use cases orchestrating repositories and domain services.
- **Infrastructure**: SQLite persistence, chunker/extractor implementations, chat responder.
- **Presentation**: Typer CLI wrapping the application layer.

This structure keeps dependencies flowing inward, so future UI/service layers can reuse the same core logic.
