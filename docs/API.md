# Read-Only HTTP API

## Authentication

`/health` and `/health/live` are liveness endpoints. All other routes require `Authorization: Bearer <OWRP_API_TOKEN>` when a token is configured. A token is mandatory for non-loopback binding.

## Endpoints

```text
GET /health
GET /health/live
GET /health/ready
GET /api/status
GET /api/repositories
GET /api/query?q=<text>&limit=8
GET /api/capsules
```

Query text is limited to 500 characters and results to 100. All responses use JSON and `Cache-Control: no-store`. The API exposes no mutation endpoints.

```bash
curl http://127.0.0.1:8787/health
curl -H "Authorization: Bearer $OWRP_API_TOKEN" \
  "http://127.0.0.1:8787/api/query?q=redis%20timeout&limit=8"
```
