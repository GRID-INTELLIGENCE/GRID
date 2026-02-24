# grid-safety

GRID Safety layer and **Cognitive Privacy Shield**: real-time safety enforcement, PII detection, masking, and compliance presets (GDPR, HIPAA, PCI-DSS) for AI inference.

## Install

```bash
pip install grid-safety
```

## Minimal usage

### Cognitive Privacy Shield (library)

```python
from safety.privacy import get_privacy_engine, PrivacyPreset, AsyncPIIDetector

# Get engine with a compliance preset
engine = get_privacy_engine(preset=PrivacyPreset.BALANCED)

# Detect PII
detections = await engine.detect("Contact me at user@example.com")

# Process (detect + mask/block/ask)
result = await engine.process("My SSN is 123-45-6789")
print(result.processed_text)  # Masked or blocked per preset
print(result.detections)
```

### Run the Safety API server

```bash
safety-api
```

Runs the FastAPI app (auth, rate limiting, pre-check, Privacy Shield middleware, inference queue). Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SAFETY_API_HOST` | `0.0.0.0` | Bind host |
| `SAFETY_API_PORT` | `8000` | Bind port |
| `SAFETY_API_RELOAD` | (off) | Set to `1`, `true`, or `yes` to enable reload |

Endpoints include:

- `POST /infer` — Submit inference (enqueued to Redis)
- `POST /privacy/detect` — Detect PII in text
- `POST /privacy/mask` — Mask or block PII
- `POST /privacy/batch` — Batch PII detection/masking (up to 100 texts)
- `GET /health`, `GET /metrics`

Set `SAFETY_DEGRADED_MODE=true` to run without Redis (e.g. for tests).

## Architecture

The Cognitive Privacy Shield is GRID's core safety and privacy API. For pipeline details, integration points, and key files, see:

- [Safety Layer & Cognitive Privacy Shield — Architecture](https://github.com/GRID-INTELLIGENCE/GRID/blob/main/docs/SAFETY_ARCHITECTURE.md) (in the GRID repo)

## License

MIT. See [LICENSE](LICENSE).
