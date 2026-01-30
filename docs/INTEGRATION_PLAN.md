# Integration Plan: Transformer + OpenAI + IBM CP4D + Azure

## Overview
Stateless transformer service consumes raw events, enriches with OpenAI embeddings, computes features, publishes to Kafka/Event Hub. IBM CP4D ModelOps consumes features for scoring. Azure provides event backbone and long-term storage.

## Artifacts Generated
- `transformer/` — FastAPI service with batching, health, Prometheus metrics.
- `streamsets/pipelines/` — Importable StreamSets pipeline (schema validation, DLQ).
- `infra/kafka-topics.sh` — Commands to create Kafka/Event Hub topics.
- `infra/cp4d-auth.sh` / `infra/cp4d-scoring.sh` — Auth and scoring snippets.
- `ml/model/register_model.py` — Register model and create deployment in CP4D.
- `infra/terraform/main.tf` — Azure Event Hub + Storage provisioning.
- `infra/monitoring/prometheus.yml` — Prometheus config for metrics.
- `.github/workflows/ci.yml` — CI: lint, test, build, push Docker image.

## Next Steps (what to run, in order)
1. **Provision infrastructure**
   ```bash
   cd infra/terraform
   terraform init
   terraform apply
   ```
2. **Create topics**
   ```bash
   chmod +x infra/kafka-topics.sh
   ./infra/kafka-topics.sh
   ```
3. **Deploy StreamSets pipeline**
   - Import `streamsets/pipelines/raw-events-to-features.json`.
   - Validate connections (Kafka/Event Hub).
4. **Build and run transformer**
   ```bash
   cd transformer
   docker build -t transformer:latest .
   docker run --rm -e OPENAI_KEY=$OPENAI_KEY -e KAFKA_BOOTSTRAP=$KAFKA_BOOTSTRAP transformer:latest
   ```
5. **Register model in CP4D**
   - Place your model artifact at `ml/model/model.pkl`.
   - Run `python ml/model/register_model.py`.
   - Note the deployment ID.
6. **Wire scoring**
   - Use `infra/cp4d-scoring.sh` to test the scoring endpoint.
   - Optionally, add a consumer microservice that reads `features` topic and calls CP4D.
7. **Monitoring**
   - Deploy Prometheus and Grafana using `infra/monitoring/prometheus.yml`.
   - Observe transformer metrics and StreamSets metrics.
8. **CI**
   - Push changes to GitHub; the CI pipeline will lint, test, build, and push the transformer image.

## Security & Secrets
- Store `OPENAI_KEY`, `CPD_USER`, `CPD_PASS`, `KAFKA_SASL_USERNAME`, `KAFKA_SASL_PASSWORD` in Azure Key Vault or IBM Secrets Manager.
- Use managed identities for Azure; SASL/TLS for Kafka.
- Enable TLS everywhere.

## Data Contracts
- `raw-events`: id, ts, source, payload, meta
- `features`: id, ts, features (embedding_v1, rolling_mean_5, shadow_projection), source_meta, model_version
- `predictions`: id, ts, predictions, explain (optional), provenance

Enforced via StreamSets schema validator; violations go to `raw-events-dlq`.

## Observability
- Structured logs with `id`, `stage`, `latency_ms`.
- Prometheus metrics: messages in/out, batch latency, OpenAI requests/errors.
- CP4D ModelOps drift and performance monitoring.
- Cost alerts for OpenAI token usage.

## Scaling & Resilience
- Run multiple transformer instances; Kafka consumer group balances load.
- Batch OpenAI calls to control cost and improve throughput.
- Use DLQ to isolate bad events without stopping pipeline.
- Use Azure Blob snapshots for audit and replay.

## Diagram
```
Sources → StreamSets → raw-events → Transformer → features → CP4D → predictions → Consumers
                                    ↘ Blob snapshots
```
