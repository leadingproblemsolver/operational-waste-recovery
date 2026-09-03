# Human-tried HTTP probe — PowerShell

Operator label: `lpsatwork`

Date: 2026-09-04

## Purpose

Manual HTTP/API foundation check against the GitHub REST API from Windows PowerShell.

This is a human-tried receipt, not an automated test and not a claim of generalized HTTP expertise.

## Environment gotcha discovered

In Windows PowerShell, `curl` resolved to `Invoke-WebRequest`, so Unix-style flags such as `-i`, `-H`, `--max-time`, and `\` line continuation did not behave like real cURL.

The working PowerShell form used `Invoke-WebRequest -Uri ...` and `-TimeoutSec`.

## Confirmed observations

### 1. Existing repository → HTTP 200

Command:

```powershell
Invoke-WebRequest -Uri "https://api.github.com/repos/leadingproblemsolver/operational-waste-recovery"
```

Observed:

```text
StatusCode        : 200
StatusDescription : OK
```

The response included GitHub API headers such as `X-GitHub-Media-Type`, the selected API version, rate-limit headers, and a JSON response body describing the repository.

Interpretation: transport completed and the target resource exists.

### 2. Missing repository → HTTP 404

Command:

```powershell
Invoke-WebRequest -Uri "https://api.github.com/repos/leadingproblemsolver/does-not-exist"
```

Observed body:

```json
{"message":"Not Found","documentation_url":"https://docs.github.com/rest/repos/repos#get-a-repository","status":"404"}
```

PowerShell surfaced the non-2xx response as `WebCmdletWebResponseException`.

Interpretation: the server returned an HTTP response; the requested resource was not found. This is different from a transport timeout.

### 3. Unreachable target with one-second timeout → timeout

Command:

```powershell
Invoke-WebRequest -Uri "https://10.255.255.1" -TimeoutSec 1
```

Observed:

```text
Invoke-WebRequest : The operation has timed out.
```

Interpretation: no successful HTTP response was obtained within the client deadline. A timeout must not be classified as an HTTP 4xx/5xx response.

### 4. Invalid-token attempt against wrong endpoint → HTTP 404

Command attempted:

```powershell
Invoke-WebRequest `
  -Uri "https://api.github.com/leadingproblemsolver" `
  -Headers @{ Authorization = "Bearer definitely-invalid-token" }
```

Observed:

```text
Invoke-WebRequest : The remote server returned an error: (404) Not Found.
```

Interpretation: this does **not** verify authentication handling. The endpoint itself is invalid for the intended auth test, so the observed `404` is a resource/route failure, not an auth failure.

### 5. Invalid bearer token against authenticated-user endpoint → HTTP 401

Command:

```powershell
Invoke-WebRequest `
  -Uri "https://api.github.com/user" `
  -Headers @{ Authorization = "Bearer definitely-invalid-token" }
```

Observed:

```text
Invoke-WebRequest : The remote server returned an error: (401) Unauthorized.
```

Interpretation: the route exists, but the presented credentials are not accepted for the requested authenticated operation.

**Learned:** `404` means the requested route/resource was not found (or intentionally hidden), while `401` means the server recognized the request target but requires valid authentication credentials.

## Foundation receipts earned

- distinguished an HTTP success (`200`) from a resource-level HTTP failure (`404`);
- distinguished an HTTP error response from a client-side timeout;
- identified a real shell/runtime mismatch: PowerShell aliases `curl` to `Invoke-WebRequest` in this environment;
- corrected the timeout syntax to native PowerShell semantics;
- caught an endpoint-selection error before misclassifying a `404` as authentication failure;
- verified an actual `401 Unauthorized` using the correct authenticated-user endpoint;
- established the base client classification boundary: `2xx -> success`, `401 -> auth_failure`, `404 -> not_found`, `timeout -> timeout`.

## Next bounded test

Implement or verify a tiny client classification boundary:

```text
2xx     -> success
401     -> auth_failure
404     -> not_found
timeout -> timeout
```

Do not add retry policy until these base classifications are correct.
