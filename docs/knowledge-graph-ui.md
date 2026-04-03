# Knowledge graph (JSON store) — UI and API

The **Knowledge Base** page (`frontend/src/pages/Knowledge.tsx`) includes a **Knowledge graph** card that visualizes entities and relationships from `PersistentJSONKnowledgeStore` (default file `dev/knowledge_graph.json`).

## CLI

From the GRID repo root (`PYTHONPATH` via `uv run`):

```bash
uv run python -m grid knowledge ingest path/to/doc.md
uv run python -m grid knowledge stats
```

Flags for ingest: `--heuristic` (no Ollama), `--model`, `--index-vectors`.

## HTTP (Mothership)

Mounted under the app’s `/api/v1` prefix:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/knowledge/stats` | Entity/relationship counts, `storage_path` |
| GET | `/api/v1/knowledge/graph` | `nodes`, `edges`, `storage_path`, `total_entities`, `truncated` |
| GET | `/api/v1/knowledge/graph?max_nodes=N` | Same, but at most `N` entities (by stable entity id order); edges only between included nodes |
| POST | `/api/v1/knowledge/ingest` | JSON body (`IngestRequest`) |
| POST | `/api/v1/knowledge/ingest/file` | Multipart upload |

## Frontend

- Hooks: `useKnowledgeGraphStats()`, `useKnowledgeGraph({ maxNodes?: number })` in `frontend/src/hooks/use-queries.ts`.
- Responses are validated in `frontend/src/lib/knowledge-api-guards.ts` so malformed JSON objects (for example `{}` with HTTP 200) surface as query errors instead of a silent empty graph.
- The Knowledge page uses `KNOWLEDGE_GRAPH_UI_MAX_NODES` (default 500) to keep the SVG layout responsive; when the API returns `truncated: true`, a short notice explains how to load the full graph.
- Renderer-only dev: `frontend/src/lib/browser-shim.ts` serves demo `stats` / `graph` payloads; query strings are ignored for lookup (path before `?`).

## Visualization encoding

- **Document** vs **Concept** nodes: different radius and styling (`KnowledgeGraphCanvas.tsx`).
- **EXPLAINS**: dashed edges; **CONNECTS_TO**: solid (`type` on each edge).

## Related code

- Export: `src/grid/knowledge/persistent_store.py` — `export_graph_visualization(max_nodes=...)`
- Router: `src/application/mothership/routers/knowledge.py`
- Types: `frontend/src/types/api.ts` — `KnowledgeGraphPayload`, etc.
