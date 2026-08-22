# ReworkTrace Review Web

Thin Next.js + TypeScript review surface over the existing Operational Waste Recovery Python API.

## Execution path

```text
/review/<audit_id>
  -> server-side TypeScript getReview()
  -> GET OWRP_API_URL/api/review/<audit_id>
  -> Python OWR HTTP server
  -> SQLite duplicate_pairs + interactions + context_capsules
  -> validated JSON contract
  -> evidence-first review UI
```

The browser never receives `OWRP_API_TOKEN`; the Next.js server performs the backend request.

## Run locally

Start the Python backend from the repository root:

```bash
python -m pip install .
owrp serve --host 127.0.0.1 --port 8787
```

Then start the web app:

```bash
cd web
npm install
OWRP_API_URL=http://127.0.0.1:8787 npm run dev
```

If the backend is configured with `OWRP_API_TOKEN`, provide the same token only to the Next.js server environment:

```bash
OWRP_API_URL=http://127.0.0.1:8787 OWRP_API_TOKEN=<token> npm run dev
```

Open a real persisted pair at:

```text
http://localhost:3000/review/<pair_id>
```

## Verification

```bash
npm test
npm run typecheck
npm run build
```

The contract tests cover happy path, missing review, malformed success payload, unauthorized backend response, and preservation of `NOT_MEASURABLE`.