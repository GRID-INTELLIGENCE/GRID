# Runtime Bug Scan Report
**Generated:** 2026-02-12 22:55:43
**Total Issues Found:** 47

## Summary by Pattern Type

### Division By Zero (42 issues)

**boundaries\examples\preparedness_overwatch_demo.py**
- Line 51: Division by boundaries (could be zero) without check
  - Code: `log_dir = config.get("overwatch", {}).get("logDir", "logs/boundaries")`
  - Fix: Add check: (x / boundaries) if boundaries != 0 else 0.0

**boundaries\logger_ws.py**
- Line 250: Division by boundaries (could be zero) without check
  - Code: `log_dir=os.environ.get("BOUNDARY_LOG_DIR", "logs/boundaries"),`
  - Fix: Add check: (x / boundaries) if boundaries != 0 else 0.0

**boundaries\overwatch.py**
- Line 30: Division by boundaries (could be zero) without check
  - Code: `self.log_dir = Path(ow.get("logDir", "logs/boundaries"))`
  - Fix: Add check: (x / boundaries) if boundaries != 0 else 0.0
- Line 89: Division by f (could be zero) without check
  - Code: `path = self._alerts_dir / f"alert_{event.get('eventId', '')}.json"`
  - Fix: Add check: (x / f) if f != 0 else 0.0
- Line 124: Division by f (could be zero) without check
  - Code: `path = self._alerts_dir / f"escalation_{event_type}_{ts}.json"`
  - Fix: Add check: (x / f) if f != 0 else 0.0

**safety\api\main.py**
- Line 5: Division by infer (could be zero) without check
  - Code: `- POST /infer         — Submit an inference request (enqueued, not direct).`
  - Fix: Add check: (x / infer) if infer != 0 else 0.0
- Line 6: Division by review (could be zero) without check
  - Code: `- POST /review        — Human reviewer approve/block an escalation.`
  - Fix: Add check: (x / review) if review != 0 else 0.0
- Line 7: Division by health (could be zero) without check
  - Code: `- GET  /health        — Health check (bypasses middleware).`
  - Fix: Add check: (x / health) if health != 0 else 0.0
- Line 8: Division by metrics (could be zero) without check
  - Code: `- GET  /metrics       — Prometheus metrics (bypasses middleware).`
  - Fix: Add check: (x / metrics) if metrics != 0 else 0.0
- Line 9: Division by status (could be zero) without check
  - Code: `- GET  /status/{id}   — Check status of a queued request.`
  - Fix: Add check: (x / status) if status != 0 else 0.0
- Line 194: Division by Response (could be zero) without check
  - Code: `# Request / Response models`
  - Fix: Add check: (x / Response) if Response != 0 else 0.0
- Line 397: Division by depth (could be zero) without check
  - Code: `@app.get("/queue/depth")`
  - Fix: Add check: (x / depth) if depth != 0 else 0.0

**safety\api\middleware.py**
- Line 111: Division by docs (could be zero) without check
  - Code: `# Skip for health/docs endpoints`
  - Fix: Add check: (x / docs) if docs != 0 else 0.0
- Line 118: Division by infer (could be zero) without check
  - Code: `# Only enforce on POST requests to /infer and /v1/ endpoints`
  - Fix: Add check: (x / infer) if infer != 0 else 0.0

**safety\api\security_headers.py**
- Line 171: Division by plain (could be zero) without check
  - Code: `return Response(content="CORS policy violation", status_code=403, media_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0
- Line 178: Division by plain (could be zero) without check
  - Code: `return Response(content="CSRF token validation failed", status_code=403, media_type="text/plain")`
  - Fix: Add check: (x / plain) if plain != 0 else 0.0

**safety\audit\models.py**
- Line 129: Division by output (could be zero) without check
  - Code: `"""Automatically redact PII from input/output fields before DB insert."""`
  - Fix: Add check: (x / output) if output != 0 else 0.0

**safety\detectors\ml_detector.py**
- Line 46: Division by models (could be zero) without check
  - Code: `_CLASSIFIER_PATH = os.getenv("SAFETY_CLASSIFIER_PATH", "safety/models/safety_classifier.joblib")`
  - Fix: Add check: (x / models) if models != 0 else 0.0

**safety\detectors\pre_check.py**
- Line 101: Division by length (could be zero) without check
  - Code: `return -sum((count / length) * math.log2(count / length) for count in freq.values())`
  - Fix: Add check: (x / length) if length != 0 else 0.0

**safety\detectors\pre_check_guardian.py**
- Line 55: Division by length (could be zero) without check
  - Code: `return -sum((count / length) * math.log2(count / length) for count in freq.values())`
  - Fix: Add check: (x / length) if length != 0 else 0.0
- Line 161: Division by encoded (could be zero) without check
  - Code: `# 3. Entropy heuristic (detect obfuscated / encoded payloads)`
  - Fix: Add check: (x / encoded) if encoded != 0 else 0.0

**safety\escalation\handler.py**
- Line 6: Division by PagerDuty (could be zero) without check
  - Code: `- Notify human reviewers via Slack / PagerDuty.`
  - Fix: Add check: (x / PagerDuty) if PagerDuty != 0 else 0.0
- Line 8: Division by block (could be zero) without check
  - Code: `- Provide approve/block API for human reviewers.`
  - Fix: Add check: (x / block) if block != 0 else 0.0

**safety\escalation\notifier.py**
- Line 164: Division by v2 (could be zero) without check
  - Code: `resp = await client.post("https://events.pagerduty.com/v2/enqueue", json=payload)`
  - Fix: Add check: (x / v2) if v2 != 0 else 0.0

**safety\guardian\loader.py**
- Line 53: Division by rules (could be zero) without check
  - Code: `self.rules_dir = Path(rules_dir or os.getenv("GUARDIAN_RULES_DIR", "config/rules"))`
  - Fix: Add check: (x / rules) if rules != 0 else 0.0
- Line 218: Division by explosives (could be zero) without check
  - Code: `# Weapons / explosives`
  - Fix: Add check: (x / explosives) if explosives != 0 else 0.0

**safety\model\client.py**
- Line 31: Division by v1 (could be zero) without check
  - Code: `_MODEL_API_URL = os.getenv("MODEL_API_URL", "http://localhost:8080/v1/completions")`
  - Fix: Add check: (x / v1) if v1 != 0 else 0.0
- Line 43: Division by json (could be zero) without check
  - Code: `headers: dict[str, str] = {"Content-Type": "application/json"}`
  - Fix: Add check: (x / json) if json != 0 else 0.0

**safety\observability\logging_setup.py**
- Line 111: Division by logs (could be zero) without check
  - Code: `log_dir = os.getenv("SAFETY_LOG_DIR", "safety/logs")`
  - Fix: Add check: (x / logs) if logs != 0 else 0.0

**safety\observability\security_monitoring.py**
- Line 130: Division by O (could be zero) without check
  - Code: `"""Background thread to handle blocking file I/O."""`
  - Fix: Add check: (x / O) if O != 0 else 0.0
- Line 276: Division by f (could be zero) without check
  - Code: `log_file = self.log_dir / f"security_{date_str}.jsonl"`
  - Fix: Add check: (x / f) if f != 0 else 0.0
- Line 548: Division by max (could be zero) without check
  - Code: `normalized_risk = risk_score / max(total_events, 1)`
  - Fix: Add check: (x / max) if max != 0 else 0.0

**safety\scripts\load_blocklist.py**
- Line 26: Division by config (could be zero) without check
  - Code: `default="safety/config/blocklist.txt",`
  - Fix: Add check: (x / config) if config != 0 else 0.0

**safety\tests\integration\test_middleware_pipeline.py**
- Line 51: Division by depth (could be zero) without check
  - Code: `resp = client.get("/queue/depth")`
  - Fix: Add check: (x / depth) if depth != 0 else 0.0

**safety\tests\unit\test_pre_check.py**
- Line 43: Division by explosives (could be zero) without check
  - Code: `# Weapons / explosives`
  - Fix: Add check: (x / explosives) if explosives != 0 else 0.0

**security\assessment_agent.py**
- Line 156: Division by SSRF (could be zero) without check
  - Code: `"""Test network/SSRF access to URLs."""`
  - Fix: Add check: (x / SSRF) if SSRF != 0 else 0.0

**security\integrate_security.py**
- Line 366: Division by monitor_network (could be zero) without check
  - Code: `# 2. Check blocked requests: python security/monitor_network.py blocked`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0
- Line 367: Division by monitor_network (could be zero) without check
  - Code: `# 3. Whitelist trusted domains: python security/monitor_network.py add <domain>`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0
- Line 368: Division by monitor_network (could be zero) without check
  - Code: `# 4. Monitor continuously: python security/monitor_network.py dashboard`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0

**security\monitor_network.py**
- Line 5: Division by allowed (could be zero) without check
  - Code: `Provides CLI interface to view blocked/allowed requests and manage whitelist.`
  - Fix: Add check: (x / allowed) if allowed != 0 else 0.0

**security\test_security.py**
- Line 271: Division by monitor_network (could be zero) without check
  - Code: `print("2. Run: python security/monitor_network.py dashboard")`
  - Fix: Add check: (x / monitor_network) if monitor_network != 0 else 0.0

**src\tools\forensics\analyze_logs.py**
- Line 35: Division by forensic_log_analyzer (could be zero) without check
  - Code: `print("Check the definition in security/forensic_log_analyzer.py.")`
  - Fix: Add check: (x / forensic_log_analyzer) if forensic_log_analyzer != 0 else 0.0

### Type Conversion (5 issues)

**safety\guardian\loader.py**
- Line 202: Type conversion of external data without try/except
  - Code: `confidence=float(data.get("confidence", 0.8)),`
  - Fix: Wrap in try/except or add validation
- Line 205: Type conversion of external data without try/except
  - Code: `priority=int(data.get("priority", 100)),`
  - Fix: Wrap in try/except or add validation
- Line 212: Type conversion of external data without try/except
  - Code: `max_matches=int(data.get("max_matches", 10)),`
  - Fix: Wrap in try/except or add validation

**safety\rules\manager.py**
- Line 258: Type conversion of external data without try/except
  - Code: `flattened_text = json.dumps(data) if isinstance(data, (dict, list)) else str(data)`
  - Fix: Wrap in try/except or add validation

**security\network_interceptor.py**
- Line 170: Type conversion of external data without try/except
  - Code: `data_str = str(data)`
  - Fix: Wrap in try/except or add validation
