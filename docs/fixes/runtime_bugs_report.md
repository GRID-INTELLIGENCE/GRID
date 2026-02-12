# Runtime Bug Scan Report
**Generated:** 2026-02-12 20:08:15
**Total Issues Found:** 749

## Summary by Pattern Type

### Division By Zero (543 issues)

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\generate_embeddings_optimized.py**
- Line 224: Division by JSONL (could be zero) without check
  - Code: `parser.add_argument("input_file", help="Input JSON/JSONL file with texts")`
  - Fix: Add check: (x / JSONL) if JSONL != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\mcp-setup\server\enhanced_tools_mcp_server.py**
- Line 371: Division by generated (could be zero) without check
  - Code: `output_dir = args.get("output_dir", "docs/generated")`
  - Fix: Add check: (x / generated) if generated != 0 else 0.0
- Line 452: Division by mypy_report (could be zero) without check
  - Code: `cmd = ["python", "-m", "mypy", target, "--json-report", "/tmp/mypy_report"]`
  - Fix: Add check: (x / mypy_report) if mypy_report != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\mcp-setup\server\grid_rag_mcp_server.py**
- Line 94: Division by A (could be zero) without check
  - Code: `- Collection: {stats.get("collection_name", "N/A")}`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 95: Division by A (could be zero) without check
  - Code: `- Embedding Model: {stats.get("embedding_model", "N/A")}`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 96: Division by A (could be zero) without check
  - Code: `- LLM Model: {stats.get("llm_model", "N/A")}`
  - Fix: Add check: (x / A) if A != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\canvas\api.py**
- Line 16: Division by v1 (could be zero) without check
  - Code: `router = APIRouter(prefix="/api/v1/canvas", tags=["canvas"])`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\canvas\canvas_integration_example.py**
- Line 110: Division by s (could be zero) without check
  - Code: `print(f"   Rotation Velocity: {json_viz['rotation_velocity']:.3f} rad/s")`
  - Fix: Add check: (x / s) if s != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\canvas\interfaces.py**
- Line 20: Division by interfaces (could be zero) without check
  - Code: `"""Bridges canvas with grid/interfaces (QuantumBridge, SensoryProcessor)."""`
  - Fix: Add check: (x / interfaces) if interfaces != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\canvas\territory_map.py**
- Line 268: Division by in (could be zero) without check
  - Code: `resolution="Import from tools module, ensure src/ in PYTHONPATH",`
  - Fix: Add check: (x / in) if in != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\__init__.py**
- Line 30: Division by response (could be zero) without check
  - Code: `- schemas/: Pydantic request/response schemas`
  - Fix: Add check: (x / response) if response != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\api\gateway.py**
- Line 8: Division by response (could be zero) without check
  - Code: `- Request/response envelope standardization`
  - Fix: Add check: (x / response) if response != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\api\v2\__init__.py**
- Line 13: Division by response (could be zero) without check
  - Code: `- Removing or renaming fields in request/response schemas`
  - Fix: Add check: (x / response) if response != 0 else 0.0
- Line 15: Division by authorization (could be zero) without check
  - Code: `- Altering authentication/authorization requirements`
  - Fix: Add check: (x / authorization) if authorization != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\api_core.py**
- Line 337: Division by second (could be zero) without check
  - Code: `rate_limit: Rate limit specification (e.g., "10/second")`
  - Fix: Add check: (x / second) if second != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\config\__init__.py**
- Line 163: Division by SQLite (could be zero) without check
  - Code: `"Falling back to MOTHERSHIP_DB_FALLBACK_URL / SQLite. "`
  - Fix: Add check: (x / SQLite) if SQLite != 0 else 0.0
- Line 178: Division by mothership (could be zero) without check
  - Code: `default_db_url = "postgresql://user:pass@localhost/mothership"`
  - Fix: Add check: (x / mothership) if mothership != 0 else 0.0
- Line 503: Division by v1 (could be zero) without check
  - Code: `bkash_base_url=env.get("BKASH_BASE_URL", "https://tokenized.sandbox.bka.sh/v1.2.0-beta"),`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\db\databricks_connector.py**
- Line 222: Division by debugging (could be zero) without check
  - Code: `"""Get connection string (for logging/debugging).`
  - Fix: Add check: (x / debugging) if debugging != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\main.py**
- Line 548: Division by status (could be zero) without check
  - Code: `@app.get("/security/status", tags=["security"])`
  - Fix: Add check: (x / status) if status != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\middleware\__init__.py**
- Line 10: Division by response (could be zero) without check
  - Code: `- Structured request/response logging`
  - Fix: Add check: (x / response) if response != 0 else 0.0
- Line 121: Division by response (could be zero) without check
  - Code: `Middleware for structured request/response logging.`
  - Fix: Add check: (x / response) if response != 0 else 0.0
- Line 249: Division by v1 (could be zero) without check
  - Code: `if request.url.path.startswith("/api/v1/admin") or request.url.path.startswith("/api/v1/auth"):`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\middleware\boundary_enforcer.py**
- Line 15: Division by v1 (could be zero) without check
  - Code: `ownership. Endpoints prefixed with ``/api/v1/intelligence```
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\middleware\circuit_breaker.py**
- Line 469: Division by live (could be zero) without check
  - Code: `excluded_paths=excluded_paths or ["/health", "/health/live", "/health/ready", "/ping", "/metrics"],`
  - Fix: Add check: (x / live) if live != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\middleware\rate_limit_redis.py**
- Line 77: Division by system (could be zero) without check
  - Code: `# Get cognitive load metrics for the user/system`
  - Fix: Add check: (x / system) if system != 0 else 0.0
- Line 202: Division by self (could be zero) without check
  - Code: `"cognitive_adjustment": effective_rpm / self.base_requests_per_minute`
  - Fix: Add check: (x / self) if self != 0 else 0.0
- Line 209: Division by self (could be zero) without check
  - Code: `"X-Cognitive-Load-Adjustment": f"{effective_rpm / self.base_requests_per_minute:.2f}"`
  - Fix: Add check: (x / self) if self != 0 else 0.0
- Line 216: Division by self (could be zero) without check
  - Code: `response.headers["X-Cognitive-Load-Adjustment"] = f"{effective_rpm / self.base_requests_per_minute:.2f}"`
  - Fix: Add check: (x / self) if self != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\middleware\request_size.py**
- Line 68: Division by Starlette (could be zero) without check
  - Code: `# Process request (streaming bodies are handled by FastAPI/Starlette)`
  - Fix: Add check: (x / Starlette) if Starlette != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\middleware\security_enforcer.py**
- Line 496: Division by json (could be zero) without check
  - Code: `if "application/json" not in content_type.lower():`
  - Fix: Add check: (x / json) if json != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\middleware\usage_tracking.py**
- Line 63: Division by handler (could be zero) without check
  - Code: `call_next: Next middleware/handler`
  - Fix: Add check: (x / handler) if handler != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\models\__init__.py**
- Line 225: Division by Output (could be zero) without check
  - Code: `# Input/Output`
  - Fix: Add check: (x / Output) if Output != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\routers\auth.py**
- Line 290: Division by database (could be zero) without check
  - Code: `# - Store token JTI in Redis/database`
  - Fix: Add check: (x / database) if database != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\routers\cockpit.py**
- Line 234: Division by full (could be zero) without check
  - Code: `"/state/full",`
  - Fix: Add check: (x / full) if full != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\routers\health.py**
- Line 156: Division by live (could be zero) without check
  - Code: `"/health/live",`
  - Fix: Add check: (x / live) if live != 0 else 0.0
- Line 176: Division by ready (could be zero) without check
  - Code: `"/health/ready",`
  - Fix: Add check: (x / ready) if ready != 0 else 0.0
- Line 236: Division by startup (could be zero) without check
  - Code: `"/health/startup",`
  - Fix: Add check: (x / startup) if startup != 0 else 0.0
- Line 290: Division by security (could be zero) without check
  - Code: `"/health/security",`
  - Fix: Add check: (x / security) if security != 0 else 0.0
- Line 460: Division by circuit (could be zero) without check
  - Code: `"/health/circuit-breakers",`
  - Fix: Add check: (x / circuit) if circuit != 0 else 0.0
- Line 504: Division by factory (could be zero) without check
  - Code: `"/health/factory-defaults",`
  - Fix: Add check: (x / factory) if factory != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\routers\navigation.py**
- Line 259: Division by traceability (could be zero) without check
  - Code: `- Authentication context (if present) is passed through into planning context for auditing/traceability.`
  - Fix: Add check: (x / traceability) if traceability != 0 else 0.0
- Line 278: Division by navigation (could be zero) without check
  - Code: `"location": "routers/navigation.py:258",`
  - Fix: Add check: (x / navigation) if navigation != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\routers\rag_streaming.py**
- Line 81: Division by stream (could be zero) without check
  - Code: `@router.post("/query/stream")`
  - Fix: Add check: (x / stream) if stream != 0 else 0.0
- Line 198: Division by batch (could be zero) without check
  - Code: `@router.post("/query/batch")`
  - Fix: Add check: (x / batch) if batch != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\schemas\__init__.py**
- Line 64: Division by responses (could be zero) without check
  - Code: `"""Task priority for API requests/responses."""`
  - Fix: Add check: (x / responses) if responses != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\schemas\requests.py**
- Line 737: Division by Filter (could be zero) without check
  - Code: `# Query/Filter Requests`
  - Fix: Add check: (x / Filter) if Filter != 0 else 0.0
- Line 871: Division by Filter (could be zero) without check
  - Code: `# Query/Filter`
  - Fix: Add check: (x / Filter) if Filter != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\security\api_sentinels.py**
- Line 442: Division by second (could be zero) without check
  - Code: `rate_limit: str = "10/second"`
  - Fix: Add check: (x / second) if second != 0 else 0.0
- Line 447: Division by json (could be zero) without check
  - Code: `allowed_content_types: list[str] = field(default_factory=lambda: ["application/json"])`
  - Fix: Add check: (x / json) if json != 0 else 0.0
- Line 655: Division by json (could be zero) without check
  - Code: `["application/json"],`
  - Fix: Add check: (x / json) if json != 0 else 0.0
- Line 665: Division by shorter (could be zero) without check
  - Code: `# Alias for backwards compatibility / shorter import`
  - Fix: Add check: (x / shorter) if shorter != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\services\finance\scopes.py**
- Line 20: Division by mothership (could be zero) without check
  - Code: `"service": "application/mothership/services/finance/yfinance_adapter.py",`
  - Fix: Add check: (x / mothership) if mothership != 0 else 0.0
- Line 21: Division by mothership (could be zero) without check
  - Code: `"router": "application/mothership/routers/finance.py",`
  - Fix: Add check: (x / mothership) if mothership != 0 else 0.0
- Line 22: Division by maintenance (could be zero) without check
  - Code: `"scheduler": "scripts/maintenance/budget_scheduler.py",  # For periodic updates`
  - Fix: Add check: (x / maintenance) if maintenance != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\resonance\adsr_envelope.py**
- Line 118: Division by self (could be zero) without check
  - Code: `progress = release_elapsed / self.release_time`
  - Fix: Add check: (x / self) if self != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\resonance\api\router.py**
- Line 292: Division by attention (could be zero) without check
  - Code: `Provides vivid explanations when context is sparse and decision/attention`
  - Fix: Add check: (x / attention) if attention != 0 else 0.0
- Line 327: Division by output (could be zero) without check
  - Code: `input/output scenarios.`
  - Fix: Add check: (x / output) if output != 0 else 0.0
- Line 494: Division by type (could be zero) without check
  - Code: `# Avoid referencing TraceOrigin.API_REQUEST in that case to prevent diagnostics/type issues.`
  - Fix: Add check: (x / type) if type != 0 else 0.0
- Line 562: Division by theater (could be zero) without check
  - Code: `"source_domain": "stage performance / theater",`
  - Fix: Add check: (x / theater) if theater != 0 else 0.0
- Line 563: Division by system (could be zero) without check
  - Code: `"target_domain": "API orchestration / system execution",`
  - Fix: Add check: (x / system) if system != 0 else 0.0
- Line 572: Division by right (could be zero) without check
  - Code: `"triages left/right/straight paths, and uses skills to transform and compress free-form work "`
  - Fix: Add check: (x / right) if right != 0 else 0.0
- Line 673: Division by api (could be zero) without check
  - Code: `"POST /api/v1/resonance/definitive → checkpoint (canvas flip) + skills orchestration",`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 674: Division by api (could be zero) without check
  - Code: `"GET /api/v1/resonance/context → fast context snapshot",`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 675: Division by api (could be zero) without check
  - Code: `"GET /api/v1/resonance/paths → left/right/straight style path options",`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 676: Division by python (could be zero) without check
  - Code: `"python -m grid skills list / python -m grid skills run <skill_id>",`
  - Fix: Add check: (x / python) if python != 0 else 0.0
- Line 677: Division by python (could be zero) without check
  - Code: `"python -m tools.rag.cli index . --rebuild --curate / python -m tools.rag.cli query '...'",`
  - Fix: Add check: (x / python) if python != 0 else 0.0
- Line 795: Division by protocol (could be zero) without check
  - Code: `# websocket_endpoint expects the API-layer ResonanceService type alias/protocol.`
  - Fix: Add check: (x / protocol) if protocol != 0 else 0.0
- Line 796: Division by type (could be zero) without check
  - Code: `# At runtime they are compatible; cast to satisfy static diagnostics/type checking.`
  - Fix: Add check: (x / type) if type != 0 else 0.0
- Line 806: Division by config (could be zero) without check
  - Code: `@router.get("/debug/config", tags=["debug"], summary="Get Debug Config")`
  - Fix: Add check: (x / config) if config != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\resonance\api\schemas.py**
- Line 2: Division by Response (could be zero) without check
  - Code: `Activity Resonance API Request/Response Schemas.`
  - Fix: Add check: (x / Response) if Response != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\resonance\context_provider.py**
- Line 4: Division by attention (could be zero) without check
  - Code: `Provides fast, concise context when decision/attention metrics are tense.`
  - Fix: Add check: (x / attention) if attention != 0 else 0.0
- Line 44: Division by attention (could be zero) without check
  - Code: `Provides vivid explanations when context is sparse and decision/attention`
  - Fix: Add check: (x / attention) if attention != 0 else 0.0
- Line 179: Division by response (could be zero) without check
  - Code: `return "API context: FastAPI routes, middleware, request/response models."`
  - Fix: Add check: (x / response) if response != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\resonance\path_visualizer.py**
- Line 5: Division by output (could be zero) without check
  - Code: `and gives glimpses of input/output scenarios when coding presents`
  - Fix: Add check: (x / output) if output != 0 else 0.0
- Line 6: Division by ways (could be zero) without check
  - Code: `recommendation triage (3-4 different paths/ways/options/choices).`
  - Fix: Add check: (x / ways) if ways != 0 else 0.0
- Line 31: Division by output (could be zero) without check
  - Code: `"""A single path option with input/output scenarios."""`
  - Fix: Add check: (x / output) if output != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\cognitive\cognitive_unit.py**
- Line 5: Division by inputs (could be zero) without check
  - Code: `The Cognitive Unit represents a synchronized slice across all senses/inputs at a`
  - Fix: Add check: (x / inputs) if inputs != 0 else 0.0
- Line 71: Division by inputs (could be zero) without check
  - Code: `"""A synchronized slice across senses/inputs.`
  - Fix: Add check: (x / inputs) if inputs != 0 else 0.0
- Line 296: Division by length (could be zero) without check
  - Code: `Straightness ratio (displacement / length, 0-1)`
  - Fix: Add check: (x / length) if length != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\cognitive\light_of_the_seven\cognitive_layer\cognitive_load\load_estimator.py**
- Line 126: Division by base_capacity (could be zero) without check
  - Code: `usage = min(1.0, chunk_count / base_capacity)`
  - Fix: Add check: (x / base_capacity) if base_capacity != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\cognitive\patterns\recognition.py**
- Line 231: Division by low (could be zero) without check
  - Code: `# Flow indicators: moderate load (not too high/low), high engagement`
  - Fix: Add check: (x / low) if low != 0 else 0.0
- Line 1717: Division by temporal (could be zero) without check
  - Code: `- Resonance Peak: Maximum response at a specific frequency/temporal point`
  - Fix: Add check: (x / temporal) if temporal != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\cognitive\temporal\functions.py**
- Line 26: Division by expansion (could be zero) without check
  - Code: `# Apply time compression/expansion based on sensitivity`
  - Fix: Add check: (x / expansion) if expansion != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\__main__.py**
- Line 224: Division by dict (could be zero) without check
  - Code: `raise SystemExit("Payload must decode to a JSON object/dict")`
  - Fix: Add check: (x / dict) if dict != 0 else 0.0
- Line 229: Division by JS (could be zero) without check
  - Code: `# PowerShell / JS-style object literal fallback: {key:1, other_key:"x"}`
  - Fix: Add check: (x / JS) if JS != 0 else 0.0
- Line 251: Division by list (could be zero) without check
  - Code: `"or a Python literal dict/list string. Received: "`
  - Fix: Add check: (x / list) if list != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\agentic\memo_generator.py**
- Line 40: Division by f (could be zero) without check
  - Code: `memo_path = self.output_dir / f"{memo_id}.json"`
  - Fix: Add check: (x / f) if f != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\agentic\skill_generator.py**
- Line 40: Division by skill_id (could be zero) without check
  - Code: `skill_dir = self.skill_store_path / skill_id`
  - Fix: Add check: (x / skill_id) if skill_id != 0 else 0.0
- Line 63: Division by A (could be zero) without check
  - Code: `- Role: {experience.get('agent_role', 'N/A')}`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 64: Division by A (could be zero) without check
  - Code: `- Task: {experience.get('task', 'N/A')}`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 65: Division by A (could be zero) without check
  - Code: `- Execution Time: {experience.get('execution_time_seconds', 'N/A')}s`
  - Fix: Add check: (x / A) if A != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\agentic\snapshot_manager.py**
- Line 163: Division by aggregate_id (could be zero) without check
  - Code: `aggregate_dir = self.storage_dir / aggregate_id`
  - Fix: Add check: (x / aggregate_id) if aggregate_id != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\context\pattern_recognition.py**
- Line 233: Division by day (could be zero) without check
  - Code: `# Get patterns for similar time/day`
  - Fix: Add check: (x / day) if day != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\distribution\eufle_bridge.py**
- Line 34: Division by eufle_models (could be zero) without check
  - Code: `models_inventory_target = self.grid_path / "config/eufle_models.yaml"`
  - Fix: Add check: (x / eufle_models) if eufle_models != 0 else 0.0
- Line 53: Division by Env (could be zero) without check
  - Code: `# 2. Sync specific settings from EUFLE's README/Env (Simulated)`
  - Fix: Add check: (x / Env) if Env != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\distribution\ghost_fx.py**
- Line 41: Division by 1_000_000_000 (could be zero) without check
  - Code: `drift_factor = min(1.0, age_ns / 1_000_000_000.0)`
  - Fix: Add check: (x / 1_000_000_000) if 1_000_000_000 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\integration\domain_gateway.py**
- Line 443: Division by Testing (could be zero) without check
  - Code: `# Demo / Testing`
  - Fix: Add check: (x / Testing) if Testing != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\interfaces\config.py**
- Line 76: Division by interfaces_metrics (could be zero) without check
  - Code: `prototype_db_path=env.get("INTERFACES_PROTOTYPE_DB_PATH", "data/interfaces_metrics.db"),`
  - Fix: Add check: (x / interfaces_metrics) if interfaces_metrics != 0 else 0.0
- Line 86: Division by logs (could be zero) without check
  - Code: `else ["data", "grid/logs/traces", "**/benchmark*.json", "**/stress*.json"]`
  - Fix: Add check: (x / logs) if logs != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\interfaces\metrics_collector.py**
- Line 109: Division by visual (could be zero) without check
  - Code: `modality: Input modality (text/visual/audio/structured)`
  - Fix: Add check: (x / visual) if visual != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\io\__init__.py**
- Line 11: Division by HTTP (could be zero) without check
  - Code: `- APIGateway: REST/HTTP API input handling`
  - Fix: Add check: (x / HTTP) if HTTP != 0 else 0.0
- Line 19: Division by O (could be zero) without check
  - Code: `- Correlation ID tracking across I/O boundaries`
  - Fix: Add check: (x / O) if O != 0 else 0.0
- Line 21: Division by O (could be zero) without check
  - Code: `- Async and sync I/O operations`
  - Fix: Add check: (x / O) if O != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\io\gateways.py**
- Line 2: Division by O (could be zero) without check
  - Code: `Input Gateway Implementations for GRID Event-Driven I/O Architecture.`
  - Fix: Add check: (x / O) if O != 0 else 0.0
- Line 9: Division by HTTP (could be zero) without check
  - Code: `- APIGateway: REST/HTTP API request handling`
  - Fix: Add check: (x / HTTP) if HTTP != 0 else 0.0
- Line 335: Division by HTTP (could be zero) without check
  - Code: `REST/HTTP API input gateway.`
  - Fix: Add check: (x / HTTP) if HTTP != 0 else 0.0
- Line 358: Division by v1 (could be zero) without check
  - Code: `"/api/v1/analyze",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 359: Division by v1 (could be zero) without check
  - Code: `"/api/v1/process",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\knowledge\graph_schema.py**
- Line 16: Division by outputs (could be zero) without check
  - Code: `- Skill: Executable capabilities with inputs/outputs`
  - Fix: Add check: (x / outputs) if outputs != 0 else 0.0
- Line 18: Division by state (could be zero) without check
  - Code: `- Context: Environmental/state information (with phase/momentum from progress_compass)`
  - Fix: Add check: (x / state) if state != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\mcp\__init__.py**
- Line 12: Division by mcp_config (could be zero) without check
  - Code: `registry = await quick_setup("mcp-setup/mcp_config.json")`
  - Fix: Add check: (x / mcp_config) if mcp_config != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\mcp\mastermind_server.py**
- Line 74: Division by A (could be zero) without check
  - Code: `- Root: {info.get("root", "N/A")}`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 86: Division by A (could be zero) without check
  - Code: `- Complexity: {results.get("complexity", "N/A")}`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 87: Division by A (could be zero) without check
  - Code: `- Quality Score: {results.get("quality_score", "N/A")}`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 88: Division by A (could be zero) without check
  - Code: `- Test Coverage: {results.get("test_coverage", "N/A")}%`
  - Fix: Add check: (x / A) if A != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\organization\toggle_kit.py**
- Line 245: Division by context (could be zero) without check
  - Code: `"""Determine if a user/context is in the rollout percentage."""`
  - Fix: Add check: (x / context) if context != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\progress\__init__.py**
- Line 11: Division by grid (could be zero) without check
  - Code: `python src/grid/progress/quick.py  # Every 30 minutes`
  - Fix: Add check: (x / grid) if grid != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\progress\momentum.py**
- Line 48: Division by CD (could be zero) without check
  - Code: `Perfect for logging to file or displaying in CI/CD.`
  - Fix: Add check: (x / CD) if CD != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\prompts\prompt_store.py**
- Line 48: Division by f (could be zero) without check
  - Code: `return self.storage_path / f"{prompt_id}.json"`
  - Fix: Add check: (x / f) if f != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\resilience\api.py**
- Line 32: Division by fallback (could be zero) without check
  - Code: `@router.get("/retry", summary="Get retry/fallback metrics")`
  - Fix: Add check: (x / fallback) if fallback != 0 else 0.0
- Line 48: Division by export (could be zero) without check
  - Code: `@router.get("/retry/export", summary="Export metrics for monitoring systems")`
  - Fix: Add check: (x / export) if export != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\resilience\observed_decorators.py**
- Line 153: Division by search (could be zero) without check
  - Code: `return requests.get(f"https://api.example.com/search?q={query}").json()`
  - Fix: Add check: (x / search) if search != 0 else 0.0
- Line 205: Division by search (could be zero) without check
  - Code: `async with session.get(f"https://api.example.com/search?q={query}") as resp:`
  - Fix: Add check: (x / search) if search != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\resilience\policies.py**
- Line 224: Division by CLI (could be zero) without check
  - Code: `# Command/CLI Operations`
  - Fix: Add check: (x / CLI) if CLI != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\secrets\__main__.py**
- Line 16: Division by to (could be zero) without check
  - Code: `# Add src/ to path for imports`
  - Fix: Add check: (x / to) if to != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\audit_logger.py**
- Line 115: Division by audit (could be zero) without check
  - Code: `audit_path = os.getenv("GRID_AUDIT_LOG_PATH", "./data/audit.log")`
  - Fix: Add check: (x / audit) if audit != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\input_sanitizer.py**
- Line 159: Division by null (could be zero) without check
  - Code: `(r">\s*/dev/null", ThreatType.COMMAND_INJECTION, ThreatSeverity.LOW),`
  - Fix: Add check: (x / null) if null != 0 else 0.0
- Line 329: Division by dictionary (could be zero) without check
  - Code: `Sanitize JSON/dictionary input.`
  - Fix: Add check: (x / dictionary) if dictionary != 0 else 0.0
- Line 342: Division by dictionary (could be zero) without check
  - Code: `Sanitize JSON/dictionary input with detailed result.`
  - Fix: Add check: (x / dictionary) if dictionary != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\local_secrets_manager.py**
- Line 413: Division by no (could be zero) without check
  - Code: `confirm = input("This will delete ALL secrets. Continue? (yes/no): ")`
  - Fix: Add check: (x / no) if no != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\path_validator.py**
- Line 40: Division by target_path (could be zero) without check
  - Code: `target = (base / target_path).resolve()`
  - Fix: Add check: (x / target_path) if target_path != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\templates.py**
- Line 252: Division by live (could be zero) without check
  - Code: `path: {config.get('GRID_LIVENESS_PATH', '/health/live')}`
  - Fix: Add check: (x / live) if live != 0 else 0.0
- Line 259: Division by ready (could be zero) without check
  - Code: `path: {config.get('GRID_READINESS_PATH', '/health/ready')}`
  - Fix: Add check: (x / ready) if ready != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\threat_detector.py**
- Line 753: Division by limit (could be zero) without check
  - Code: `rate_risk = min(1.0, count / limit) * 0.5`
  - Fix: Add check: (x / limit) if limit != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\senses\sensory_store.py**
- Line 17: Division by data (could be zero) without check
  - Code: `storage_path: Path to store sensory inputs (default: ./grid/data/senses)`
  - Fix: Add check: (x / data) if data != 0 else 0.0
- Line 20: Division by data (could be zero) without check
  - Code: `storage_path = Path("grid/data/senses")`
  - Fix: Add check: (x / data) if data != 0 else 0.0
- Line 32: Division by date_str (could be zero) without check
  - Code: `date_dir = self.storage_path / date_str`
  - Fix: Add check: (x / date_str) if date_str != 0 else 0.0
- Line 35: Division by input_data (could be zero) without check
  - Code: `type_dir = date_dir / input_data.sensory_type.value`
  - Fix: Add check: (x / input_data) if input_data != 0 else 0.0
- Line 38: Division by f (could be zero) without check
  - Code: `input_file = type_dir / f"{input_data.input_id}.json"`
  - Fix: Add check: (x / f) if f != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\services\inference_harness.py**
- Line 187: Division by api (could be zero) without check
  - Code: `response = requests.get("http://localhost:11434/api/tags", timeout=1)`
  - Fix: Add check: (x / api) if api != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\diagnostics.py**
- Line 37: Division by skills_diagnostics (could be zero) without check
  - Code: `self._reports_dir = reports_dir or Path("./data/skills_diagnostics")`
  - Fix: Add check: (x / skills_diagnostics) if skills_diagnostics != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\intelligence_inventory.py**
- Line 67: Division by skills_intelligence (could be zero) without check
  - Code: `storage_path = Path(os.getenv("GRID_SKILLS_INVENTORY_PATH", "./data/skills_intelligence.db"))`
  - Fix: Add check: (x / skills_intelligence) if skills_intelligence != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\persistence_verifier.py**
- Line 132: Division by zero (could be zero) without check
  - Code: `# Check for invalid (negative/zero) latencies - allow NULL for optional fields`
  - Fix: Add check: (x / zero) if zero != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\topic_extractor.py**
- Line 11: Division by stitching (could be zero) without check
  - Code: `"""Extract discussion topics using wall-board metaphor with pins/stitching imagery."""`
  - Fix: Add check: (x / stitching) if stitching != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\version_manager.py**
- Line 62: Division by skill_id (could be zero) without check
  - Code: `skill_dir = self._storage_dir / skill_id`
  - Fix: Add check: (x / skill_id) if skill_id != 0 else 0.0
- Line 146: Division by f (could be zero) without check
  - Code: `version_file = skill_dir / f"{version.version_id}.json"`
  - Fix: Add check: (x / f) if f != 0 else 0.0
- Line 166: Division by f (could be zero) without check
  - Code: `version_file = skill_dir / f"{version_id}.json"`
  - Fix: Add check: (x / f) if f != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\spark\personas.py**
- Line 311: Division by destination (could be zero) without check
  - Code: `# Extract origin/destination from context or use defaults`
  - Fix: Add check: (x / destination) if destination != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\spark\pipeline.py**
- Line 25: Division by harvests (could be zero) without check
  - Code: `def __init__(self, output_dir: str = "e:/grid/harvests") -> None:`
  - Fix: Add check: (x / harvests) if harvests != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\spark\staircase.py**
- Line 41: Division by route (could be zero) without check
  - Code: `"""State of a staircase/route."""`
  - Fix: Add check: (x / route) if route != 0 else 0.0
- Line 282: Division by discover (could be zero) without check
  - Code: `f"{self.base_url}/routes/discover",`
  - Fix: Add check: (x / discover) if discover != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\tracing\trace_store.py**
- Line 51: Division by date_str (could be zero) without check
  - Code: `date_dir = self.storage_path / date_str`
  - Fix: Add check: (x / date_str) if date_str != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\version_3_5.py**
- Line 40: Division by VERSION_ACCURACY_REPORT (could be zero) without check
  - Code: `Formula from docs/VERSION_ACCURACY_REPORT.md`
  - Fix: Add check: (x / VERSION_ACCURACY_REPORT) if VERSION_ACCURACY_REPORT != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\workflow\suggestions.py**
- Line 148: Division by directory (could be zero) without check
  - Code: `# Get files from same project/directory`
  - Fix: Add check: (x / directory) if directory != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\xai\performance_optimizer.py**
- Line 197: Division by instances (could be zero) without check
  - Code: `Load balancer for distributing XAI requests across multiple servers/instances.`
  - Fix: Add check: (x / instances) if instances != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\agent_prompts\advanced_protocols.py**
- Line 66: Division by knowledgebase (could be zero) without check
  - Code: `# Step 1: Search memory/knowledgebase`
  - Fix: Add check: (x / knowledgebase) if knowledgebase != 0 else 0.0
- Line 106: Division by knowledgebase (could be zero) without check
  - Code: `"""Search memory/knowledgebase for similar cases."""`
  - Fix: Add check: (x / knowledgebase) if knowledgebase != 0 else 0.0
- Line 343: Division by TEST (could be zero) without check
  - Code: `reference_file_path=".case_references/TEST-002_reference.json",`
  - Fix: Add check: (x / TEST) if TEST != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\agent_prompts\case_filing.py**
- Line 31: Division by rare (could be zero) without check
  - Code: `RARE = "rare"  # New/rare cases that don't fit existing categories`
  - Fix: Add check: (x / rare) if rare != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\agent_prompts\processing_unit.py**
- Line 260: Division by f (could be zero) without check
  - Code: `reference_file = self.reference_output_path / f"{case_id}_reference.json"`
  - Fix: Add check: (x / f) if f != 0 else 0.0
- Line 275: Division by resurface (could be zero) without check
  - Code: `This allows users to reflect/resurface seed instances or provide`
  - Fix: Add check: (x / resurface) if resurface != 0 else 0.0
- Line 352: Division by agent_prompts (could be zero) without check
  - Code: `parser.add_argument("--knowledge-base", default="tools/agent_prompts", help="Knowledge base path")`
  - Fix: Add check: (x / agent_prompts) if agent_prompts != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\agent_prompts\reference_generator.py**
- Line 252: Division by plan (could be zero) without check
  - Code: `workflow.append("3. Run /plan to create backlog")`
  - Fix: Add check: (x / plan) if plan != 0 else 0.0
- Line 255: Division by execute (could be zero) without check
  - Code: `workflow.append("4. Run /execute to generate artifacts")`
  - Fix: Add check: (x / execute) if execute != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\agent_validate.py**
- Line 113: Division by schemas (could be zero) without check
  - Code: `# Handle OpenAPI references like "openapi.yaml#/components/schemas/BassSpec"`
  - Fix: Add check: (x / schemas) if schemas != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\antigravity_skill_store\grid_master\scripts\health_check.py**
- Line 63: Division by api (could be zero) without check
  - Code: `resp = requests.get("http://localhost:11434/api/tags", timeout=2)`
  - Fix: Add check: (x / api) if api != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\architectural_audit.py**
- Line 239: Division by directory (could be zero) without check
  - Code: `steps.append(f"1. Create routers/ directory in {target_domain}/")`
  - Fix: Add check: (x / directory) if directory != 0 else 0.0
- Line 240: Division by directory (could be zero) without check
  - Code: `steps.append(f"2. Create services/ directory in {target_domain}/")`
  - Fix: Add check: (x / directory) if directory != 0 else 0.0
- Line 241: Division by directory (could be zero) without check
  - Code: `steps.append(f"3. Create repositories/ directory in {target_domain}/")`
  - Fix: Add check: (x / directory) if directory != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\collect_interfaces_metrics.py**
- Line 441: Division by SQLite (could be zero) without check
  - Code: `parser = argparse.ArgumentParser(description="Collect interfaces metrics and push to Databricks/SQLite")`
  - Fix: Add check: (x / SQLite) if SQLite != 0 else 0.0
- Line 473: Division by traces (could be zero) without check
  - Code: `help="Collect metrics from JSON files instead of audit logs/traces",`
  - Fix: Add check: (x / traces) if traces != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\interfaces_dashboard\dashboard.py**
- Line 54: Division by html (could be zero) without check
  - Code: `self.send_header("Content-Type", "text/html")`
  - Fix: Add check: (x / html) if html != 0 else 0.0
- Line 66: Division by metrics (could be zero) without check
  - Code: `if path == "/api/metrics":`
  - Fix: Add check: (x / metrics) if metrics != 0 else 0.0
- Line 74: Division by json (could be zero) without check
  - Code: `self.send_header("Content-Type", "application/json")`
  - Fix: Add check: (x / json) if json != 0 else 0.0
- Line 83: Division by json (could be zero) without check
  - Code: `self.send_header("Content-Type", "application/json")`
  - Fix: Add check: (x / json) if json != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\chat.py**
- Line 293: Division by tags (could be zero) without check
  - Code: `resp = await client.get(f"{self.config.ollama_base_url}/api/tags")`
  - Fix: Add check: (x / tags) if tags != 0 else 0.0
- Line 547: Division by A (could be zero) without check
  - Code: `print(c(f"  Collection: {stats.get('collection_name', 'N/A')}", Colors.WHITE))`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 548: Division by A (could be zero) without check
  - Code: `print(c(f"  Embedding Model: {stats.get('embedding_model', 'N/A')}", Colors.WHITE))`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 606: Division by quit (could be zero) without check
  - Code: `print(c("\n\nInterrupted. Type /quit to exit.", Colors.YELLOW))`
  - Fix: Add check: (x / quit) if quit != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\cli.py**
- Line 76: Division by application (could be zero) without check
  - Code: `"grid/application.py",`
  - Fix: Add check: (x / application) if application != 0 else 0.0
- Line 77: Division by __main__ (could be zero) without check
  - Code: `"grid/__main__.py",`
  - Fix: Add check: (x / __main__) if __main__ != 0 else 0.0
- Line 78: Division by awareness (could be zero) without check
  - Code: `"grid/awareness/context.py",`
  - Fix: Add check: (x / awareness) if awareness != 0 else 0.0
- Line 139: Division by high (could be zero) without check
  - Code: `help="Curated rebuild index using a small high-signal file set (recommended for fast/high-quality retrieval)",`
  - Fix: Add check: (x / high) if high != 0 else 0.0
- Line 177: Division by indexing (could be zero) without check
  - Code: `help="Number of docs files to preselect before embedding/indexing (default: 50)",`
  - Fix: Add check: (x / indexing) if indexing != 0 else 0.0
- Line 183: Division by index (could be zero) without check
  - Code: `help="Hard cap on number of chunks to embed/index per query (default: 2000)",`
  - Fix: Add check: (x / index) if index != 0 else 0.0
- Line 290: Division by N (could be zero) without check
  - Code: `response = input("  Continue anyway? [y/N]: ")`
  - Fix: Add check: (x / N) if N != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\comprehensive_indexer.py**
- Line 309: Division by sentence (could be zero) without check
  - Code: `# Get first line/sentence`
  - Fix: Add check: (x / sentence) if sentence != 0 else 0.0
- Line 656: Division by chars_per_line (could be zero) without check
  - Code: `target_lines = int(self.max_chunk_size / chars_per_line)`
  - Fix: Add check: (x / chars_per_line) if chars_per_line != 0 else 0.0
- Line 758: Division by whitespace (could be zero) without check
  - Code: `"""Calculate ratio of code vs comments/whitespace."""`
  - Fix: Add check: (x / whitespace) if whitespace != 0 else 0.0
- Line 1433: Division by all (could be zero) without check
  - Code: `default="sentence-transformers/all-MiniLM-L6-v2",`
  - Fix: Add check: (x / all) if all != 0 else 0.0
- Line 1435: Division by all (could be zero) without check
  - Code: `"sentence-transformers/all-MiniLM-L6-v2",`
  - Fix: Add check: (x / all) if all != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\config.py**
- Line 122: Division by Reranker (could be zero) without check
  - Code: `# Hybrid/Reranker config`
  - Fix: Add check: (x / Reranker) if Reranker != 0 else 0.0
- Line 126: Division by ms (could be zero) without check
  - Code: `cross_encoder_model=os.getenv("RAG_CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2"),`
  - Fix: Add check: (x / ms) if ms != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\conversational_rag.py**
- Line 376: Division by mcp (could be zero) without check
  - Code: `"docs/mcp/",`
  - Fix: Add check: (x / mcp) if mcp != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\cross_encoder_reranker.py**
- Line 78: Division by ms (could be zero) without check
  - Code: `model_name = "cross-encoder/ms-marco-MiniLM-L6-v2"`
  - Fix: Add check: (x / ms) if ms != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\embeddings\nomic_v2.py**
- Line 92: Division by None (could be zero) without check
  - Code: `#     print(f"DEBUG: Embedding is empty/None for {model_name}. Response keys/attrs: {dir(response)}")`
  - Fix: Add check: (x / None) if None != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\indexer\distributed_spark_indexer.py**
- Line 273: Division by api (could be zero) without check
  - Code: `"http://localhost:11434/api/embeddings",`
  - Fix: Add check: (x / api) if api != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\intelligence\entity_extractor.py**
- Line 48: Division by Constants (could be zero) without check
  - Code: `# Environment variables / Constants: GRID_QUIET`
  - Fix: Add check: (x / Constants) if Constants != 0 else 0.0
- Line 134: Division by rag (could be zero) without check
  - Code: `"How does `RAGEngine.query` work in tools/rag/rag_engine.py?",`
  - Fix: Add check: (x / rag) if rag != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\intelligence\test_phase3.py**
- Line 295: Division by A (could be zero) without check
  - Code: `print(f"Total Time: {metrics['timing'].get('total', 'N/A')}")`
  - Fix: Add check: (x / A) if A != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\llm\factory.py**
- Line 22: Division by cloud (could be zero) without check
  - Code: `"""Get an LLM provider with local/cloud selection.`
  - Fix: Add check: (x / cloud) if cloud != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\on_demand_engine.py**
- Line 88: Division by window (could be zero) without check
  - Code: `# If Ollama embeddings fail (context/window issues), fall back to HF embeddings locally.`
  - Fix: Add check: (x / window) if window != 0 else 0.0
- Line 107: Division by using (could be zero) without check
  - Code: `# 1) Seed scope with docs/ using a cheap prefilter so we don't index everything.`
  - Fix: Add check: (x / using) if using != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\progress.py**
- Line 46: Division by sec (could be zero) without check
  - Code: `"""Calculate current rate (items/sec) using a rolling window."""`
  - Fix: Add check: (x / sec) if sec != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\utils.py**
- Line 25: Division by tags (could be zero) without check
  - Code: `response = client.get(f"{base_url.rstrip('/')}/api/tags")`
  - Fix: Add check: (x / tags) if tags != 0 else 0.0
- Line 42: Division by tags (could be zero) without check
  - Code: `response = client.get(f"{base_url.rstrip('/')}/api/tags")`
  - Fix: Add check: (x / tags) if tags != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\scripts\debug_nav_test.py**
- Line 34: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\security\vulnerability_scanner.py**
- Line 602: Division by data (could be zero) without check
  - Code: `references=["https://cwe.mitre.org/data/definitions/78.html"],`
  - Fix: Add check: (x / data) if data != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\slash_commands\ci.py**
- Line 354: Division by ci (could be zero) without check
  - Code: `"""Return help text for the /ci command"""`
  - Fix: Add check: (x / ci) if ci != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\slash_commands\sync.py**
- Line 487: Division by sync (could be zero) without check
  - Code: `recommendations.append("No new documents found - consider running /sync without --quick")`
  - Fix: Add check: (x / sync) if sync != 0 else 0.0
- Line 517: Division by sync (could be zero) without check
  - Code: `"""Return help text for the /sync command"""`
  - Fix: Add check: (x / sync) if sync != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\__init__.py**
- Line 10: Division by thread (could be zero) without check
  - Code: `- stream_context: Session/thread/anchor management`
  - Fix: Add check: (x / thread) if thread != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\core\emergence_layer.py**
- Line 232: Division by patterns (could be zero) without check
  - Code: `Returns a map of topics/patterns to their current salience scores.`
  - Fix: Add check: (x / patterns) if patterns != 0 else 0.0
- Line 333: Division by type (could be zero) without check
  - Code: `# Extract action/type for sequence`
  - Fix: Add check: (x / type) if type != 0 else 0.0
- Line 399: Division by type (could be zero) without check
  - Code: `# Group by action/type`
  - Fix: Add check: (x / type) if type != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\core\engine.py**
- Line 342: Division by query (could be zero) without check
  - Code: `# Topic anchors from content/query`
  - Fix: Add check: (x / query) if query != 0 else 0.0
- Line 395: Division by type (could be zero) without check
  - Code: `# Direct action/type field`
  - Fix: Add check: (x / type) if type != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\protocols\discoverable.py**
- Line 30: Division by observed (could be zero) without check
  - Code: `discovery_timestamp: When this entity was created/observed.`
  - Fix: Add check: (x / observed) if observed != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\security\anomaly_detector.py**
- Line 465: Division by time_delta_seconds (could be zero) without check
  - Code: `gain_rate = (gain / time_delta_seconds) * 60`
  - Fix: Add check: (x / time_delta_seconds) if time_delta_seconds != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\security\audit_logger.py**
- Line 271: Division by security (could be zero) without check
  - Code: `log_dir: str = "logs/security"`
  - Fix: Add check: (x / security) if security != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\async_stress_harness.py**
- Line 99: Division by stress_metrics (could be zero) without check
  - Code: `parser.add_argument("--output", type=str, default="data/stress_metrics.json", help="Output JSON path")`
  - Fix: Add check: (x / stress_metrics) if stress_metrics != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\benchmark_arena_structure.py**
- Line 96: Division by elapsed (could be zero) without check
  - Code: `ops_per_sec = n_iterations / elapsed`
  - Fix: Add check: (x / elapsed) if elapsed != 0 else 0.0
- Line 151: Division by elapsed (could be zero) without check
  - Code: `ops_per_sec = n_ops / elapsed`
  - Fix: Add check: (x / elapsed) if elapsed != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_agentic_api.py**
- Line 45: Division by TEST (could be zero) without check
  - Code: `"reference_file_path": ".case_references/TEST-001_reference.json",`
  - Fix: Add check: (x / TEST) if TEST != 0 else 0.0
- Line 180: Division by api (could be zero) without check
  - Code: `"""Test GET /api/v1/agentic/cases/{case_id}."""`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 181: Division by v1 (could be zero) without check
  - Code: `response = client.get("/api/v1/agentic/cases/TEST-001")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 189: Division by api (could be zero) without check
  - Code: `"""Test GET /api/v1/agentic/cases/{case_id}/reference."""`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 190: Division by v1 (could be zero) without check
  - Code: `response = client.get("/api/v1/agentic/cases/TEST-001/reference")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 200: Division by api (could be zero) without check
  - Code: `"""Test GET /api/v1/agentic/experience."""`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 201: Division by v1 (could be zero) without check
  - Code: `response = client.get("/api/v1/agentic/experience")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_auth_jwt.py**
- Line 276: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/login",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 308: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/login",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 315: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 328: Division by v1 (could be zero) without check
  - Code: `response = client.get("/api/v1/auth/validate")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 371: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/login",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 432: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 441: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 457: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 483: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/login",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_e2e.py**
- Line 40: Division by v1 (could be zero) without check
  - Code: `response = client.get(f"/api/v1/resonance/envelope/{activity_id}")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 47: Division by v1 (could be zero) without check
  - Code: `response = client.get(f"/api/v1/resonance/events/{activity_id}")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 61: Division by v1 (could be zero) without check
  - Code: `response = client.get(f"/api/v1/resonance/envelope/{activity_id}")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 110: Division by v1 (could be zero) without check
  - Code: `response = client.get(f"/api/v1/resonance/envelope/{activity_id}")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 129: Division by v1 (could be zero) without check
  - Code: `response = client.get(f"/api/v1/resonance/envelope/{activity_id}")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 142: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/context",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 160: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/paths",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 186: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/context",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 193: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/paths",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_grid_benchmark.py**
- Line 225: Division by iterations (could be zero) without check
  - Code: `duration_ms = (end - start) * 1000 / iterations`
  - Fix: Add check: (x / iterations) if iterations != 0 else 0.0
- Line 297: Division by p95 (could be zero) without check
  - Code: `# SLA tracking (optional enforcement): Fail test if full_pipeline mean/p95/p99 > 0.1 ms`
  - Fix: Add check: (x / p95) if p95 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_jwt_security_advanced.py**
- Line 431: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 444: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 454: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/login",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 461: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 488: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/login",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 559: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 575: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 610: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 616: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_navigation.py**
- Line 65: Division by v1 (could be zero) without check
  - Code: `response = client.post("/api/v1/navigation/plan", json={"goal": "Implement user login"})`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 130: Division by v1 (could be zero) without check
  - Code: `response = client.post("/api/v1/navigation/plan", json={})`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 179: Division by v1 (could be zero) without check
  - Code: `response = client.post("/api/v1/navigation/plan", json={"goal": f"Test goal {_}", "max_alternatives": 1})`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 188: Division by v1 (could be zero) without check
  - Code: `response = client.options("/api/v1/navigation/plan")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 195: Division by v1 (could be zero) without check
  - Code: `response = client.get("/api/v1/navigation/plan")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_pipeline_productivity.py**
- Line 283: Division by baseline_time (could be zero) without check
  - Code: `baseline_metrics.throughput_assets_per_second = num_assets / baseline_time`
  - Fix: Add check: (x / baseline_time) if baseline_time != 0 else 0.0
- Line 287: Division by refined_time (could be zero) without check
  - Code: `refined_metrics.throughput_assets_per_second = num_assets / refined_time`
  - Fix: Add check: (x / refined_time) if refined_time != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_property_based_auth.py**
- Line 534: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 651: Division by v1 (could be zero) without check
  - Code: `"/api/v1/auth/validate",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_router.py**
- Line 4: Division by response (could be zero) without check
  - Code: `Tests REST endpoints with TestClient, request/response validation, and error handling.`
  - Fix: Add check: (x / response) if response != 0 else 0.0
- Line 54: Division by api (could be zero) without check
  - Code: `"""Test GET /api/v1/resonance/context endpoint."""`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 59: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/context",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 78: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/context",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 88: Division by v1 (could be zero) without check
  - Code: `response = client.get("/api/v1/resonance/context")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 94: Division by api (could be zero) without check
  - Code: `"""Test GET /api/v1/resonance/paths endpoint."""`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 99: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/paths",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 117: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/paths",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 127: Division by v1 (could be zero) without check
  - Code: `response = client.get("/api/v1/resonance/paths")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 133: Division by api (could be zero) without check
  - Code: `"""Test GET /api/v1/resonance/envelope/{activity_id} endpoint."""`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 137: Division by v1 (could be zero) without check
  - Code: `response = client.get(f"/api/v1/resonance/envelope/{sample_activity_id}")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 150: Division by v1 (could be zero) without check
  - Code: `response = client.get("/api/v1/resonance/envelope/non-existent-id")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 177: Division by api (could be zero) without check
  - Code: `"""Test GET /api/v1/resonance/events/{activity_id} endpoint."""`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 182: Division by v1 (could be zero) without check
  - Code: `f"/api/v1/resonance/events/{sample_activity_id}",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 196: Division by v1 (could be zero) without check
  - Code: `f"/api/v1/resonance/events/{sample_activity_id}",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 208: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/process",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 214: Division by v1 (could be zero) without check
  - Code: `response = client.get(f"/api/v1/resonance/events/{activity_id}")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 367: Division by v1 (could be zero) without check
  - Code: `"/api/v1/resonance/definitive",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_security_governance.py**
- Line 11: Division by api (could be zero) without check
  - Code: `Run with: pytest tests/api/test_security_governance.py -v`
  - Fix: Add check: (x / api) if api != 0 else 0.0
- Line 285: Division by v1 (could be zero) without check
  - Code: `{"path": "/api/v1/data", "method": "POST", "auth_level": "integrity"},`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 479: Division by path (could be zero) without check
  - Code: `circuit = manager.get_circuit("/test/path")`
  - Fix: Add check: (x / path) if path != 0 else 0.0
- Line 480: Division by path (could be zero) without check
  - Code: `assert circuit.key == "/test/path"`
  - Fix: Add check: (x / path) if path != 0 else 0.0
- Line 484: Division by path (could be zero) without check
  - Code: `circuit1 = manager.get_circuit("/test/path")`
  - Fix: Add check: (x / path) if path != 0 else 0.0
- Line 485: Division by path (could be zero) without check
  - Code: `circuit2 = manager.get_circuit("/test/path")`
  - Fix: Add check: (x / path) if path != 0 else 0.0
- Line 490: Division by path (could be zero) without check
  - Code: `circuit = manager.get_circuit("/test/path")`
  - Fix: Add check: (x / path) if path != 0 else 0.0
- Line 493: Division by path (could be zero) without check
  - Code: `result = manager.reset_circuit("/test/path")`
  - Fix: Add check: (x / path) if path != 0 else 0.0
- Line 788: Division by test (could be zero) without check
  - Code: `response = client.post("/api/test", json={"name": "safe data"})`
  - Fix: Add check: (x / test) if test != 0 else 0.0
- Line 816: Division by test (could be zero) without check
  - Code: `response = client.post("/api/test", json={"name": "test"}, headers={"X-Request-ID": "test-123"})`
  - Fix: Add check: (x / test) if test != 0 else 0.0
- Line 846: Division by data (could be zero) without check
  - Code: `@app.post("/api/data")`
  - Fix: Add check: (x / data) if data != 0 else 0.0
- Line 859: Division by data (could be zero) without check
  - Code: `response = client.post("/api/data", json={"name": "test", "value": 42})`
  - Fix: Add check: (x / data) if data != 0 else 0.0
- Line 994: Division by security (could be zero) without check
  - Code: `@app.get("/health/security")`
  - Fix: Add check: (x / security) if security != 0 else 0.0
- Line 1012: Division by security (could be zero) without check
  - Code: `response = client.get("/health/security")`
  - Fix: Add check: (x / security) if security != 0 else 0.0
- Line 1042: Division by v1 (could be zero) without check
  - Code: `response = client.post("/api/v1/failing")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 1052: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 1061: Division by security (could be zero) without check
  - Code: `response = client.get("/health/security")`
  - Fix: Add check: (x / security) if security != 0 else 0.0
- Line 1199: Division by test (could be zero) without check
  - Code: `response = client.post("/api/test", json={"key": "value"})`
  - Fix: Add check: (x / test) if test != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_streaming_security.py**
- Line 154: Division by json (could be zero) without check
  - Code: `"Content-Type": "application/json",`
  - Fix: Add check: (x / json) if json != 0 else 0.0
- Line 241: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 243: Division by event (could be zero) without check
  - Code: `headers={"Accept": "text/event-stream", "X-Request-ID": "propagation-test-456"},`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 275: Division by v1 (could be zero) without check
  - Code: `response = client.post("/api/v1/failing-stream", json={})`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 330: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 332: Division by event (could be zero) without check
  - Code: `headers={"Accept": "text/event-stream", "X-Request-ID": f"parallel-{request_id}"},`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 357: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 365: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 367: Division by event (could be zero) without check
  - Code: `headers={"Accept": "text/event-stream"},`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 490: Division by event (could be zero) without check
  - Code: `headers={"Accept": "text/event-stream", "X-Request-ID": "ghost-test-789"},`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 494: Division by event (could be zero) without check
  - Code: `assert response.headers["Content-Type"].startswith("text/event-stream")`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 563: Division by v1 (could be zero) without check
  - Code: `response = client.post("/api/v1/slow-stream", json={})`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 572: Division by v1 (could be zero) without check
  - Code: `response = client.post("/api/v1/slow-stream", json={})`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 580: Division by security (could be zero) without check
  - Code: `response = client.get("/health/security")`
  - Fix: Add check: (x / security) if security != 0 else 0.0
- Line 587: Division by circuit (could be zero) without check
  - Code: `response = client.get("/health/circuit-breakers")`
  - Fix: Add check: (x / circuit) if circuit != 0 else 0.0
- Line 648: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 650: Division by event (could be zero) without check
  - Code: `headers={"Accept": "text/event-stream"},`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 656: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 658: Division by event (could be zero) without check
  - Code: `headers={"Accept": "text/event-stream"},`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 664: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 666: Division by event (could be zero) without check
  - Code: `headers={"Accept": "text/event-stream"},`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 676: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 684: Division by security (could be zero) without check
  - Code: `health_resp = client.get("/health/security")`
  - Fix: Add check: (x / security) if security != 0 else 0.0
- Line 694: Division by v1 (could be zero) without check
  - Code: `"/api/v1/navigation/plan-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 700: Division by security (could be zero) without check
  - Code: `health_resp = client.get("/health/security")`
  - Fix: Add check: (x / security) if security != 0 else 0.0
- Line 773: Division by concurrent (could be zero) without check
  - Code: `"/api/concurrent-stream",`
  - Fix: Add check: (x / concurrent) if concurrent != 0 else 0.0
- Line 775: Division by event (could be zero) without check
  - Code: `headers={"Accept": "text/event-stream"},`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 784: Division by event (could be zero) without check
  - Code: `# All requests should receive all events (3 events = 9 lines with data/event/newline)`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 890: Division by event (could be zero) without check
  - Code: `response = client.get("/sse-test", headers={"Accept": "text/event-stream"})`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 893: Division by event (could be zero) without check
  - Code: `assert response.headers["Content-Type"].startswith("text/event-stream")`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 933: Division by event (could be zero) without check
  - Code: `response = client.get("/sse-id-test", headers={"Accept": "text/event-stream"})`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 969: Division by event (could be zero) without check
  - Code: `response = client.get("/sse-retry-test", headers={"Accept": "text/event-stream"})`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 1000: Division by event (could be zero) without check
  - Code: `response = client.get("/sse-empty-test", headers={"Accept": "text/event-stream"})`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 1270: Division by v1 (could be zero) without check
  - Code: `@app.post("/api/v1/secure-stream")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 1401: Division by v1 (could be zero) without check
  - Code: `"/api/v1/secure-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 1412: Division by v1 (could be zero) without check
  - Code: `"/api/v1/secure-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 1518: Division by v1 (could be zero) without check
  - Code: `@app.post("/api/v1/e2e-stream")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 1535: Division by security (could be zero) without check
  - Code: `response = client.get("/health/security")`
  - Fix: Add check: (x / security) if security != 0 else 0.0
- Line 1543: Division by v1 (could be zero) without check
  - Code: `"/api/v1/e2e-stream",`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 1545: Division by event (could be zero) without check
  - Code: `headers={"Accept": "text/event-stream", "X-Request-ID": "e2e-test-123"},`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 1549: Division by event (could be zero) without check
  - Code: `assert response.headers["Content-Type"].startswith("text/event-stream")`
  - Fix: Add check: (x / event) if event != 0 else 0.0
- Line 1639: Division by security (could be zero) without check
  - Code: `response = client.get("/health/security")`
  - Fix: Add check: (x / security) if security != 0 else 0.0
- Line 1660: Division by circuit (could be zero) without check
  - Code: `response = client.get("/health/circuit-breakers")`
  - Fix: Add check: (x / circuit) if circuit != 0 else 0.0
- Line 1678: Division by second (could be zero) without check
  - Code: `assert defaults.rate_limit == "10/second"`
  - Fix: Add check: (x / second) if second != 0 else 0.0
- Line 1682: Division by security (could be zero) without check
  - Code: `response = client.get("/health/security")`
  - Fix: Add check: (x / security) if security != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\mcp\servers\database\server.py**
- Line 239: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\mcp\servers\filesystem\production_server.py**
- Line 70: Division by irfan (could be zero) without check
  - Code: `os.path.expanduser("~"),  # C:/Users/irfan`
  - Fix: Add check: (x / irfan) if irfan != 0 else 0.0
- Line 217: Division by directory (could be zero) without check
  - Code: `"""Get file/directory information"""`
  - Fix: Add check: (x / directory) if directory != 0 else 0.0
- Line 301: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\mcp\servers\filesystem\server.py**
- Line 43: Division by irfan (could be zero) without check
  - Code: `os.path.expanduser("~"),  # C:/Users/irfan`
  - Fix: Add check: (x / irfan) if irfan != 0 else 0.0
- Line 183: Division by directory (could be zero) without check
  - Code: `"""Get file/directory information"""`
  - Fix: Add check: (x / directory) if directory != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\mcp\servers\memory\production_server.py**
- Line 319: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\mcp\servers\playwright\server.py**
- Line 546: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\mcp\servers\postgres\production_server.py**
- Line 83: Division by grid (could be zero) without check
  - Code: `database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/grid")`
  - Fix: Add check: (x / grid) if grid != 0 else 0.0
- Line 370: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\servers\database\server.py**
- Line 239: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\servers\filesystem\production_server.py**
- Line 70: Division by irfan (could be zero) without check
  - Code: `os.path.expanduser("~"),  # C:/Users/irfan`
  - Fix: Add check: (x / irfan) if irfan != 0 else 0.0
- Line 217: Division by directory (could be zero) without check
  - Code: `"""Get file/directory information"""`
  - Fix: Add check: (x / directory) if directory != 0 else 0.0
- Line 301: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\servers\filesystem\server.py**
- Line 43: Division by irfan (could be zero) without check
  - Code: `os.path.expanduser("~"),  # C:/Users/irfan`
  - Fix: Add check: (x / irfan) if irfan != 0 else 0.0
- Line 183: Division by directory (could be zero) without check
  - Code: `"""Get file/directory information"""`
  - Fix: Add check: (x / directory) if directory != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\servers\memory\production_server.py**
- Line 319: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\servers\playwright\server.py**
- Line 546: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\servers\postgres\production_server.py**
- Line 83: Division by grid (could be zero) without check
  - Code: `database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/grid")`
  - Fix: Add check: (x / grid) if grid != 0 else 0.0
- Line 370: Division by plain (could be zero) without check
  - Code: `return web.Response(text="healthy\n", content_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\servers\postgres\server.py**
- Line 42: Division by grid (could be zero) without check
  - Code: `database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/grid")`
  - Fix: Add check: (x / grid) if grid != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\analyze_issues.py**
- Line 14: Division by backend (could be zero) without check
  - Code: `# Filter out apps/backend and e:/app`
  - Fix: Add check: (x / backend) if backend != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\analyze_issues_detailed.py**
- Line 14: Division by backend (could be zero) without check
  - Code: `# Filter out apps/backend and e:/app`
  - Fix: Add check: (x / backend) if backend != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\analyze_repo.py**
- Line 138: Division by YAML (could be zero) without check
  - Code: `"""Redact secret values in JSON/YAML content."""`
  - Fix: Add check: (x / YAML) if YAML != 0 else 0.0
- Line 303: Division by exports (could be zero) without check
  - Code: `# Try to detect imports/exports`
  - Fix: Add check: (x / exports) if exports != 0 else 0.0
- Line 369: Division by JavaScript (could be zero) without check
  - Code: `# Detect docstrings (JSDoc for TypeScript/JavaScript)`
  - Fix: Add check: (x / JavaScript) if JavaScript != 0 else 0.0
- Line 476: Division by fan (could be zero) without check
  - Code: `# Calculate fan-in/fan-out`
  - Fix: Add check: (x / fan) if fan != 0 else 0.0
- Line 553: Division by metrics (could be zero) without check
  - Code: `full_path = self.root_path / metrics.path`
  - Fix: Add check: (x / metrics) if metrics != 0 else 0.0
- Line 646: Division by file_info (could be zero) without check
  - Code: `path = self.root_path / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\cleanup_temp.py**
- Line 130: Division by item (could be zero) without check
  - Code: `archive_path = ARCHIVE_DIR / item.relative_to(workspace_root)`
  - Fix: Add check: (x / item) if item != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\compare_projects.py**
- Line 90: Division by fan (could be zero) without check
  - Code: `# Compare fan-in/fan-out (traffic patterns)`
  - Fix: Add check: (x / fan) if fan != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\generate_artifacts.py**
- Line 363: Division by file_info (could be zero) without check
  - Code: `file_path = repo_root / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0
- Line 388: Division by TSX (could be zero) without check
  - Code: `# Search in TypeScript/TSX files`
  - Fix: Add check: (x / TSX) if TSX != 0 else 0.0
- Line 393: Division by file_info (could be zero) without check
  - Code: `file_path = repo_root / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0
- Line 717: Division by Transform (could be zero) without check
  - Code: `│   Warehouse     │   │    │  (Fetch/Transform)│`
  - Fix: Add check: (x / Transform) if Transform != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\init_safety_logging.py**
- Line 307: Division by allow (could be zero) without check
  - Code: `print("  ├── enforcement/     - Server denial/allow decisions")`
  - Fix: Add check: (x / allow) if allow != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\project_path_protector.py**
- Line 126: Division by A (could be zero) without check
  - Code: `f"Destination: {dest_path or 'N/A'}\n\n"`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 194: Division by project_path_protection (could be zero) without check
  - Code: `default='config/project_path_protection.json',`
  - Fix: Add check: (x / project_path_protection) if project_path_protection != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\verify_eufle_setup.py**
- Line 42: Division by api (could be zero) without check
  - Code: `response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)`
  - Fix: Add check: (x / api) if api != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\security\integrate_security.py**
- Line 380: Division by monitor_network (could be zero) without check
  - Code: `# 2. Check blocked requests: python security/monitor_network.py blocked`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0
- Line 381: Division by monitor_network (could be zero) without check
  - Code: `# 3. Whitelist trusted domains: python security/monitor_network.py add <domain>`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0
- Line 382: Division by monitor_network (could be zero) without check
  - Code: `# 4. Monitor continuously: python security/monitor_network.py dashboard`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\security\monitor_network.py**
- Line 5: Division by allowed (could be zero) without check
  - Code: `Provides CLI interface to view blocked/allowed requests and manage whitelist.`
  - Fix: Add check: (x / allowed) if allowed != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\security\test_security.py**
- Line 271: Division by monitor_network (could be zero) without check
  - Code: `print("2. Run: python security/monitor_network.py dashboard")`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\shared\studio_agent_config\functions.py**
- Line 179: Division by completions (could be zero) without check
  - Code: `chat=endpoints.get("chat", "/chat/completions"),`
  - Fix: Add check: (x / completions) if completions != 0 else 0.0
- Line 574: Division by limitations (could be zero) without check
  - Code: `summarized_system_prompt="The Mistral agent assists with pattern recognition, data validation, decision logging, artifact generation, and dynamic capability retrieval within the GRID ecosystem. Key guidelines include: Communication: Be clear, concise, context-aware, user-centric, and avoid unnecessary jargon. Task Execution: Pattern Recognition: Extract relevant entities, relationships, sentiment, and intent from input text. Data Validation: Validate discussion rows against the Great Hall schema; provide clear feedback on issues. Decision Logging: Record decisions accurately with context, traceability, and compliance to Great Hall schema. Artifact Generation: Generate artifacts in specified formats (JSON, markdown, HTML, CSV); validate against relevant schemas. Capability Retrieval: Dynamically retrieve GRID subsystems or tools based on context; warn users of unavailable capabilities. Error Handling: Address unavailable services with fallback responses; mark uncertain outputs and provide recommendations for improving confidence levels. Output Formatting: Maintain consistent formatting, readability, and traceability in outputs. Include provenance information where applicable. Constraints & Compliance: Ensure adherence to schemas, specified constraints, GRID ecosystem policies, and cross-reference linked criteria against session schema. User Interaction: Provide clear feedback, transparency about capabilities/limitations, prompt responsiveness, and inform users about task progress/status.",`
  - Fix: Add check: (x / limitations) if limitations != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\shared\workspace_utils\eufle_verifier.py**
- Line 57: Division by api (could be zero) without check
  - Code: `response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)`
  - Fix: Add check: (x / api) if api != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\shared\workspace_utils\repo_analyzer.py**
- Line 149: Division by YAML (could be zero) without check
  - Code: `"""Redact secret values in JSON/YAML content."""`
  - Fix: Add check: (x / YAML) if YAML != 0 else 0.0
- Line 538: Division by file_info (could be zero) without check
  - Code: `path = self.root_path / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0
- Line 658: Division by metrics (could be zero) without check
  - Code: `full_path = self.root_path / metrics.path`
  - Fix: Add check: (x / metrics) if metrics != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\shared\workspace_utils\tests\test_project_comparator.py**
- Line 122: Division by analysis1 (could be zero) without check
  - Code: `project1_analysis_dir="temp/analysis1",`
  - Fix: Add check: (x / analysis1) if analysis1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\stripe-sample-code\server.py**
- Line 21: Division by test (could be zero) without check
  - Code: `"Get your key from: https://dashboard.stripe.com/test/apikeys"`
  - Fix: Add check: (x / test) if test != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\tests\test_endpoints.py**
- Line 21: Division by cache (could be zero) without check
  - Code: `# May be 200 or 503 depending on database/cache availability`
  - Fix: Add check: (x / cache) if cache != 0 else 0.0
- Line 43: Division by services (could be zero) without check
  - Code: `# Skipping actual request since database/services may not be configured`
  - Fix: Add check: (x / services) if services != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\analyze_issues.py**
- Line 14: Division by backend (could be zero) without check
  - Code: `# Filter out apps/backend and e:/app`
  - Fix: Add check: (x / backend) if backend != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\analyze_issues_detailed.py**
- Line 14: Division by backend (could be zero) without check
  - Code: `# Filter out apps/backend and e:/app`
  - Fix: Add check: (x / backend) if backend != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\analyze_repo.py**
- Line 138: Division by YAML (could be zero) without check
  - Code: `"""Redact secret values in JSON/YAML content."""`
  - Fix: Add check: (x / YAML) if YAML != 0 else 0.0
- Line 303: Division by exports (could be zero) without check
  - Code: `# Try to detect imports/exports`
  - Fix: Add check: (x / exports) if exports != 0 else 0.0
- Line 369: Division by JavaScript (could be zero) without check
  - Code: `# Detect docstrings (JSDoc for TypeScript/JavaScript)`
  - Fix: Add check: (x / JavaScript) if JavaScript != 0 else 0.0
- Line 476: Division by fan (could be zero) without check
  - Code: `# Calculate fan-in/fan-out`
  - Fix: Add check: (x / fan) if fan != 0 else 0.0
- Line 553: Division by metrics (could be zero) without check
  - Code: `full_path = self.root_path / metrics.path`
  - Fix: Add check: (x / metrics) if metrics != 0 else 0.0
- Line 646: Division by file_info (could be zero) without check
  - Code: `path = self.root_path / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\cleanup_temp.py**
- Line 130: Division by item (could be zero) without check
  - Code: `archive_path = ARCHIVE_DIR / item.relative_to(workspace_root)`
  - Fix: Add check: (x / item) if item != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\compare_projects.py**
- Line 90: Division by fan (could be zero) without check
  - Code: `# Compare fan-in/fan-out (traffic patterns)`
  - Fix: Add check: (x / fan) if fan != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\generate_artifacts.py**
- Line 363: Division by file_info (could be zero) without check
  - Code: `file_path = repo_root / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0
- Line 388: Division by TSX (could be zero) without check
  - Code: `# Search in TypeScript/TSX files`
  - Fix: Add check: (x / TSX) if TSX != 0 else 0.0
- Line 393: Division by file_info (could be zero) without check
  - Code: `file_path = repo_root / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0
- Line 717: Division by Transform (could be zero) without check
  - Code: `│   Warehouse     │   │    │  (Fetch/Transform)│`
  - Fix: Add check: (x / Transform) if Transform != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\init_safety_logging.py**
- Line 307: Division by allow (could be zero) without check
  - Code: `print("  ├── enforcement/     - Server denial/allow decisions")`
  - Fix: Add check: (x / allow) if allow != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\profile_python_entrypoints.py**
- Line 194: Division by PY_ENTRYPOINT_PROFILE (could be zero) without check
  - Code: `parser.add_argument("--output-md", default="E:/analysis_outputs/PY_ENTRYPOINT_PROFILE.md")`
  - Fix: Add check: (x / PY_ENTRYPOINT_PROFILE) if PY_ENTRYPOINT_PROFILE != 0 else 0.0
- Line 195: Division by PY_ENTRYPOINT_PROFILE (could be zero) without check
  - Code: `parser.add_argument("--output-json", default="E:/analysis_outputs/PY_ENTRYPOINT_PROFILE.json")`
  - Fix: Add check: (x / PY_ENTRYPOINT_PROFILE) if PY_ENTRYPOINT_PROFILE != 0 else 0.0
- Line 196: Division by python_entrypoint_blocklist (could be zero) without check
  - Code: `parser.add_argument("--blocklist-out", default="E:/config/python_entrypoint_blocklist.json")`
  - Fix: Add check: (x / python_entrypoint_blocklist) if python_entrypoint_blocklist != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\project_path_protector.py**
- Line 126: Division by A (could be zero) without check
  - Code: `f"Destination: {dest_path or 'N/A'}\n\n"`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 194: Division by project_path_protection (could be zero) without check
  - Code: `default='config/project_path_protection.json',`
  - Fix: Add check: (x / project_path_protection) if project_path_protection != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\verify_eufle_setup.py**
- Line 42: Division by api (could be zero) without check
  - Code: `response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)`
  - Fix: Add check: (x / api) if api != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\security\integrate_security.py**
- Line 380: Division by monitor_network (could be zero) without check
  - Code: `# 2. Check blocked requests: python security/monitor_network.py blocked`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0
- Line 381: Division by monitor_network (could be zero) without check
  - Code: `# 3. Whitelist trusted domains: python security/monitor_network.py add <domain>`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0
- Line 382: Division by monitor_network (could be zero) without check
  - Code: `# 4. Monitor continuously: python security/monitor_network.py dashboard`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\security\monitor_network.py**
- Line 5: Division by allowed (could be zero) without check
  - Code: `Provides CLI interface to view blocked/allowed requests and manage whitelist.`
  - Fix: Add check: (x / allowed) if allowed != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\security\test_security.py**
- Line 271: Division by monitor_network (could be zero) without check
  - Code: `print("2. Run: python security/monitor_network.py dashboard")`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\shared\studio_agent_config\functions.py**
- Line 179: Division by completions (could be zero) without check
  - Code: `chat=endpoints.get("chat", "/chat/completions"),`
  - Fix: Add check: (x / completions) if completions != 0 else 0.0
- Line 574: Division by limitations (could be zero) without check
  - Code: `summarized_system_prompt="The Mistral agent assists with pattern recognition, data validation, decision logging, artifact generation, and dynamic capability retrieval within the GRID ecosystem. Key guidelines include: Communication: Be clear, concise, context-aware, user-centric, and avoid unnecessary jargon. Task Execution: Pattern Recognition: Extract relevant entities, relationships, sentiment, and intent from input text. Data Validation: Validate discussion rows against the Great Hall schema; provide clear feedback on issues. Decision Logging: Record decisions accurately with context, traceability, and compliance to Great Hall schema. Artifact Generation: Generate artifacts in specified formats (JSON, markdown, HTML, CSV); validate against relevant schemas. Capability Retrieval: Dynamically retrieve GRID subsystems or tools based on context; warn users of unavailable capabilities. Error Handling: Address unavailable services with fallback responses; mark uncertain outputs and provide recommendations for improving confidence levels. Output Formatting: Maintain consistent formatting, readability, and traceability in outputs. Include provenance information where applicable. Constraints & Compliance: Ensure adherence to schemas, specified constraints, GRID ecosystem policies, and cross-reference linked criteria against session schema. User Interaction: Provide clear feedback, transparency about capabilities/limitations, prompt responsiveness, and inform users about task progress/status.",`
  - Fix: Add check: (x / limitations) if limitations != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\shared\workspace_utils\eufle_verifier.py**
- Line 57: Division by api (could be zero) without check
  - Code: `response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)`
  - Fix: Add check: (x / api) if api != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\shared\workspace_utils\repo_analyzer.py**
- Line 149: Division by YAML (could be zero) without check
  - Code: `"""Redact secret values in JSON/YAML content."""`
  - Fix: Add check: (x / YAML) if YAML != 0 else 0.0
- Line 538: Division by file_info (could be zero) without check
  - Code: `path = self.root_path / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0
- Line 658: Division by metrics (could be zero) without check
  - Code: `full_path = self.root_path / metrics.path`
  - Fix: Add check: (x / metrics) if metrics != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\shared\workspace_utils\tests\test_project_comparator.py**
- Line 122: Division by analysis1 (could be zero) without check
  - Code: `project1_analysis_dir="temp/analysis1",`
  - Fix: Add check: (x / analysis1) if analysis1 != 0 else 0.0

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\tests\test_endpoints.py**
- Line 21: Division by cache (could be zero) without check
  - Code: `# May be 200 or 503 depending on database/cache availability`
  - Fix: Add check: (x / cache) if cache != 0 else 0.0
- Line 43: Division by services (could be zero) without check
  - Code: `# Skipping actual request since database/services may not be configured`
  - Fix: Add check: (x / services) if services != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\config\audit_config.py**
- Line 125: Division by filename (could be zero) without check
  - Code: `return self.log_dir / filename`
  - Fix: Add check: (x / filename) if filename != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\config\rate_limiter.py**
- Line 199: Division by minute (could be zero) without check
  - Code: `requests_per_minute=30, burst_size=5  # Free tier: 30 calls/minute`
  - Fix: Add check: (x / minute) if minute != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\core\backup_manager.py**
- Line 375: Division by backup_id (could be zero) without check
  - Code: `shutil.copytree(backup_path, target / backup_id)`
  - Fix: Add check: (x / backup_id) if backup_id != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\core\webhook_manager.py**
- Line 243: Division by json (could be zero) without check
  - Code: `"Content-Type": "application/json",`
  - Fix: Add check: (x / json) if json != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\database\ai_safe_analyzer.py**
- Line 329: Division by sell (could be zero) without check
  - Code: `# Generate safe recommendations (no specific buy/sell advice)`
  - Fix: Add check: (x / sell) if sell != 0 else 0.0
- Line 382: Division by total_value (could be zero) without check
  - Code: `top_position_percentage = (top_position_value / total_value) * 100`
  - Fix: Add check: (x / total_value) if total_value != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\database\databricks_analyzer.py**
- Line 175: Division by total_value (could be zero) without check
  - Code: `top_position_percentage = (top_position_value / total_value) * 100`
  - Fix: Add check: (x / total_value) if total_value != 0 else 0.0
- Line 179: Division by total_value (could be zero) without check
  - Code: `top_3_percentage = (top_3_value / total_value) * 100`
  - Fix: Add check: (x / total_value) if total_value != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\features\fact_check.py**
- Line 25: Division by report (could be zero) without check
  - Code: `"""Schema for a grounded factual assertion in API/report outputs."""`
  - Fix: Add check: (x / report) if report != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\features\google_search_grounding.py**
- Line 17: Division by customsearch (could be zero) without check
  - Code: `_CUSTOM_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"`
  - Fix: Add check: (x / customsearch) if customsearch != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\integrations\coinbase_api.py**
- Line 105: Division by json (could be zero) without check
  - Code: `{"Content-Type": "application/json", "User-Agent": "CoinbasePlatform/1.0"}`
  - Fix: Add check: (x / json) if json != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\integrations\yahoo_finance.py**
- Line 44: Division by loss (could be zero) without check
  - Code: `"""Calculate total gain/loss."""`
  - Fix: Add check: (x / loss) if loss != 0 else 0.0
- Line 49: Division by loss (could be zero) without check
  - Code: `"""Calculate gain/loss percentage."""`
  - Fix: Add check: (x / loss) if loss != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\skills.py**
- Line 740: Division by Reward (could be zero) without check
  - Code: `# Risk/Reward calculation`
  - Fix: Add check: (x / Reward) if Reward != 0 else 0.0

**archive\build_backup\Coinbase\coinbase\verification\fast_verify.py**
- Line 348: Division by loss (could be zero) without check
  - Code: `lambda: (True, "Gain/loss is calculated correctly"),`
  - Fix: Add check: (x / loss) if loss != 0 else 0.0

**archive\build_backup\Coinbase\examples\databricks_integration.py**
- Line 57: Division by Loss (could be zero) without check
  - Code: `print(f"Total Gain/Loss: ${summary['total_gain_loss']:,.2f}")`
  - Fix: Add check: (x / Loss) if Loss != 0 else 0.0
- Line 126: Division by Loss (could be zero) without check
  - Code: `print(f"   Gain/Loss: {pos['gain_loss_percentage']:.2f}% | ${pos['total_gain_loss']:,.2f}")`
  - Fix: Add check: (x / Loss) if Loss != 0 else 0.0

**archive\build_backup\Coinbase\examples\real_portfolio_analysis.py**
- Line 50: Division by Loss (could be zero) without check
  - Code: `print(f"   Gain/Loss: {pos.gain_loss_percentage:.2f}% | ${pos.total_gain_loss:,.2f}")`
  - Fix: Add check: (x / Loss) if Loss != 0 else 0.0
- Line 63: Division by Loss (could be zero) without check
  - Code: `print(f"   Gain/Loss: {pos.gain_loss_percentage:.2f}% | ${pos.total_gain_loss:,.2f}")`
  - Fix: Add check: (x / Loss) if Loss != 0 else 0.0

**archive\build_backup\Coinbase\tests\benchmarks\bench_crypto_skills.py**
- Line 265: Division by price (could be zero) without check
  - Code: `diff_amount = diff_value / price`
  - Fix: Add check: (x / price) if price != 0 else 0.0

**archive\build_backup\Coinbase\tests\benchmarks\conftest.py**
- Line 207: Division by max (could be zero) without check
  - Code: `# Clamp to min/max`
  - Fix: Add check: (x / max) if max != 0 else 0.0

**archive\build_backup\Coinbase\tests\test_databricks_integration.py**
- Line 163: Division by portfolios (could be zero) without check
  - Code: `parser = YahooPortfolioParser("e:/Coinbase/portfolios/yahoo_portfolio.csv")`
  - Fix: Add check: (x / portfolios) if portfolios != 0 else 0.0
- Line 230: Division by total_purchase_value (could be zero) without check
  - Code: `gain_loss_percentage = (total_gain_loss / total_purchase_value) * 100`
  - Fix: Add check: (x / total_purchase_value) if total_purchase_value != 0 else 0.0

**archive\build_backup\Coinbase\tests\test_integration_workflows.py**
- Line 212: Division by corrupted (could be zero) without check
  - Code: `"""Test detection of invalid/corrupted data."""`
  - Fix: Add check: (x / corrupted) if corrupted != 0 else 0.0
- Line 300: Division by min (could be zero) without check
  - Code: `for _ in range(35):  # Exceeds CoinGecko limit of 30/min`
  - Fix: Add check: (x / min) if min != 0 else 0.0

**archive\build_backup\activate_guardrails.py**
- Line 292: Division by violations (could be zero) without check
  - Code: `print(f"  Modules w/violations : {enforcement.get('modules_with_violations', 0)}")`
  - Fix: Add check: (x / violations) if violations != 0 else 0.0

**archive\build_backup\api\middleware\boundary.py**
- Line 84: Division by json (could be zero) without check
  - Code: `media_type="application/json",`
  - Fix: Add check: (x / json) if json != 0 else 0.0
- Line 106: Division by API (could be zero) without check
  - Code: `# TODO: Implement proper JWT/API key validation`
  - Fix: Add check: (x / API) if API != 0 else 0.0

**archive\build_backup\api\middleware\rights_boundary.py**
- Line 41: Division by deny (could be zero) without check
  - Code: `4. Boundary decision (allow/deny/quarantine)`
  - Fix: Add check: (x / deny) if deny != 0 else 0.0
- Line 231: Division by PUT (could be zero) without check
  - Code: `# Try to get content from request body (for POST/PUT)`
  - Fix: Add check: (x / PUT) if PUT != 0 else 0.0

**archive\build_backup\api\schema\rights_boundary.py**
- Line 6: Division by response (could be zero) without check
  - Code: `- Request/response patterns with rights validation`
  - Fix: Add check: (x / response) if response != 0 else 0.0

**archive\build_backup\scripts\analyze_issues.py**
- Line 14: Division by backend (could be zero) without check
  - Code: `# Filter out apps/backend and e:/app`
  - Fix: Add check: (x / backend) if backend != 0 else 0.0

**archive\build_backup\scripts\analyze_issues_detailed.py**
- Line 14: Division by backend (could be zero) without check
  - Code: `# Filter out apps/backend and e:/app`
  - Fix: Add check: (x / backend) if backend != 0 else 0.0

**archive\build_backup\scripts\analyze_repo.py**
- Line 138: Division by YAML (could be zero) without check
  - Code: `"""Redact secret values in JSON/YAML content."""`
  - Fix: Add check: (x / YAML) if YAML != 0 else 0.0
- Line 303: Division by exports (could be zero) without check
  - Code: `# Try to detect imports/exports`
  - Fix: Add check: (x / exports) if exports != 0 else 0.0
- Line 369: Division by JavaScript (could be zero) without check
  - Code: `# Detect docstrings (JSDoc for TypeScript/JavaScript)`
  - Fix: Add check: (x / JavaScript) if JavaScript != 0 else 0.0
- Line 476: Division by fan (could be zero) without check
  - Code: `# Calculate fan-in/fan-out`
  - Fix: Add check: (x / fan) if fan != 0 else 0.0
- Line 553: Division by metrics (could be zero) without check
  - Code: `full_path = self.root_path / metrics.path`
  - Fix: Add check: (x / metrics) if metrics != 0 else 0.0
- Line 646: Division by file_info (could be zero) without check
  - Code: `path = self.root_path / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0

**archive\build_backup\scripts\cleanup_temp.py**
- Line 130: Division by item (could be zero) without check
  - Code: `archive_path = ARCHIVE_DIR / item.relative_to(workspace_root)`
  - Fix: Add check: (x / item) if item != 0 else 0.0

**archive\build_backup\scripts\compare_projects.py**
- Line 90: Division by fan (could be zero) without check
  - Code: `# Compare fan-in/fan-out (traffic patterns)`
  - Fix: Add check: (x / fan) if fan != 0 else 0.0

**archive\build_backup\scripts\generate_artifacts.py**
- Line 363: Division by file_info (could be zero) without check
  - Code: `file_path = repo_root / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0
- Line 388: Division by TSX (could be zero) without check
  - Code: `# Search in TypeScript/TSX files`
  - Fix: Add check: (x / TSX) if TSX != 0 else 0.0
- Line 393: Division by file_info (could be zero) without check
  - Code: `file_path = repo_root / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0
- Line 717: Division by Transform (could be zero) without check
  - Code: `│   Warehouse     │   │    │  (Fetch/Transform)│`
  - Fix: Add check: (x / Transform) if Transform != 0 else 0.0

**archive\build_backup\scripts\init_safety_logging.py**
- Line 307: Division by allow (could be zero) without check
  - Code: `print("  ├── enforcement/     - Server denial/allow decisions")`
  - Fix: Add check: (x / allow) if allow != 0 else 0.0

**archive\build_backup\scripts\profile_python_entrypoints.py**
- Line 194: Division by PY_ENTRYPOINT_PROFILE (could be zero) without check
  - Code: `parser.add_argument("--output-md", default="E:/analysis_outputs/PY_ENTRYPOINT_PROFILE.md")`
  - Fix: Add check: (x / PY_ENTRYPOINT_PROFILE) if PY_ENTRYPOINT_PROFILE != 0 else 0.0
- Line 195: Division by PY_ENTRYPOINT_PROFILE (could be zero) without check
  - Code: `parser.add_argument("--output-json", default="E:/analysis_outputs/PY_ENTRYPOINT_PROFILE.json")`
  - Fix: Add check: (x / PY_ENTRYPOINT_PROFILE) if PY_ENTRYPOINT_PROFILE != 0 else 0.0
- Line 196: Division by python_entrypoint_blocklist (could be zero) without check
  - Code: `parser.add_argument("--blocklist-out", default="E:/config/python_entrypoint_blocklist.json")`
  - Fix: Add check: (x / python_entrypoint_blocklist) if python_entrypoint_blocklist != 0 else 0.0

**archive\build_backup\scripts\project_path_protector.py**
- Line 126: Division by A (could be zero) without check
  - Code: `f"Destination: {dest_path or 'N/A'}\n\n"`
  - Fix: Add check: (x / A) if A != 0 else 0.0
- Line 194: Division by project_path_protection (could be zero) without check
  - Code: `default='config/project_path_protection.json',`
  - Fix: Add check: (x / project_path_protection) if project_path_protection != 0 else 0.0

**archive\build_backup\scripts\verify_eufle_setup.py**
- Line 42: Division by api (could be zero) without check
  - Code: `response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)`
  - Fix: Add check: (x / api) if api != 0 else 0.0

**archive\build_backup\security\integrate_security.py**
- Line 383: Division by monitor_network (could be zero) without check
  - Code: `# 2. Check blocked requests: python security/monitor_network.py blocked`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0
- Line 384: Division by monitor_network (could be zero) without check
  - Code: `# 3. Whitelist trusted domains: python security/monitor_network.py add <domain>`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0
- Line 385: Division by monitor_network (could be zero) without check
  - Code: `# 4. Monitor continuously: python security/monitor_network.py dashboard`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0

**archive\build_backup\security\monitor_network.py**
- Line 5: Division by allowed (could be zero) without check
  - Code: `Provides CLI interface to view blocked/allowed requests and manage whitelist.`
  - Fix: Add check: (x / allowed) if allowed != 0 else 0.0

**archive\build_backup\security\test_security.py**
- Line 271: Division by monitor_network (could be zero) without check
  - Code: `print("2. Run: python security/monitor_network.py dashboard")`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0

**archive\build_backup\shared\studio_agent_config\functions.py**
- Line 179: Division by completions (could be zero) without check
  - Code: `chat=endpoints.get("chat", "/chat/completions"),`
  - Fix: Add check: (x / completions) if completions != 0 else 0.0
- Line 574: Division by limitations (could be zero) without check
  - Code: `summarized_system_prompt="The Mistral agent assists with pattern recognition, data validation, decision logging, artifact generation, and dynamic capability retrieval within the GRID ecosystem. Key guidelines include: Communication: Be clear, concise, context-aware, user-centric, and avoid unnecessary jargon. Task Execution: Pattern Recognition: Extract relevant entities, relationships, sentiment, and intent from input text. Data Validation: Validate discussion rows against the Great Hall schema; provide clear feedback on issues. Decision Logging: Record decisions accurately with context, traceability, and compliance to Great Hall schema. Artifact Generation: Generate artifacts in specified formats (JSON, markdown, HTML, CSV); validate against relevant schemas. Capability Retrieval: Dynamically retrieve GRID subsystems or tools based on context; warn users of unavailable capabilities. Error Handling: Address unavailable services with fallback responses; mark uncertain outputs and provide recommendations for improving confidence levels. Output Formatting: Maintain consistent formatting, readability, and traceability in outputs. Include provenance information where applicable. Constraints & Compliance: Ensure adherence to schemas, specified constraints, GRID ecosystem policies, and cross-reference linked criteria against session schema. User Interaction: Provide clear feedback, transparency about capabilities/limitations, prompt responsiveness, and inform users about task progress/status.",`
  - Fix: Add check: (x / limitations) if limitations != 0 else 0.0

**archive\build_backup\shared\workspace_utils\eufle_verifier.py**
- Line 57: Division by api (could be zero) without check
  - Code: `response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)`
  - Fix: Add check: (x / api) if api != 0 else 0.0

**archive\build_backup\shared\workspace_utils\repo_analyzer.py**
- Line 149: Division by YAML (could be zero) without check
  - Code: `"""Redact secret values in JSON/YAML content."""`
  - Fix: Add check: (x / YAML) if YAML != 0 else 0.0
- Line 538: Division by file_info (could be zero) without check
  - Code: `path = self.root_path / file_info['path']`
  - Fix: Add check: (x / file_info) if file_info != 0 else 0.0
- Line 658: Division by metrics (could be zero) without check
  - Code: `full_path = self.root_path / metrics.path`
  - Fix: Add check: (x / metrics) if metrics != 0 else 0.0

**archive\build_backup\shared\workspace_utils\tests\test_project_comparator.py**
- Line 122: Division by analysis1 (could be zero) without check
  - Code: `project1_analysis_dir="temp/analysis1",`
  - Fix: Add check: (x / analysis1) if analysis1 != 0 else 0.0

**archive\build_backup\src\guardrails\ci\cicd_integration.py**
- Line 347: Division by workflows (could be zero) without check
  - Code: `"github": ".github/workflows/guardrail.yml",`
  - Fix: Add check: (x / workflows) if workflows != 0 else 0.0

**archive\build_backup\src\guardrails\utils\dashboard.py**
- Line 341: Division by A (could be zero) without check
  - Code: `<p>Trend: {trends.get('trend', 'N/A').upper()}</p>`
  - Fix: Add check: (x / A) if A != 0 else 0.0

**archive\build_backup\src\guardrails\utils\integration_utils.py**
- Line 426: Division by GitLab (could be zero) without check
  - Code: `"""Create a GitHub/GitLab issue template for an issue."""`
  - Fix: Add check: (x / GitLab) if GitLab != 0 else 0.0
- Line 463: Division by path (could be zero) without check
  - Code: `DATA_DIR = Path(os.getenv("YOUR_APP_ROOT", "/default/path")) / "data"`
  - Fix: Add check: (x / path) if path != 0 else 0.0

**archive\build_backup\tests\test_endpoints.py**
- Line 21: Division by cache (could be zero) without check
  - Code: `# May be 200 or 503 depending on database/cache availability`
  - Fix: Add check: (x / cache) if cache != 0 else 0.0
- Line 43: Division by services (could be zero) without check
  - Code: `# Skipping actual request since database/services may not be configured`
  - Fix: Add check: (x / services) if services != 0 else 0.0

**archive\build_backup\wellness_studio\AI SAFETY\CORE_AUTOMATION\engines\run_monitoring.py**
- Line 28: Division by monitoring (could be zero) without check
  - Code: `DEFAULT_CONFIG_PATH = "AI SAFETY - OPENAI/monitoring/monitoring_config.json"`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 191: Division by monitoring (could be zero) without check
  - Code: `outputs, "log_path", "AI SAFETY - OPENAI/monitoring/logs/monitoring.log"`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 199: Division by monitoring (could be zero) without check
  - Code: `"AI SAFETY - OPENAI/monitoring/status/last_run.json",`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 204: Division by monitoring (could be zero) without check
  - Code: `get_str_from_dict(outputs, "diff_path", "AI SAFETY - OPENAI/monitoring/diffs"),`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 209: Division by monitoring (could be zero) without check
  - Code: `outputs, "reports_path", "AI SAFETY - OPENAI/monitoring/reports"`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 215: Division by monitoring (could be zero) without check
  - Code: `outputs, "snapshots_path", "AI SAFETY - OPENAI/monitoring/snapshots"`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0

**archive\build_backup\wellness_studio\AI SAFETY\CORE_AUTOMATION\modules\gap_detection.py**
- Line 95: Division by json (could be zero) without check
  - Code: `headers={'Content-Type': 'application/json'}`
  - Fix: Add check: (x / json) if json != 0 else 0.0

**archive\build_backup\wellness_studio\AI SAFETY\CORE_AUTOMATION\tests\test_innovative_features.py**
- Line 25: Division by a (could be zero) without check
  - Code: `"fetch": {"url": "https://example.com/a"},`
  - Fix: Add check: (x / a) if a != 0 else 0.0
- Line 75: Division by safety (could be zero) without check
  - Code: `{"fetch": {"url": "https://openai.com/safety/"}, "safety_analysis": {"gaps": ["gap-1", "gap-2"], "safety_score": 84}},`
  - Fix: Add check: (x / safety) if safety != 0 else 0.0
- Line 76: Division by safety (could be zero) without check
  - Code: `{"fetch": {"url": "https://openai.com/safety/evaluations/"}, "safety_analysis": {"gaps": ["gap-3"], "safety_score": 92}}`
  - Fix: Add check: (x / safety) if safety != 0 else 0.0
- Line 79: Division by safety (could be zero) without check
  - Code: `{"fetch": {"url": "https://anthropic.com/safety/"}, "safety_analysis": {"gaps": ["gap-1", "gap-2", "gap-3"], "safety_score": 76}}`
  - Fix: Add check: (x / safety) if safety != 0 else 0.0

**archive\build_backup\wellness_studio\AI SAFETY\PROVIDERS\GOOGLE\google_safety_engine.py**
- Line 31: Division by filename (could be zero) without check
  - Code: `path = self.base_path / filename`
  - Fix: Add check: (x / filename) if filename != 0 else 0.0

**archive\build_backup\wellness_studio\AI SAFETY\PROVIDERS\GOOGLE\monitoring\run_monitoring.py**
- Line 27: Division by PROVIDERS (could be zero) without check
  - Code: `DEFAULT_CONFIG_PATH = "AI SAFETY/PROVIDERS/GOOGLE/monitoring/monitoring_config.json"`
  - Fix: Add check: (x / PROVIDERS) if PROVIDERS != 0 else 0.0
- Line 194: Division by PROVIDERS (could be zero) without check
  - Code: `"AI SAFETY/PROVIDERS/GOOGLE/monitoring/logs/monitoring.log",`
  - Fix: Add check: (x / PROVIDERS) if PROVIDERS != 0 else 0.0
- Line 202: Division by PROVIDERS (could be zero) without check
  - Code: `"AI SAFETY/PROVIDERS/GOOGLE/monitoring/status/last_run.json",`
  - Fix: Add check: (x / PROVIDERS) if PROVIDERS != 0 else 0.0
- Line 208: Division by PROVIDERS (could be zero) without check
  - Code: `outputs, "diff_path", "AI SAFETY/PROVIDERS/GOOGLE/monitoring/diffs"`
  - Fix: Add check: (x / PROVIDERS) if PROVIDERS != 0 else 0.0
- Line 214: Division by PROVIDERS (could be zero) without check
  - Code: `outputs, "reports_path", "AI SAFETY/PROVIDERS/GOOGLE/monitoring/reports"`
  - Fix: Add check: (x / PROVIDERS) if PROVIDERS != 0 else 0.0
- Line 220: Division by PROVIDERS (could be zero) without check
  - Code: `outputs, "snapshots_path", "AI SAFETY/PROVIDERS/GOOGLE/monitoring/snapshots"`
  - Fix: Add check: (x / PROVIDERS) if PROVIDERS != 0 else 0.0

**archive\build_backup\wellness_studio\AI SAFETY\PROVIDERS\OPENAI\OPENAI SAFETY\monitoring\run_monitoring.py**
- Line 28: Division by monitoring (could be zero) without check
  - Code: `DEFAULT_CONFIG_PATH = "AI SAFETY - OPENAI/monitoring/monitoring_config.json"`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 191: Division by monitoring (could be zero) without check
  - Code: `outputs, "log_path", "AI SAFETY - OPENAI/monitoring/logs/monitoring.log"`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 199: Division by monitoring (could be zero) without check
  - Code: `"AI SAFETY - OPENAI/monitoring/status/last_run.json",`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 204: Division by monitoring (could be zero) without check
  - Code: `get_str_from_dict(outputs, "diff_path", "AI SAFETY - OPENAI/monitoring/diffs"),`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 209: Division by monitoring (could be zero) without check
  - Code: `outputs, "reports_path", "AI SAFETY - OPENAI/monitoring/reports"`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0
- Line 215: Division by monitoring (could be zero) without check
  - Code: `outputs, "snapshots_path", "AI SAFETY - OPENAI/monitoring/snapshots"`
  - Fix: Add check: (x / monitoring) if monitoring != 0 else 0.0

**archive\build_backup\wellness_studio\src\wellness_studio\__init__.py**
- Line 47: Division by transformers (could be zero) without check
  - Code: `# torch/transformers not available - security modules only`
  - Fix: Add check: (x / transformers) if transformers != 0 else 0.0

**archive\build_backup\wellness_studio\src\wellness_studio\pipeline.py**
- Line 44: Division by Text (could be zero) without check
  - Code: `1. Input Processing (PDF/Text/Audio → Raw Text)`
  - Fix: Add check: (x / Text) if Text != 0 else 0.0

**archive\build_backup\wellness_studio\src\wellness_studio\security\consent_manager.py**
- Line 63: Division by f (could be zero) without check
  - Code: `return self.storage_dir / f"user_{user_id}.json"`
  - Fix: Add check: (x / f) if f != 0 else 0.0

**archive\build_backup\wellness_studio\src\wellness_studio\security\rate_limiter.py**
- Line 302: Division by max (could be zero) without check
  - Code: `'rate': 10 / max(time_span, 0.1)`
  - Fix: Add check: (x / max) if max != 0 else 0.0

**archive\build_backup\wellness_studio\tests\test_input_validation.py**
- Line 94: Division by etc (could be zero) without check
  - Code: `"| cat /etc/passwd",`
  - Fix: Add check: (x / etc) if etc != 0 else 0.0
- Line 113: Division by passwd (could be zero) without check
  - Code: `"../../../etc/passwd",`
  - Fix: Add check: (x / passwd) if passwd != 0 else 0.0

**archive\build_backup\wellness_studio\tests\test_input_validation_guardrails.py**
- Line 81: Division by etc (could be zero) without check
  - Code: `malicious = "file.txt; cat /etc/passwd"`
  - Fix: Add check: (x / etc) if etc != 0 else 0.0
- Line 105: Division by passwd (could be zero) without check
  - Code: `malicious = "../../../etc/passwd"`
  - Fix: Add check: (x / passwd) if passwd != 0 else 0.0
- Line 334: Division by etc (could be zero) without check
  - Code: `malicious = "file.txt; cat /etc/passwd"`
  - Fix: Add check: (x / etc) if etc != 0 else 0.0
- Line 342: Division by passwd (could be zero) without check
  - Code: `malicious = "../../../etc/passwd"`
  - Fix: Add check: (x / passwd) if passwd != 0 else 0.0

### None Check (15 issues)

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\canvas\wheel.py**
- Line 73: Truthy check on Optional target_zone before attribute access
  - Code: `if target_zone and target_zone != self.zone:`
  - Fix: Change to: if target_zone is not None:

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\cognitive\scaffolding_engine.py**
- Line 517: Truthy check on Optional profile before attribute access
  - Code: `if profile and profile.expertise_level.value in ["novice", "beginner"]:`
  - Fix: Change to: if profile is not None:

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\entry_points\cli_entry.py**
- Line 54: Truthy check on Optional user_id before attribute access
  - Code: `if user_id and not self.org_manager.check_user_permission(user_id, command, org_id):`
  - Fix: Change to: if user_id is not None:

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\entry_points\service_entry.py**
- Line 58: Truthy check on Optional user_id before attribute access
  - Code: `if user_id and not self.org_manager.check_user_permission(user_id, action_name, org_id):`
  - Fix: Change to: if user_id is not None:

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\prompts\prompt_store.py**
- Line 114: Truthy check on Optional user_id before attribute access
  - Code: `if user_id and prompt.user_id != user_id:`
  - Fix: Change to: if user_id is not None:
- Line 116: Truthy check on Optional org_id before attribute access
  - Code: `if org_id and prompt.org_id != org_id:`
  - Fix: Change to: if org_id is not None:
- Line 118: Truthy check on Optional source before attribute access
  - Code: `if source and prompt.source != source:`
  - Fix: Change to: if source is not None:

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\discovery_engine.py**
- Line 99: Truthy check on Optional skill_obj before attribute access
  - Code: `if skill_obj and hasattr(skill_obj, "id") and skill_obj.id:`
  - Fix: Change to: if skill_obj is not None:

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\conversation.py**
- Line 192: Truthy check on Optional session_id before attribute access
  - Code: `if session_id and hasattr(self.base_rag_engine, 'conversation_memory'):`
  - Fix: Change to: if session_id is not None:

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\debug_basedpyright.py**
- Line 251: Truthy check on Optional log_file before attribute access
  - Code: `if log_file and log_file.exists():`
  - Fix: Change to: if log_file is not None:

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\debug_basedpyright.py**
- Line 251: Truthy check on Optional log_file before attribute access
  - Code: `if log_file and log_file.exists():`
  - Fix: Change to: if log_file is not None:

**archive\build_backup\Coinbase\coinbase\core\auth.py**
- Line 500: Truthy check on Optional permission before attribute access
  - Code: `if permission and not auth.check_permission(session, permission):`
  - Fix: Change to: if permission is not None:

**archive\build_backup\Coinbase\coinbase\core\backup_manager.py**
- Line 157: Truthy check on Optional db_path before attribute access
  - Code: `if db_path and Path(db_path).exists():`
  - Fix: Change to: if db_path is not None:

**archive\build_backup\scripts\debug_basedpyright.py**
- Line 251: Truthy check on Optional log_file before attribute access
  - Code: `if log_file and log_file.exists():`
  - Fix: Change to: if log_file is not None:

**archive\build_backup\src\guardrails\anomaly\anomaly_detection.py**
- Line 608: Truthy check on Optional threshold before attribute access
  - Code: `if threshold and detector_name in self.thresholds:`
  - Fix: Change to: if threshold is not None:

### Nan Handling (6 issues)

**archive\build_backup\Coinbase\coinbase\integrations\yahoo_finance.py**
- Line 87: float() conversion without NaN check on pandas data
  - Code: `current_price = self._parse_float(row.get("Current Price", "0"))`
  - Fix: Add pd.notna() check before conversion
- Line 88: float() conversion without NaN check on pandas data
  - Code: `purchase_price = self._parse_float(row.get("Purchase Price", "0"))`
  - Fix: Add pd.notna() check before conversion
- Line 89: float() conversion without NaN check on pandas data
  - Code: `quantity = self._parse_float(row.get("Quantity", "0"))`
  - Fix: Add pd.notna() check before conversion
- Line 90: float() conversion without NaN check on pandas data
  - Code: `commission = self._parse_float(row.get("Commission", "0"))`
  - Fix: Add pd.notna() check before conversion
- Line 91: float() conversion without NaN check on pandas data
  - Code: `high_limit = self._parse_float(row.get("High Limit", ""))`
  - Fix: Add pd.notna() check before conversion
- Line 92: float() conversion without NaN check on pandas data
  - Code: `low_limit = self._parse_float(row.get("Low Limit", ""))`
  - Fix: Add pd.notna() check before conversion

### Type Conversion (185 issues)

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\config\__init__.py**
- Line 91: Type conversion of external data without try/except
  - Code: `port=int(env.get("MOTHERSHIP_PORT", "8080")),`
  - Fix: Wrap in try/except or add validation
- Line 92: Type conversion of external data without try/except
  - Code: `workers=int(env.get("MOTHERSHIP_WORKERS", "4")),`
  - Fix: Wrap in try/except or add validation
- Line 190: Type conversion of external data without try/except
  - Code: `pool_size=int(env.get("MOTHERSHIP_DB_POOL_SIZE", "5")),`
  - Fix: Wrap in try/except or add validation
- Line 191: Type conversion of external data without try/except
  - Code: `max_overflow=int(env.get("MOTHERSHIP_DB_MAX_OVERFLOW", "10")),`
  - Fix: Wrap in try/except or add validation
- Line 192: Type conversion of external data without try/except
  - Code: `pool_timeout=int(env.get("MOTHERSHIP_DB_POOL_TIMEOUT", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 226: Type conversion of external data without try/except
  - Code: `access_token_expire_minutes=int(env.get("MOTHERSHIP_ACCESS_TOKEN_EXPIRE", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 227: Type conversion of external data without try/except
  - Code: `refresh_token_expire_days=int(env.get("MOTHERSHIP_REFRESH_TOKEN_EXPIRE", "7")),`
  - Fix: Wrap in try/except or add validation
- Line 232: Type conversion of external data without try/except
  - Code: `rate_limit_requests=int(env.get("MOTHERSHIP_RATE_LIMIT_REQUESTS", "100")),`
  - Fix: Wrap in try/except or add validation
- Line 233: Type conversion of external data without try/except
  - Code: `rate_limit_window_seconds=int(env.get("MOTHERSHIP_RATE_LIMIT_WINDOW", "60")),`
  - Fix: Wrap in try/except or add validation
- Line 414: Type conversion of external data without try/except
  - Code: `gemini_timeout=int(env.get("GEMINI_TIMEOUT", "120")),`
  - Fix: Wrap in try/except or add validation
- Line 417: Type conversion of external data without try/except
  - Code: `grid_timeout=int(env.get("GRID_TIMEOUT", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 420: Type conversion of external data without try/except
  - Code: `webhook_timeout=int(env.get("MOTHERSHIP_WEBHOOK_TIMEOUT", "10")),`
  - Fix: Wrap in try/except or add validation
- Line 421: Type conversion of external data without try/except
  - Code: `webhook_retry_count=int(env.get("MOTHERSHIP_WEBHOOK_RETRY", "3")),`
  - Fix: Wrap in try/except or add validation
- Line 454: Type conversion of external data without try/except
  - Code: `tracing_sample_rate=float(env.get("MOTHERSHIP_TRACING_SAMPLE_RATE", "0.1")),`
  - Fix: Wrap in try/except or add validation
- Line 458: Type conversion of external data without try/except
  - Code: `health_check_interval=int(env.get("MOTHERSHIP_HEALTH_CHECK_INTERVAL", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 511: Type conversion of external data without try/except
  - Code: `default_timeout_seconds=int(env.get("MOTHERSHIP_PAYMENT_TIMEOUT", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 552: Type conversion of external data without try/except
  - Code: `free_tier_relationship_analyses=int(env.get("BILLING_FREE_RELATIONSHIP_ANALYSES", "100")),`
  - Fix: Wrap in try/except or add validation
- Line 553: Type conversion of external data without try/except
  - Code: `free_tier_entity_extractions=int(env.get("BILLING_FREE_ENTITY_EXTRACTIONS", "1000")),`
  - Fix: Wrap in try/except or add validation
- Line 554: Type conversion of external data without try/except
  - Code: `starter_tier_relationship_analyses=int(env.get("BILLING_STARTER_RELATIONSHIP_ANALYSES", "1000")),`
  - Fix: Wrap in try/except or add validation
- Line 555: Type conversion of external data without try/except
  - Code: `starter_tier_entity_extractions=int(env.get("BILLING_STARTER_ENTITY_EXTRACTIONS", "10000")),`
  - Fix: Wrap in try/except or add validation
- Line 556: Type conversion of external data without try/except
  - Code: `pro_tier_relationship_analyses=int(env.get("BILLING_PRO_RELATIONSHIP_ANALYSES", "10000")),`
  - Fix: Wrap in try/except or add validation
- Line 557: Type conversion of external data without try/except
  - Code: `pro_tier_entity_extractions=int(env.get("BILLING_PRO_ENTITY_EXTRACTIONS", "100000")),`
  - Fix: Wrap in try/except or add validation
- Line 558: Type conversion of external data without try/except
  - Code: `starter_monthly_price=int(env.get("BILLING_STARTER_PRICE_CENTS", "4900")),`
  - Fix: Wrap in try/except or add validation
- Line 559: Type conversion of external data without try/except
  - Code: `pro_monthly_price=int(env.get("BILLING_PRO_PRICE_CENTS", "19900")),`
  - Fix: Wrap in try/except or add validation
- Line 560: Type conversion of external data without try/except
  - Code: `relationship_analysis_overage_cents=int(env.get("BILLING_RELATIONSHIP_OVERAGE_CENTS", "5")),`
  - Fix: Wrap in try/except or add validation
- Line 561: Type conversion of external data without try/except
  - Code: `entity_extraction_overage_cents=int(env.get("BILLING_ENTITY_OVERAGE_CENTS", "1")),`
  - Fix: Wrap in try/except or add validation
- Line 562: Type conversion of external data without try/except
  - Code: `billing_cycle_days=int(env.get("BILLING_CYCLE_DAYS", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 599: Type conversion of external data without try/except
  - Code: `session_timeout_minutes=int(env.get("MOTHERSHIP_SESSION_TIMEOUT", "60")),`
  - Fix: Wrap in try/except or add validation
- Line 600: Type conversion of external data without try/except
  - Code: `max_concurrent_sessions=int(env.get("MOTHERSHIP_MAX_SESSIONS", "100")),`
  - Fix: Wrap in try/except or add validation
- Line 601: Type conversion of external data without try/except
  - Code: `task_queue_size=int(env.get("MOTHERSHIP_TASK_QUEUE_SIZE", "1000")),`
  - Fix: Wrap in try/except or add validation
- Line 602: Type conversion of external data without try/except
  - Code: `task_timeout_seconds=int(env.get("MOTHERSHIP_TASK_TIMEOUT", "300")),`
  - Fix: Wrap in try/except or add validation
- Line 603: Type conversion of external data without try/except
  - Code: `task_retry_limit=int(env.get("MOTHERSHIP_TASK_RETRY_LIMIT", "3")),`
  - Fix: Wrap in try/except or add validation
- Line 605: Type conversion of external data without try/except
  - Code: `websocket_heartbeat_interval=int(env.get("MOTHERSHIP_WS_HEARTBEAT", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 606: Type conversion of external data without try/except
  - Code: `websocket_max_connections=int(env.get("MOTHERSHIP_WS_MAX_CONNECTIONS", "500")),`
  - Fix: Wrap in try/except or add validation
- Line 607: Type conversion of external data without try/except
  - Code: `dashboard_refresh_rate=int(env.get("MOTHERSHIP_DASHBOARD_REFRESH", "5")),`
  - Fix: Wrap in try/except or add validation
- Line 608: Type conversion of external data without try/except
  - Code: `dashboard_history_hours=int(env.get("MOTHERSHIP_DASHBOARD_HISTORY", "24")),`
  - Fix: Wrap in try/except or add validation
- Line 610: Type conversion of external data without try/except
  - Code: `autoscale_min_workers=int(env.get("MOTHERSHIP_AUTOSCALE_MIN", "1")),`
  - Fix: Wrap in try/except or add validation
- Line 611: Type conversion of external data without try/except
  - Code: `autoscale_max_workers=int(env.get("MOTHERSHIP_AUTOSCALE_MAX", "10")),`
  - Fix: Wrap in try/except or add validation
- Line 612: Type conversion of external data without try/except
  - Code: `autoscale_cpu_threshold=float(env.get("MOTHERSHIP_AUTOSCALE_CPU_THRESHOLD", "0.8")),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\config\inference_abrasiveness.py**
- Line 300: Type conversion of external data without try/except
  - Code: `confidence_threshold=float(env.get("INFERENCE_CONFIDENCE_THRESHOLD", "0.7")),`
  - Fix: Wrap in try/except or add validation
- Line 301: Type conversion of external data without try/except
  - Code: `resource_utilization_threshold=float(env.get("INFERENCE_RESOURCE_THRESHOLD", "0.8")),`
  - Fix: Wrap in try/except or add validation
- Line 302: Type conversion of external data without try/except
  - Code: `inference_failure_threshold=int(env.get("INFERENCE_FAILURE_THRESHOLD", "5")),`
  - Fix: Wrap in try/except or add validation
- Line 303: Type conversion of external data without try/except
  - Code: `temporal_decay_threshold=float(env.get("INFERENCE_TEMPORAL_DECAY_THRESHOLD", "0.5")),`
  - Fix: Wrap in try/except or add validation
- Line 304: Type conversion of external data without try/except
  - Code: `pattern_deviation_threshold=float(env.get("INFERENCE_PATTERN_DEVIATION_THRESHOLD", "0.3")),`
  - Fix: Wrap in try/except or add validation
- Line 312: Type conversion of external data without try/except
  - Code: `temporary_files_cleanup_threshold=int(env.get("INFERENCE_CLEANUP_TEMP_THRESHOLD", "7")),`
  - Fix: Wrap in try/except or add validation
- Line 313: Type conversion of external data without try/except
  - Code: `stale_results_cleanup_threshold=int(env.get("INFERENCE_CLEANUP_STALE_THRESHOLD", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 314: Type conversion of external data without try/except
  - Code: `cache_cleanup_threshold=int(env.get("INFERENCE_CLEANUP_CACHE_THRESHOLD", "90")),`
  - Fix: Wrap in try/except or add validation
- Line 315: Type conversion of external data without try/except
  - Code: `cloud_content_dehydration_threshold=float(env.get("INFERENCE_CLOUD_DEHYDRATION_THRESHOLD", "0.5")),`
  - Fix: Wrap in try/except or add validation
- Line 316: Type conversion of external data without try/except
  - Code: `downloads_cleanup_threshold=int(env.get("INFERENCE_DOWNLOADS_CLEANUP_THRESHOLD", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 317: Type conversion of external data without try/except
  - Code: `recycle_bin_cleanup_threshold=int(env.get("INFERENCE_RECYCLE_BIN_CLEANUP_THRESHOLD", "14")),`
  - Fix: Wrap in try/except or add validation
- Line 335: Type conversion of external data without try/except
  - Code: `reference_threshold_adjustment = float(env.get("INFERENCE_REFERENCE_THRESHOLD_ADJUSTMENT", "0.1"))`
  - Fix: Wrap in try/except or add validation
- Line 336: Type conversion of external data without try/except
  - Code: `reference_confidence_boost = float(env.get("INFERENCE_REFERENCE_CONFIDENCE_BOOST", "0.05"))`
  - Fix: Wrap in try/except or add validation
- Line 343: Type conversion of external data without try/except
  - Code: `confidence_adjustment_factor = float(env.get("INFERENCE_CONFIDENCE_ADJUSTMENT_FACTOR", "1.0"))`
  - Fix: Wrap in try/except or add validation
- Line 344: Type conversion of external data without try/except
  - Code: `temporal_decay_rate = float(env.get("INFERENCE_TEMPORAL_DECAY_RATE", "0.95"))`
  - Fix: Wrap in try/except or add validation
- Line 345: Type conversion of external data without try/except
  - Code: `pattern_adherence_weight = float(env.get("INFERENCE_PATTERN_ADHERENCE_WEIGHT", "0.7"))`
  - Fix: Wrap in try/except or add validation
- Line 346: Type conversion of external data without try/except
  - Code: `deviation_tolerance = float(env.get("INFERENCE_DEVIATION_TOLERANCE", "0.15"))`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\exceptions.py**
- Line 206: Type conversion of external data without try/except
  - Code: `details["value"] = str(value)[:100]  # Truncate for safety`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\middleware\__init__.py**
- Line 155: Type conversion of external data without try/except
  - Code: `"query": str(request.url.query) if request.url.query else None,`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\middleware\security_enforcer.py**
- Line 454: Type conversion of external data without try/except
  - Code: `if self._is_public_endpoint(request.url.path):`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\repositories\db_repos.py**
- Line 210: Type conversion of external data without try/except
  - Code: `usage[endpoint_type] = usage.get(endpoint_type, 0) + int(row.cost_units)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\routers\navigation_simple.py**
- Line 72: Type conversion of external data without try/except
  - Code: `return str(request_context.request_id)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\security\api_sentinels.py**
- Line 261: Type conversion of external data without try/except
  - Code: `original_value=str(value),`
  - Fix: Wrap in try/except or add validation
- Line 262: Type conversion of external data without try/except
  - Code: `sanitized_value=str(value),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\mothership\utils\cache.py**
- Line 91: Type conversion of external data without try/except
  - Code: `cache_key = f"{func.__name__}:{key}:" + str(args) + str(kwargs)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\resonance\api\router.py**
- Line 577: Type conversion of external data without try/except
  - Code: `{"text": summary_text, "max_chars": int(request.max_chars), "use_llm": bool(request.use_llm)}`
  - Fix: Wrap in try/except or add validation
- Line 739: Type conversion of external data without try/except
  - Code: `progress=float(request.progress),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\application\resonance\api\websocket.py**
- Line 154: Type conversion of external data without try/except
  - Code: `else str(envelope_metrics.phase)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\__main__.py**
- Line 132: Type conversion of external data without try/except
  - Code: `return str(args.text)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\interfaces\config.py**
- Line 67: Type conversion of external data without try/except
  - Code: `default_time_window_days=int(env.get("INTERFACES_METRICS_TIME_WINDOW_DAYS", "7")),`
  - Fix: Wrap in try/except or add validation
- Line 68: Type conversion of external data without try/except
  - Code: `trace_limit=int(env.get("INTERFACES_METRICS_TRACE_LIMIT", "1000")),`
  - Fix: Wrap in try/except or add validation
- Line 69: Type conversion of external data without try/except
  - Code: `batch_size=int(env.get("INTERFACES_METRICS_BATCH_SIZE", "100")),`
  - Fix: Wrap in try/except or add validation
- Line 77: Type conversion of external data without try/except
  - Code: `prototype_port=int(env.get("INTERFACES_PROTOTYPE_PORT", "8080")),`
  - Fix: Wrap in try/except or add validation
- Line 79: Type conversion of external data without try/except
  - Code: `refresh_interval_seconds=int(env.get("INTERFACES_DASHBOARD_REFRESH_SECONDS", "30")),`
  - Fix: Wrap in try/except or add validation
- Line 80: Type conversion of external data without try/except
  - Code: `default_chart_hours=int(env.get("INTERFACES_DASHBOARD_CHART_HOURS", "24")),`
  - Fix: Wrap in try/except or add validation
- Line 82: Type conversion of external data without try/except
  - Code: `json_scan_days=int(env.get("INTERFACES_JSON_SCAN_DAYS", "7")),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\interfaces\json_parser.py**
- Line 380: Type conversion of external data without try/except
  - Code: `latency = float(data[key])`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\interfaces\metrics_collector.py**
- Line 323: Type conversion of external data without try/except
  - Code: `modality = str(input_data.get("modality", "text"))`
  - Fix: Wrap in try/except or add validation
- Line 347: Type conversion of external data without try/except
  - Code: `raw_size = len(str(input_data))`
  - Fix: Wrap in try/except or add validation
- Line 352: Type conversion of external data without try/except
  - Code: `source = str(input_data.get("source", "unknown"))`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\interfaces\sensory.py**
- Line 42: Type conversion of external data without try/except
  - Code: `"coherence": float(data.get("clarity", 0.5)),`
  - Fix: Wrap in try/except or add validation
- Line 56: Type conversion of external data without try/except
  - Code: `"coherence": float(data.get("clarity", 0.5)),`
  - Fix: Wrap in try/except or add validation
- Line 65: Type conversion of external data without try/except
  - Code: `"coherence": float(data.get("confidence", 0.5)),`
  - Fix: Wrap in try/except or add validation
- Line 81: Type conversion of external data without try/except
  - Code: `"coherence": float(data.get("confidence", 0.8)),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\io\outputs.py**
- Line 258: Type conversion of external data without try/except
  - Code: `value_str = str(value)[:value_width]`
  - Fix: Wrap in try/except or add validation
- Line 384: Type conversion of external data without try/except
  - Code: `value_str = str(value).replace(",", ";").replace('"', '""')`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\patterns\hybrid_detection.py**
- Line 101: Type conversion of external data without try/except
  - Code: `metrics[key] = float(value)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\quantum\quantizer.py**
- Line 78: Type conversion of external data without try/except
  - Code: `quantized[key] = self.quantize_value(float(value), level)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\secrets\__main__.py**
- Line 98: Type conversion of external data without try/except
  - Code: `print(value)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\input_sanitizer.py**
- Line 387: Type conversion of external data without try/except
  - Code: `original_length=len(str(data)),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\local_secrets_manager.py**
- Line 397: Type conversion of external data without try/except
  - Code: `print(value)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\secrets.py**
- Line 89: Type conversion of external data without try/except
  - Code: `version=str(data.get("data", {}).get("metadata", {}).get("version", "")),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\security\threat_detector.py**
- Line 624: Type conversion of external data without try/except
  - Code: `return str(data)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\analysis_process_context.py**
- Line 77: Type conversion of external data without try/except
  - Code: `max_entities = int(args.get("max_entities", 50) or 50)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\compress_articulate.py**
- Line 19: Type conversion of external data without try/except
  - Code: `max_chars = int(args.get("max_chars", 280) or 280)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\compress_secure.py**
- Line 36: Type conversion of external data without try/except
  - Code: `max_chars = int(args.get("max_chars", 280) or 280)`
  - Fix: Wrap in try/except or add validation
- Line 37: Type conversion of external data without try/except
  - Code: `security_level = float(args.get("security_level", 0.5) or 0.5)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\cross_reference_explain.py**
- Line 10: Type conversion of external data without try/except
  - Code: `concept = str(args.get("concept") or "").strip()`
  - Fix: Wrap in try/except or add validation
- Line 11: Type conversion of external data without try/except
  - Code: `source_domain = str(args.get("source_domain") or args.get("sourceDomain") or "").strip()`
  - Fix: Wrap in try/except or add validation
- Line 12: Type conversion of external data without try/except
  - Code: `target_domain = str(args.get("target_domain") or args.get("targetDomain") or "").strip()`
  - Fix: Wrap in try/except or add validation
- Line 13: Type conversion of external data without try/except
  - Code: `style = str(args.get("style") or "plain").strip()`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\extraction_engine.py**
- Line 206: Type conversion of external data without try/except
  - Code: `type_name = getattr(param_type, "__name__", str(param_type))`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\rag_query_knowledge.py**
- Line 55: Type conversion of external data without try/except
  - Code: `top_k = int(args.get("top_k", 5) or 5)`
  - Fix: Wrap in try/except or add validation
- Line 56: Type conversion of external data without try/except
  - Code: `temperature = float(args.get("temperature", 0.7) or 0.7)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\topic_extractor.py**
- Line 22: Type conversion of external data without try/except
  - Code: `max_topics = int(args.get("max_topics", 8))`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\transform_schema_map.py**
- Line 695: Type conversion of external data without try/except
  - Code: `target_schema = str(args.get("target_schema") or args.get("targetSchema") or "default")`
  - Fix: Wrap in try/except or add validation
- Line 696: Type conversion of external data without try/except
  - Code: `output_format = str(args.get("output_format") or args.get("outputFormat") or "json").lower()`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\skills\youtube_transcript_analyze.py**
- Line 74: Type conversion of external data without try/except
  - Code: `top_n = int(args.get("top_n", 15) or 15)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\grid\version_3_5.py**
- Line 133: Type conversion of external data without try/except
  - Code: `confidence = float(data.get("confidence", 0.7))`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\chat.py**
- Line 554: Type conversion of external data without try/except
  - Code: `config.top_k = int(arg)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\tools\rag\vector_store\databricks_store.py**
- Line 504: Type conversion of external data without try/except
  - Code: `"distance": float(row[6]),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\demo.py**
- Line 213: Type conversion of external data without try/except
  - Code: `bar = "▓" * int(value * 20) + "░" * (20 - int(value * 20))`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\interfaces\grid_bridge.py**
- Line 368: Type conversion of external data without try/except
  - Code: `return str(value)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\security\input_validator.py**
- Line 595: Type conversion of external data without try/except
  - Code: `result.sanitized_value = self.sanitize_string(str(value))`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\src\vection\security\rate_limiter.py**
- Line 538: Type conversion of external data without try/except
  - Code: `session_id = str(args[0])`
  - Fix: Wrap in try/except or add validation
- Line 550: Type conversion of external data without try/except
  - Code: `session_id = str(args[0])`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_security_governance.py**
- Line 776: Type conversion of external data without try/except
  - Code: `async def test_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 981: Type conversion of external data without try/except
  - Code: `async def navigation_plan_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 988: Type conversion of external data without try/except
  - Code: `async def navigation_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1190: Type conversion of external data without try/except
  - Code: `async def test_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\tests\test_streaming_security.py**
- Line 138: Type conversion of external data without try/except
  - Code: `async def navigation_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 261: Type conversion of external data without try/except
  - Code: `async def failing_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 290: Type conversion of external data without try/except
  - Code: `async def slow_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 457: Type conversion of external data without try/except
  - Code: `async def navigation_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 523: Type conversion of external data without try/except
  - Code: `async def failing_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 558: Type conversion of external data without try/except
  - Code: `async def slow_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 603: Type conversion of external data without try/except
  - Code: `async def error_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 626: Type conversion of external data without try/except
  - Code: `async def degrading_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 762: Type conversion of external data without try/except
  - Code: `async def concurrent_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1075: Type conversion of external data without try/except
  - Code: `async def slow_consumer_test_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1101: Type conversion of external data without try/except
  - Code: `async def large_event_test_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1128: Type conversion of external data without try/except
  - Code: `async def high_freq_test_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1153: Type conversion of external data without try/except
  - Code: `async def malformed_test_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1182: Type conversion of external data without try/except
  - Code: `async def special_char_test_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1271: Type conversion of external data without try/except
  - Code: `async def secure_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1359: Type conversion of external data without try/except
  - Code: `async def failing_secure_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1519: Type conversion of external data without try/except
  - Code: `async def e2e_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1602: Type conversion of external data without try/except
  - Code: `async def e2e_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1707: Type conversion of external data without try/except
  - Code: `async def test_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation
- Line 1734: Type conversion of external data without try/except
  - Code: `async def secure_stream_endpoint(data: dict):`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\mcp\servers\memory\production_server.py**
- Line 197: Type conversion of external data without try/except
  - Code: `"size": len(str(value)),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\mcp\servers\memory\server.py**
- Line 163: Type conversion of external data without try/except
  - Code: `"size": len(str(value)),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\servers\memory\production_server.py**
- Line 197: Type conversion of external data without try/except
  - Code: `"size": len(str(value)),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\grid-rag-enhanced\workspace\servers\memory\server.py**
- Line 163: Type conversion of external data without try/except
  - Code: `"size": len(str(value)),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\scripts\apply_denylist_drive_wide.py**
- Line 72: Type conversion of external data without try/except
  - Code: `'path': str(config_path),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\security\network_interceptor.py**
- Line 180: Type conversion of external data without try/except
  - Code: `data_str = str(data)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-01T20-18-14\shared\workspace_utils\logging_config.py**
- Line 60: Type conversion of external data without try/except
  - Code: `'workspace_root': str(config.get_workspace_root()),`
  - Fix: Wrap in try/except or add validation
- Line 61: Type conversion of external data without try/except
  - Code: `'output_dir': str(config.get_output_dir()),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\apply_denylist_drive_wide.py**
- Line 70: Type conversion of external data without try/except
  - Code: `"path": str(config_path),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\scripts\server_denylist_manager.py**
- Line 137: Type conversion of external data without try/except
  - Code: `return [str(value)]`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\security\network_interceptor.py**
- Line 180: Type conversion of external data without try/except
  - Code: `data_str = str(data)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\.worktrees\copilot-worktree-2026-02-07T01-40-39\shared\workspace_utils\logging_config.py**
- Line 60: Type conversion of external data without try/except
  - Code: `'workspace_root': str(config.get_workspace_root()),`
  - Fix: Wrap in try/except or add validation
- Line 61: Type conversion of external data without try/except
  - Code: `'output_dir': str(config.get_output_dir()),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\Coinbase\coinbase\features\fact_check.py**
- Line 248: Type conversion of external data without try/except
  - Code: `price = float(data.get("price", 0))`
  - Fix: Wrap in try/except or add validation
- Line 256: Type conversion of external data without try/except
  - Code: `price = float(data.get("data", {}).get("amount", 0))`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\Coinbase\coinbase\ingestion\data_ingestion.py**
- Line 170: Type conversion of external data without try/except
  - Code: `symbol = str(row.get("Symbol", "")).strip()`
  - Fix: Wrap in try/except or add validation
- Line 211: Type conversion of external data without try/except
  - Code: `high_limit = float(row.get("High Limit", 0.0)) if pd.notna(row.get("High Limit")) else None`
  - Fix: Wrap in try/except or add validation
- Line 212: Type conversion of external data without try/except
  - Code: `low_limit = float(row.get("Low Limit", 0.0)) if pd.notna(row.get("Low Limit")) else None`
  - Fix: Wrap in try/except or add validation
- Line 213: Type conversion of external data without try/except
  - Code: `comment = str(row.get("Comment", "")).strip() if pd.notna(row.get("Comment")) else None`
  - Fix: Wrap in try/except or add validation
- Line 215: Type conversion of external data without try/except
  - Code: `str(row.get("Transaction Type", "")).strip()`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\Coinbase\coinbase\integrations\yahoo_finance.py**
- Line 87: Type conversion of external data without try/except
  - Code: `current_price = self._parse_float(row.get("Current Price", "0"))`
  - Fix: Wrap in try/except or add validation
- Line 88: Type conversion of external data without try/except
  - Code: `purchase_price = self._parse_float(row.get("Purchase Price", "0"))`
  - Fix: Wrap in try/except or add validation
- Line 89: Type conversion of external data without try/except
  - Code: `quantity = self._parse_float(row.get("Quantity", "0"))`
  - Fix: Wrap in try/except or add validation
- Line 90: Type conversion of external data without try/except
  - Code: `commission = self._parse_float(row.get("Commission", "0"))`
  - Fix: Wrap in try/except or add validation
- Line 91: Type conversion of external data without try/except
  - Code: `high_limit = self._parse_float(row.get("High Limit", ""))`
  - Fix: Wrap in try/except or add validation
- Line 92: Type conversion of external data without try/except
  - Code: `low_limit = self._parse_float(row.get("Low Limit", ""))`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\Coinbase\coinbase\logging_config.py**
- Line 207: Type conversion of external data without try/except
  - Code: `mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\Coinbase\coinbase\security\portfolio_data_policy.py**
- Line 288: Type conversion of external data without try/except
  - Code: `return str(value).upper() if value else None`
  - Fix: Wrap in try/except or add validation
- Line 302: Type conversion of external data without try/except
  - Code: `return round(float(value), 2) if value else 0.0`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\Coinbase\coinbase\verification\verification_scale.py**
- Line 201: Type conversion of external data without try/except
  - Code: `price = float(data.get("price", 0)) if data else 0`
  - Fix: Wrap in try/except or add validation
- Line 206: Type conversion of external data without try/except
  - Code: `price = float(data.get("data", {}).get("amount", 0)) if data else 0`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\Coinbase\tests\test_portfolio_safety_mcp_integration.py**
- Line 103: Type conversion of external data without try/except
  - Code: `assert "quantity" not in str(data)`
  - Fix: Wrap in try/except or add validation
- Line 104: Type conversion of external data without try/except
  - Code: `assert "purchase_price" not in str(data)`
  - Fix: Wrap in try/except or add validation
- Line 121: Type conversion of external data without try/except
  - Code: `assert "quantity" not in str(data)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\scripts\apply_denylist_drive_wide.py**
- Line 70: Type conversion of external data without try/except
  - Code: `"path": str(config_path),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\scripts\server_denylist_manager.py**
- Line 137: Type conversion of external data without try/except
  - Code: `return [str(value)]`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\security\network_interceptor.py**
- Line 180: Type conversion of external data without try/except
  - Code: `data_str = str(data)`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\shared\workspace_utils\logging_config.py**
- Line 60: Type conversion of external data without try/except
  - Code: `'workspace_root': str(config.get_workspace_root()),`
  - Fix: Wrap in try/except or add validation
- Line 61: Type conversion of external data without try/except
  - Code: `'output_dir': str(config.get_output_dir()),`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\wellness_studio\AI SAFETY\CORE_AUTOMATION\engines\run_monitoring.py**
- Line 171: Type conversion of external data without try/except
  - Code: `def get_list_str(data: JsonDict, key: str) -> list[str]:`
  - Fix: Wrap in try/except or add validation
- Line 180: Type conversion of external data without try/except
  - Code: `return str(value) if isinstance(value, str) else default`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\wellness_studio\AI SAFETY\PROVIDERS\GOOGLE\monitoring\run_monitoring.py**
- Line 172: Type conversion of external data without try/except
  - Code: `def get_list_str(data: JsonDict, key: str) -> list[str]:`
  - Fix: Wrap in try/except or add validation
- Line 181: Type conversion of external data without try/except
  - Code: `return str(value) if isinstance(value, str) else default`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\wellness_studio\AI SAFETY\PROVIDERS\OPENAI\OPENAI SAFETY\monitoring\run_monitoring.py**
- Line 171: Type conversion of external data without try/except
  - Code: `def get_list_str(data: JsonDict, key: str) -> list[str]:`
  - Fix: Wrap in try/except or add validation
- Line 180: Type conversion of external data without try/except
  - Code: `return str(value) if isinstance(value, str) else default`
  - Fix: Wrap in try/except or add validation

**archive\build_backup\wellness_studio\ai_safety\monitoring\spawn_monitor.py**
- Line 574: Type conversion of external data without try/except
  - Code: `config_key = str(config_path)`
  - Fix: Wrap in try/except or add validation
