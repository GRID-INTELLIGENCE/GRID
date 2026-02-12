# Executive Summary: GRID Intelligence Framework Architecture

## Overview

The GRID Intelligence Framework is a **multi-repository intelligence platform** that transforms codebases into actionable business intelligence. The system uses GRID as the core cognitive framework with specialized repositories for different concerns, normalizing them into stable artifacts and generating stakeholder-ready outputs.

## Core Architecture Principles

### 1. **Separation of Concerns**
- **`E:\grid`** - AI/ML framework, cognitive architecture, RAG system (core)
- **`E:\Coinbase`** - Crypto-focused application with GRID integration
- **`E:\analysis_outputs`** - Shared analysis artifacts repository
- **Future: `E:\apps`** - Orchestrator, UI, business logic (planned)

### 2. **Run-Based Immutable Snapshots**
- Every analysis creates a unique `run_id` (format: `YYYYMMDD-HHMMSSZ_<uuid8>`)
- Runs are immutable snapshots stored in `Apps/data/harness/runs/{run_id}/`
- Enables demo stability, versioning, and reproducible analysis

### 3. **Tiered Deep Harvest System**
- **Tier 1**: Consume existing artifacts from `analysis_outputs/`
- **Tier 2**: Trigger `analyze_repo.py` for fresh deep analysis
- **Tier 3**: Lightweight fallback (READMEs, configs, entrypoint detection)

### 4. **Normalization & Indexing**
- Heterogeneous repo outputs → canonical `ProjectGraph` schema
- Enables consistent reasoning across different codebase types
- Backward-compatible adapter layer for existing frontend

### 5. **Derived Intelligence Packs**
- Stakeholder updates
- Demo scripts
- Compliance packets
- Product/services manifests
- Profile/resume generation (with AI safety analysis)
- Monetization packs (pricing, Stripe health, subscription metrics)

## System Components

### Core Services (`E:\grid\src`)

**Application Layer (`application/mothership/`):**
- FastAPI-based API server
- Authentication and authorization (JWT, RBAC)
- Service orchestration and background tasks (Celery)

**Cognitive Layer (`cognitive/`):**
- Cognitive patterns and decision support
- Vision layer integration
- Event-driven architecture

**RAG System (`tools/rag/`):**
- Local-first RAG with ChromaDB
- Ollama integration for embeddings
- Intelligent query processing

**Core Intelligence (`grid/`):**
- Skills registry and execution
- Knowledge graph integration
- Security and secrets management

### API Architecture

**Modular Router Structure:**
- `/api/harness/*` - Deep context harvesting
- `/api/pipeline-check/*` - Legacy pipeline analysis
- `/api/payment/*` - Stripe integration
- `/api/referrals/*` - Referral system
- `/api/agents/*` - Agent cloning
- `/api/ab-tests/*` - A/B testing

## Data Flow

```
┌─────────────┐
│   Repos     │
│ (grid/EUFLE)│
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Harvest Service │
│  (Tier 1/2/3)    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Analysis Outputs │
│  (E:\analysis_   │
│   outputs)       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Run Directory   │
│  (Immutable)     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Normalization    │
│  (ProjectGraph)  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Reasoning       │
│  (Packs)         │
└──────────────────┘
```

## Key Features

### 1. **Deep Context Harvesting**
- Recursively extracts architectural context (module graphs, entry points, dependencies)
- Detects AI safety patterns (RLHF, alignment, guardrails)
- Analyzes compliance and risk metadata

### 2. **AI Safety Analysis**
- Model usage detection (OpenAI, Anthropic, Ollama, HuggingFace)
- Prompt security scoring
- Data privacy assessment
- Safety pattern identification

### 3. **Profile & Resume Generation**
- Structured codebase profiles
- Technical skills extraction
- AI safety expertise documentation
- Resume transformation for stakeholder presentations

### 4. **Monetization Intelligence**
- Pricing table generation
- Stripe configuration health checks
- Subscription funnel metrics
- Compliance reporting integration

### 5. **Stripe Integration**
- Fixed free tier handling (no checkout for free)
- Subscription metadata propagation
- Webhook idempotency
- Protected price auto-creation (dev flag required)

## Technology Stack

**Backend:**
- FastAPI (Python 3.13+)
- SQLAlchemy (async ORM)
- Pydantic v2 (validation)
- Celery (background tasks)
- ChromaDB (vector store)
- Ollama (local LLM)

**Analysis Tools:**
- RAG CLI - `python -m tools.rag.cli query "question"`
- Codebase analysis scripts
- Security vulnerability scanners

## Security & Compliance

- Path validation and whitelisting
- Traversal attack prevention
- Environment-first configuration
- Webhook signature verification
- Idempotent webhook processing
- AI safety risk assessment

## Scalability Considerations

- Run-based isolation enables parallel analysis
- Artifact compression for large codebases
- Async job execution for long-running analysis
- Retention policies for run cleanup
- Degraded mode tracking for failed repos

## Current Status

✅ **Complete:**
- Harness architecture implementation
- Tiered harvest system
- Normalization layer
- API endpoints
- Frontend migration
- Profile/resume generation
- AI safety analysis
- Monetization pack generation
- Stripe integration fixes

🔄 **In Progress:**
- Enhanced reasoning with LLM integration
- UI components for run management
- Background job queue

📋 **Planned:**
- Cross-run querying (SQLite index)
- Advanced caching (Redis)
- Monitoring and metrics

## Business Value

1. **Demo Stability** - Immutable run snapshots ensure consistent stakeholder presentations
2. **Compliance Readiness** - Automated compliance packet generation
3. **Monetization Intelligence** - Real-time subscription metrics and Stripe health
4. **AI Safety Documentation** - Automated safety pattern detection and reporting
5. **Stakeholder Communication** - Auto-generated updates and demo scripts

---

**Last Updated**: 2026-01-14
**Architecture Version**: 1.0
**Status**: Production Ready
