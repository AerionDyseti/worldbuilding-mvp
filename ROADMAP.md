# Resonance MVP Roadmap

## 0. Foundation (Done)
- Clean/DDD-inspired structure (`domain`, `application`, `infrastructure`, `presentation`).
- CLI workflow (Typer) with ingestion + chat commands.
- SQLite store via SQLAlchemy Core + Alembic migrations.
- Deterministic embedding stub + heuristic extractor wired through document ledger.

## 1. Short-Term Enhancements (Next Up)
1. **Embedding Infrastructure**
   - Swap `SimpleEmbeddingService` for a real local model (ONNX/GGUF such as `bge-small` or `gte-small`).
   - Introduce sqlite_vec tables/functions for true vector similarity search.
2. **Extraction Improvements**
   - Prompt/LLM-based extractor capable of free-form fiction/session notes.
   - Relation extraction that leverages `DocumentLedger` context and emits predicates (ownership, allegiance, conflict, etc.).
3. **Quality + Testing**
   - Unit tests for ledger dedupe/resolve, repository persistence, and chat retrieval fallback logic.
   - CLI smoke tests (ingest + chat) using fixture documents.
4. **DX/Tooling**
   - Add Make/Invoke/Taskfile helpers (`uv run resonance ingest samples/...`).
   - GitHub Actions for lint/test (uv-powered).

## 2. Medium-Term Goals
1. **Interactive Review UX**
   - TUI (Textual/Rich) reviewer for confirming/updating extracted entities and relations.
   - API endpoints that mirror review actions for future web UI.
2. **Entity System Expansion**
   - Custom entity schemas (e.g., Ancestries, Cultures, Story levels, Mechanics) with subtype tables or JSON schemas.
   - Tagging/metadata UX powered by the key-value `metadata` fields.
3. **Richer Retrieval & Chat**
   - Retrieval-augmented answers citing chunk IDs and relation summaries.
   - Relation-aware queries (“How is Ravenwood connected to Highwind?”).
4. **Content Ingestion Pipeline**
   - Support additional document formats (DOCX, PDF) and multi-file ingestion sessions.
   - Background job queue for long extractions.

## 3. Long-Term Vision
1. **Consistency & Validation**
   - Constraint rules (timeline conflicts, duplicate names, lore contradictions).
   - Automated consistency reports surfaced in UI/chat.
2. **Alternate Timelines / AUs**
   - Versioned entities + branching relations enabling “what-if” scenarios.
   - Diff tooling to compare timelines.
3. **Model Specialization Pipeline**
   - Data export + fine-tuning scripts for extraction/chat models.
   - Support for custom embeddings and instruct-tuned LLMs per campaign/fiction universe.
4. **UI Ecosystem**
   - Web client (React/Vue/Solid) backed by FastAPI/GraphQL service.
   - Plugin hooks so DMs/writers can attach custom automations.

## 4. Stretch Ideas / Maybe Later
- **Consistency watchtower**: real-time alerts when new text conflicts with canon.
- **World simulation hooks**: run mechanics or events that mutate entities.
- **Collaboration mode**: multi-user annotations, role-based access.
- **Import/export**: Obsidian, Notion, Foundry VTT integrations.

## Guiding Principles
- Prefer clean boundaries (domain/application/infrastructure) to keep swap-able implementations.
- Own the data locally (SQLite first, easy migration to Postgres when needed).
- Optimize for local/offline workflows with later optional services.
