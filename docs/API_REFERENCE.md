# GRID API Reference

## Authentication
`POST /auth/token`  
Authenticate user and get access token

## Inference
`POST /api/v1/inference/`  
Process inference request synchronously

`POST /api/v1/inference/async`  
Queue async inference request

`GET /api/v1/inference/status/{task_id}`  
Check status of async request

## Privacy
`POST /api/v1/privacy/detect`  
Detect PII in text

`POST /api/v1/privacy/mask`  
Mask PII in text

`POST /api/v1/privacy/batch`  
Batch process privacy operations

## Health
`GET /health`  
Service health check

## Models
`GET /api/v1/inference/models`  
List available models
