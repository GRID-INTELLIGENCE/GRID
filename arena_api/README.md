# Arena API - Dynamic Architecture

The Arena API represents a complete modernization of the previous dial-up-like architecture into a dynamic, scalable, and secure API infrastructure. This transformation eliminates the static bottlenecks and creates a seamless integration system inspired by mechanical watches.

## Architecture Overview

### Core Components

1. **API Gateway** (`api_gateway/`)
   - Dynamic routing with service discovery integration
   - JWT and API key authentication
   - Intelligent rate limiting with adaptive algorithms
   - Request/response transformation

2. **Service Mesh** (`service_mesh/`)
   - Automatic service registration and discovery
   - Health monitoring and circuit breakers
   - Load balancing across service instances
   - Fault tolerance and recovery

3. **Services** (`services/`)
   - Microservice architecture with clear separation
   - AI/ML service integration with safety checks
   - Event-driven communication
   - Horizontal scalability

4. **Monitoring** (`monitoring/`)
   - Real-time metrics collection
   - Structured logging with correlation IDs
   - Alerting and anomaly detection
   - Performance monitoring

5. **AI Safety** (`ai_safety/`)
   - Input validation and sanitization
   - Output filtering and content safety
   - Compliance monitoring (HIPAA, GDPR)
   - Bias detection and ethical AI enforcement

## Key Improvements Over Dial-up Architecture

### Before (Dial-up Model)
- Blocking I/O operations
- Single-threaded processing
- Tight coupling between components
- Static routing and limited scalability
- Basic error handling
- Manual service management

### After (Dynamic API Model)
- Asynchronous processing with event-driven architecture
- Parallel processing and load balancing
- Loose coupling with service mesh
- Dynamic routing with health-aware decisions
- Comprehensive error recovery and circuit breakers
- Automated service discovery and registration

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Running the API Gateway
```bash
cd arena_api/api_gateway
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Running a Service (Example: AI Service)
```bash
cd arena_api/services/ai_service
python main.py
```

### Service Registration
Services automatically register with the service discovery system on startup:

```python
# Services register themselves
registration_data = {
    "service_name": "ai_service",
    "url": "http://localhost:8001",
    "health_url": "http://localhost:8001/health",
    "metadata": {
        "version": "1.0.0",
        "capabilities": ["text_generation", "safety_checks"]
    }
}
```

### API Usage Examples

#### Text Generation with AI Service
```bash
curl -X POST "http://localhost:8000/ai_service/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "prompt": "Explain the Arena architecture",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

#### Service Discovery
```bash
curl "http://localhost:8000/services"
```

#### Health Check
```bash
curl "http://localhost:8000/health"
```

## Configuration

### Environment Variables
```bash
# API Gateway
ARENA_API_PORT=8000
ARENA_JWT_SECRET=your-secret-key

# Service Discovery
SERVICE_DISCOVERY_URL=http://localhost:8500

# Monitoring
ARENA_DASHBOARD_URL=http://localhost:3000
ARENA_METRICS_ENDPOINT=http://localhost:9090/metrics

# AI Safety
AI_SAFETY_LOG_LEVEL=INFO
```

### Service Configuration
Each service can be configured independently:

```yaml
# config/service_config.yaml
service:
  name: ai_service
  port: 8001
  health_check_interval: 30
  rate_limits:
    requests_per_minute: 60
    tokens_per_minute: 10000

ai:
  model: arena-gpt
  safety_enabled: true
  max_input_length: 1000
```

## Security Features

### Authentication
- JWT token validation
- API key authentication
- Service-to-service tokens
- Role-based access control (RBAC)

### AI Safety
- Input sanitization and validation
- Harmful content detection
- Bias monitoring
- Compliance checking (HIPAA, GDPR)
- Output filtering

### Rate Limiting
- Fixed window limits
- Sliding window for accuracy
- Token bucket for burst handling
- User and service-specific limits

## Monitoring and Observability

### Metrics Collection
- Request/response metrics
- Error rates and latency
- Service health status
- AI safety compliance scores

### Alerting
- Performance degradation alerts
- Security violation notifications
- Service health issues
- Compliance breaches

### Logging
- Structured JSON logging
- Request correlation IDs
- Security event tracking
- Audit trails

## Deployment

### Docker Build
```bash
docker build -t arena-api .
docker run -p 8000:8000 arena-api
```

### Kubernetes Deployment
```bash
kubectl apply -f k8s/
```

### CI/CD Pipeline
The GitHub Actions pipeline provides:
- Automated testing and linting
- Security scanning
- Docker image building
- Multi-environment deployment
- Performance testing

## Development

### Project Structure
```
arena_api/
├── api_gateway/          # Main API gateway
│   ├── __init__.py      # FastAPI application
│   ├── routing/         # Dynamic routing
│   ├── authentication/  # Auth systems
│   └── rate_limiting/   # Rate limiting
├── service_mesh/         # Service discovery
├── services/             # Microservices
├── monitoring/           # Observability
├── ai_safety/           # AI safety systems
├── cicd/                # CI/CD configurations
└── requirements.txt     # Dependencies
```

### Adding New Services
1. Create service directory under `services/`
2. Implement service with Arena integration
3. Register with service discovery
4. Add authentication and monitoring
5. Include AI safety checks

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=./ --cov-report=html

# Run specific service tests
pytest services/ai_service/
```

## Performance Characteristics

### Scalability
- Horizontal scaling through service mesh
- Load balancing across instances
- Circuit breakers for fault tolerance
- Asynchronous processing

### Benchmarks
- < 100ms P95 response time
- 99.9% uptime SLA
- Auto-scaling based on load
- Zero-downtime deployments

## Compliance and Safety

### Standards Supported
- HIPAA for healthcare data
- GDPR for personal data
- ISO 27001 for information security
- PCI DSS for payment data

### AI Ethics
- Bias detection and mitigation
- Explainable AI decisions
- Content safety filtering
- Audit trails for all AI interactions

## Troubleshooting

### Common Issues
1. **Service not found**: Check service registration and health
2. **Rate limiting**: Review rate limit configurations
3. **Authentication failures**: Verify JWT tokens and API keys
4. **AI safety blocks**: Check input content and compliance rules

### Debug Mode
```bash
export ARENA_DEBUG=true
export LOG_LEVEL=DEBUG
```

## Contributing

1. Follow the established patterns for service integration
2. Include comprehensive tests
3. Add monitoring and logging
4. Ensure AI safety compliance
5. Update documentation

## Roadmap

### Phase 2: Core Services
- Additional AI/ML services
- Data processing pipelines
- Event streaming
- Advanced caching

### Phase 3: AI/ML Integration
- Model serving infrastructure
- Experiment tracking
- A/B testing framework
- Model monitoring

### Phase 4: Optimization
- Performance tuning
- Advanced monitoring
- Security hardening
- Production deployment

---

**Note**: This architecture transforms the previous dial-up limitations into a dynamic, scalable system that can handle modern AI workloads while maintaining security and compliance standards.
