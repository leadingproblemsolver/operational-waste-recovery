# OWR Trace Inspector

A bounded Next.js/TypeScript review surface over the Python OWR API.

## Boundary

```text
browser
  -> Next.js server component
  -> OWRP_API_BASE_URL/api/findings/:pair_id
  -> bearer token (server only)
  -> Python OWR HTTP server
  -> SQLite duplicate_pairs + interactions + context_capsules
  -> typed finding payload
```

The browser never receives `OWRP_API_TOKEN`.

## Run

Start the OWR API from the repository root:

```bash
export OWRP_API_TOKEN=local-proof-token
PYTHONPATH=src python -m owrp.cli --root ./state serve --host 127.0.0.1 --port 8787
```

Then:

```bash
cd web
npm install
OWRP_API_BASE_URL=http://127.0.0.1:8787 \
OWRP_API_TOKEN=local-proof-token \
npm run dev
```

Open:

```text
http://localhost:3000/review/<duplicate_pair_id>
```

## Proof cases

The Python tests cover:

- authenticated finding read
- unauthorized read
- missing finding
- observed/inferred separation
- `ESTIMATED`
- `NOT_MEASURABLE`

The TypeScript contract tests cover:

- happy-path typed finding
- 404
- malformed successful response
- unauthorized upstream
- `NOT_MEASURABLE` preservation

CI also runs TypeScript type-check, Vitest, and `next build`.

## Claim boundary

This proves a production-shaped TypeScript -> HTTP -> Python -> SQLite integration and bounded failure handling. It does not prove customer usefulness, production traffic, realized savings, or independent human ownership.
