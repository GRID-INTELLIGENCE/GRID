# GRID Architecture Summary

## Executive Summary

**GRID** (Geometric Resonance Intelligence Driver) v2.5.0 is a local-first, privacy-first AI safety and cognitive analysis platform implementing Domain-Driven Design with Event-Driven Architecture.

---

## Architecture Layers

### 1. Core Domain Layer (`src/grid/`)
The "Mind" of the system — handles state representation, pattern recognition, context awareness, quantum state management, and agentic workflows. Key modules include:
- **Essence**: Core state representation via `EssentialState` dataclass
- **Patterns**: Recognition and emergence detection
- **Awareness**: Context and observer mechanics
- **Quantum**: Quantized architecture with locomotion
- **Senses**: Extended cognitive sensory support
- **Agentic**: Event-driven case management with Redis-backed EventBus
- **Processing**: Periodic processing with emergency real-time flows

### 2. Application Layer (`src/application/`)
The Mothership Cockpit — FastAPI backend (port 8080) implementing:
- Session management with TTL and activity tracking
- Operation/task lifecycle management
- Component health monitoring
- Alert system with severity levels
- Real-time WebSocket support
- Repository pattern with Unit of Work

### 3. Cognitive Layer (`src/cognitive/`)
Nine cognition patterns engine:
- **Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination**
- CognitiveEngine orchestrator
- ProfileStore for persistent user profiles
- InteractionTracker for behavioral inference
- ScaffoldingEngine for dynamic content adaptation
- CognitiveRouter for cognitive-aware request routing

### 4. RAG Pipeline (`src/tools/rag/`)
Local-first Retrieval-Augmented Generation:
- Ollama models (nomic-embed-text-v2, ministral)
- ChromaDB vector store persistence
- Hybrid BM25+Vector search with reranking
- LangChain integration (optional)

### 5. Safety Subsystem (`safety/`)
Fail-closed AI safety enforcement (<50ms pre-check):
- Deterministic pattern matching (no ML/network in pre-check)
- Guardian engine with rule-based detection
- Dynamic blocklist from Redis
- Temporal safety, hook detection, wellbeing monitoring
- Stamina/Heat systems for interaction pacing

### 6. Security Subsystem (`security/`)
Network access control and monitoring:
- Default-deny network policy
- Kill switch for emergency blocking
- Domain whitelisting
- Forensic log analysis
- Incident response tooling

### 7. Boundaries Subsystem (`boundaries/`)
Boundary contracts and consent management:
- BoundaryEngine with hard/soft/audit enforcement
- Consent lifecycle (grant/deny/revoke)
- Guardrail actions (block/warn/redact/log)
- Refusal rights integration

### 8. Unified Fabric (`src/unified_fabric/`)
Cross-project async event bus:
- Redis-backed pub/sub
- Domain-aware routing (safety, grid, coinbase)
- Request-reply pattern
- Event versioning and schema validation

### 9. Frontend (`frontend/`)
Electron + React 19 desktop application:
- TypeScript strict mode
- TailwindCSS 4 styling
- TanStack Query for data fetching
- Zod validation schemas

---

## Key Insights

### 1. Fail-Closed Safety Design
The safety subsystem operates on a fail-closed principle — unknown boundary IDs and guardrails trigger blocks, not silent passes. Pre-check must complete in <50ms using only deterministic pattern matching.

### 2. Dual Event Bus Architecture
Two complementary event systems:
- `grid/agentic/event_bus.py` — Redis-backed for agentic workflows
- `unified_fabric/` — Domain-aware routing with request-reply pattern

### 3. Local-First AI Strategy
All AI/ML runs locally via Ollama — no external API calls for inference. This aligns with the privacy-first design principle.

### 4. Triadic Safeguarding
The boundary engine implements refusal rights where user consent can override guardrails, but safety boundaries cannot be bypassed by autonomy.

### 5. 9 Cognitive Patterns
A unique cognitive architecture inspired by geometric resonance concepts, providing explainable AI through pattern-based reasoning.

### 6. Stamina/Heat Interaction Pacing
Novel approach to preventing AI manipulation through:
- **Stamina**: Input-locked resource that depletes with usage
- **Heat**: Accumulates with rapid interactions, triggers cooldowns

### 7. DRT Middleware
Unified "Data Resilience & Telemetry" middleware stack handling corruption detection, stream monitoring, and distributed tracing.

---

## API Endpoint Summary

| Router | Purpose | Key Endpoints |
|--------|---------|---------------|
| `auth.py` | Authentication | `/auth/login`, `/auth/logout`, `/auth/refresh` |
| `cockpit.py` | State Management | `/cockpit/state`, `/cockpit/sessions` |
| `agentic.py` | Case Operations | `/agentic/cases`, `/agentic/events` |
| `health.py` | System Health | `/health`, `/health/components` |
| `payment.py` | Billing | `/payment/checkout`, `/payment/webhooks` |
| `rag_streaming.py` | RAG Queries | `/rag/query`, `/rag/stream` |
| `safety.py` | Safety Status | `/safety/status`, `/safety/alerts` |
| `privacy.py` | Data Protection | `/privacy/export`, `/privacy/delete` |

---

## Technology Stack Matrix

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy async, Redis, Celery |
| **Frontend** | React 19, TypeScript strict, Vite 7, Electron 40, TailwindCSS 4 |
| **AI/ML** | Ollama (local), sentence-transformers, ChromaDB, BM25 hybrid search |
| **Quality** | ruff (120), mypy strict, pytest, ESLint 9, Prettier |
| **Observability** | OpenTelemetry, Prometheus, structlog, Jaeger |

---

## RAG System Usage

### Index a Repository
```bash
python -m tools.rag.cli index . --curate
```

### Query the Knowledge Base
```bash
python -m tools.rag.cli query "How does the grid system work?"
```

### Interactive Chat
```bash
grid chat --model ministral-3:3b
```

---

## Safety Rules (Trust Layer Standard)

1. **No Perpetrator Voice**: Safety code describes harm, never performs it
2. **Nominalization**: Convert harmful actions to abstract nouns
3. **Register Analysis**: Distinguish formal vs colloquial registers
4. **Distress vs Threat**: Distress triggers support, not blocking
5. **Active Refusal**: Immediate refusal of harmful requests at inference layer
6. **Content Provenance**: Watermarking for all AI-generated safety reports
7. **Triadic Safeguarding**: Safety boundaries over autonomy in critical discovery
