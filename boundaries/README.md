# Boundaries Module

Schema and runtime for **boundaries**, **consent**, and **guardrails** with the **right to refuse service at any instance** and **WebSocket-persistent logging**.

## Quick start

```python
from boundaries import BoundaryEngine, refuse_service, get_logger

# Refuse service at any time (no reason required when configured)
record = refuse_service(scope="request", trigger="optional_action_id")

# Enforce boundaries/consent/guardrails (honours refusals)
engine = BoundaryEngine(config)
allowed = engine.check_boundary("boundary_id", "subject")
has_consent = engine.require_consent("consent_id")
action, overridden = engine.check_guardrail("guardrail_id", context={})
```

All events are logged persistently (NDJSON under `logs/boundaries/`) and can be streamed via WebSocket (see `server_ws.py` and `config/BOUNDARY_ARCHITECTURE.md`).

## Config

- Default config: `boundaries/config/default_boundary_config.json`
- Schema: `config/schemas/boundary-schema.json`
- Architecture: `config/BOUNDARY_ARCHITECTURE.md`

## Optional dependencies

- `jsonschema` – config validation in `schema.load_validated_config()`
- `websockets` – for `BoundaryWebSocketServer` in `server_ws.py`
