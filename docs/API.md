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
GET /api/review/<pair_id>
```

Query text is limited to 500 characters and results to 100. All responses use JSON and `Cache-Control: no-store`. The API exposes no mutation endpoints.

`GET /api/review/<pair_id>` resolves one persisted duplicate-work finding. `pair_id` is the 24-character hexadecimal identifier stored in `duplicate_pairs`. The response joins the pair to its two source interactions and the latest recovery capsule for that repository.

The review contract keeps evidence states explicit:

- `measurement_state: "OBSERVED"` means the duplicate pair and its token/cost values are deterministic measurements over imported data.
- `finding.state: "OBSERVED"` labels the persisted repeated-work finding.
- `inference.state: "INFERRED"` labels the interpretation that the pair may represent avoidable context reconstruction.
- The API does **not** claim realized labor savings, production ROI, or organization-wide waste.

Unknown or malformed pair IDs return `404 {"error":"review_not_found"}`. When API authentication is enabled, authorization is checked before the review lookup, so a missing/invalid bearer token returns `401` without disclosing whether a pair exists.

```bash
curl http://127.0.0.1:8787/health
curl -H "Authorization: Bearer $OWRP_API_TOKEN" \
  "http://127.0.0.1:8787/api/query?q=redis%20timeout&limit=8"
curl -H "Authorization: Bearer $OWRP_API_TOKEN" \
  "http://127.0.0.1:8787/api/review/<pair_id>"
```