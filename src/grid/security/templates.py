"""Production Configuration Templates.

Environment-specific configuration templates for GRID deployments.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Development Configuration
DEVELOPMENT_CONFIG = {
    # Environment
    "GRID_ENV": "development",
    "GRID_DEBUG": "true",
    # Safety Controls (Permissive)
    "GRID_COMMAND_DENYLIST": "",
    "GRID_MIN_CONTRIBUTION": "0.0",
    "GRID_CHECK_CONTRIBUTION": "false",
    "GRID_LOCKDOWN": "",
    "GRID_BLOCKED_ENV_VARS": "",
    "GRID_REQUIRED_ENV_VARS": "",
    # Secrets (Environment variables for development)
    "USE_SECRETS_MANAGER": "false",
    # Logging
    "GRID_LOG_LEVEL": "DEBUG",
    "GRID_ENABLE_AUDIT": "false",
    # Performance
    "GRID_CACHE_TTL": "60",
    "GRID_MAX_WORKERS": "4",
}

# Staging Configuration
STAGING_CONFIG = {
    # Environment
    "GRID_ENV": "staging",
    "GRID_DEBUG": "false",
    # Safety Controls (Standard)
    "GRID_COMMAND_DENYLIST": "serve",
    "GRID_MIN_CONTRIBUTION": "0.6",
    "GRID_CHECK_CONTRIBUTION": "true",
    "GRID_LOCKDOWN": "",
    "GRID_BLOCKED_ENV_VARS": "GRID_LOCKDOWN",
    "GRID_REQUIRED_ENV_VARS": "GRID_SESSIONS,GRID_CONVERSATIONS",
    # Secrets (Vault integration)
    "USE_SECRETS_MANAGER": "true",
    "VAULT_ADDR": "https://vault.staging.example.com",
    "VAULT_MOUNT_PATH": "secret",
    # Logging
    "GRID_LOG_LEVEL": "INFO",
    "GRID_ENABLE_AUDIT": "true",
    # Performance
    "GRID_CACHE_TTL": "300",
    "GRID_MAX_WORKERS": "8",
    # Monitoring
    "GRID_METRICS_ENABLED": "true",
    "GRID_HEALTH_CHECK_INTERVAL": "30",
}

# Production Configuration
PRODUCTION_CONFIG = {
    # Environment
    "GRID_ENV": "production",
    "GRID_DEBUG": "false",
    # Safety Controls (Restrictive)
    "GRID_COMMAND_DENYLIST": "analyze,serve",
    "GRID_MIN_CONTRIBUTION": "0.8",
    "GRID_CHECK_CONTRIBUTION": "true",
    "GRID_LOCKDOWN": "",
    "GRID_BLOCKED_ENV_VARS": "GRID_LOCKDOWN",
    "GRID_REQUIRED_ENV_VARS": "GRID_SESSIONS,GRID_CONVERSATIONS,GRID_ENV",
    # Secrets (Vault required)
    "USE_SECRETS_MANAGER": "true",
    "VAULT_ADDR": "https://vault.production.example.com",
    "VAULT_MOUNT_PATH": "secret",
    # Logging
    "GRID_LOG_LEVEL": "WARNING",
    "GRID_ENABLE_AUDIT": "true",
    # Performance
    "GRID_CACHE_TTL": "600",
    "GRID_MAX_WORKERS": "16",
    # Monitoring
    "GRID_METRICS_ENABLED": "true",
    "GRID_HEALTH_CHECK_INTERVAL": "15",
    "GRID_ALERT_WEBHOOK": os.getenv("GRID_ALERT_WEBHOOK", ""),
    # Security Headers
    "GRID_SECURITY_HEADERS": "true",
    "GRID_RATE_LIMIT": "100",
    "GRID_SESSION_TIMEOUT": "3600",
}

# Docker Production Configuration
DOCKER_PRODUCTION_CONFIG = {
    **PRODUCTION_CONFIG,
    # Docker-specific
    "GRID_CONTAINER_MODE": "true",
    "GRID_HEALTH_ENDPOINT": "/health",
    "GRID_GRACEFUL_SHUTDOWN_TIMEOUT": "30",
    # Resource limits
    "GRID_MAX_MEMORY_MB": "2048",
    "GRID_MAX_CPU_PERCENT": "80",
}

# Kubernetes Production Configuration
KUBERNETES_CONFIG = {
    **PRODUCTION_CONFIG,
    # Kubernetes-specific
    "GRID_K8S_MODE": "true",
    "GRID_POD_NAME": os.getenv("POD_NAME", ""),
    "GRID_NAMESPACE": os.getenv("NAMESPACE", "default"),
    # Service discovery
    "GRID_SERVICE_NAME": "grid-service",
    "GRID_CLUSTER_DOMAIN": "cluster.local",
    # Volumes
    "GRID_SECRETS_VOLUME": "secrets-volume",
    "GRID_CONFIG_VOLUME": "config-volume",
    "GRID_LOGS_VOLUME": "logs-volume",
    # Probes
    "GRID_LIVENESS_PATH": "/health/live",
    "GRID_READINESS_PATH": "/health/ready",
    "GRID_STARTUP_PATH": "/health/startup",
}


def generate_env_file(config: dict[str, Any], output_path: str) -> None:
    """Generate .env file from configuration."""
    env_content = []

    for key, value in config.items():
        if value:  # Skip empty values
            env_content.append(f"{key}={value}")

    env_file = Path(output_path)
    env_file.write_text("\n".join(env_content) + "\n")
    print(f"Generated environment file: {env_file}")


def generate_docker_compose(config: dict[str, Any], output_path: str) -> None:
    """Generate docker-compose.yml with GRID configuration."""
    docker_compose = f"""version: '3.8'

services:
  grid:
    image: grid:latest
    container_name: grid-production
    restart: unless-stopped

    environment:
{chr(10).join(f'      - {k}={v}' for k, v in config.items() if v and not k.startswith('GRID_K8S'))}

    volumes:
      - ./logs:/app/logs
      - ./config:/app/config

    ports:
      - "8000:8000"

    resources:
      limits:
        memory: {config.get('GRID_MAX_MEMORY_MB', '2048')}M
        cpus: '{config.get("GRID_MAX_CPU_PERCENT", "80")}%'

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000{config.get('GRID_HEALTH_ENDPOINT', '/health')}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

volumes:
  logs:
  config:
"""

    compose_file = Path(output_path)
    compose_file.write_text(docker_compose)
    print(f"Generated docker-compose file: {compose_file}")


def generate_kubernetes_manifests(config: dict[str, Any], output_dir: str) -> None:
    """Generate Kubernetes manifests for GRID deployment."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # ConfigMap
    configmap = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: grid-config
  namespace: {config.get('GRID_NAMESPACE', 'default')}
data:
{chr(10).join(f'  {k}: "{v}"' for k, v in config.items() if v and not any(sensitive in k for sensitive in ['TOKEN', 'KEY', 'SECRET', 'PASSWORD']))}
"""

    # Secret (for sensitive values)
    secret = f"""apiVersion: v1
kind: Secret
metadata:
  name: grid-secrets
  namespace: {config.get('GRID_NAMESPACE', 'default')}
type: Opaque
data:
  # Values should be base64 encoded
  # Use: echo -n 'value' | base64
"""

    # Deployment
    deployment = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: grid-deployment
  namespace: {config.get('GRID_NAMESPACE', 'default')}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: grid
  template:
    metadata:
      labels:
        app: grid
    spec:
      containers:
      - name: grid
        image: grid:latest
        ports:
        - containerPort: 8000

        envFrom:
        - configMapRef:
            name: grid-config
        - secretRef:
            name: grid-secrets

        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "{config.get('GRID_MAX_MEMORY_MB', '2048')}Mi"
            cpu: "{config.get('GRID_MAX_CPU_PERCENT', '80')}%"

        livenessProbe:
          httpGet:
            path: {config.get('GRID_LIVENESS_PATH', '/health/live')}
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

        readinessProbe:
          httpGet:
            path: {config.get('GRID_READINESS_PATH', '/health/ready')}
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: logs-volume
          mountPath: /app/logs

      volumes:
      - name: config-volume
        configMap:
          name: grid-config
      - name: logs-volume
        emptyDir: {{}}
"""

    # Service
    service = f"""apiVersion: v1
kind: Service
metadata:
  name: {config.get('GRID_SERVICE_NAME', 'grid-service')}
  namespace: {config.get('GRID_NAMESPACE', 'default')}
spec:
  selector:
    app: grid
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
"""

    # Write files
    (output_path / "configmap.yaml").write_text(configmap)
    (output_path / "secret.yaml").write_text(secret)
    (output_path / "deployment.yaml").write_text(deployment)
    (output_path / "service.yaml").write_text(service)

    print(f"Generated Kubernetes manifests in: {output_path}")


def main() -> None:
    """Generate all configuration templates."""
    # Generate environment files
    generate_env_file(DEVELOPMENT_CONFIG, ".env.development")
    generate_env_file(STAGING_CONFIG, ".env.staging")
    generate_env_file(PRODUCTION_CONFIG, ".env.production")

    # Generate Docker configuration
    generate_docker_compose(DOCKER_PRODUCTION_CONFIG, "docker-compose.prod.yml")

    # Generate Kubernetes manifests
    generate_kubernetes_manifests(KUBERNETES_CONFIG, "k8s/")

    print("\nConfiguration templates generated successfully!")
    print("\nDeployment instructions:")
    print("1. Development: cp .env.development .env")
    print("2. Staging: cp .env.staging .env && docker-compose -f docker-compose.staging.yml up")
    print("3. Production: cp .env.production .env && kubectl apply -f k8s/")


if __name__ == "__main__":
    main()
