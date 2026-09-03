# Human-Tried Operational Learnings

Operator label: `lpsatwork`

Purpose: accumulate concise, evidence-backed operational/programmatic learnings earned through manual execution. Each entry should come from an observed receipt, not an inferred claim.

## 2026-09-04 — HTTP / PowerShell

- In Windows PowerShell, `curl` may resolve to `Invoke-WebRequest`; Unix cURL flags such as `-i`, `-H`, `--max-time`, and `\` continuation therefore do not behave as expected.
- `Invoke-WebRequest -Headers` expects a PowerShell dictionary/hashtable, e.g. `@{ Authorization = "Bearer ..." }`.
- `404 Not Found` means the requested route/resource was not found (or intentionally hidden); it does not by itself prove an authentication failure.
- `401 Unauthorized` means the target exists for the request but valid authentication credentials are required or the provided credentials were rejected.
- A timeout is a transport/client-deadline failure, not an HTTP status response; classify it separately from `4xx`/`5xx`.
- Client classification boundary established manually: `2xx -> success`, `401 -> auth_failure`, `404 -> not_found`, `timeout -> timeout`.

## Entry rule

Append only when a manual or externally observed run changes what we can confidently claim. Prefer one-line causal lessons over generic notes.
