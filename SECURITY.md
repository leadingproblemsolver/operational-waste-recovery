# Security

Operational Waste Recovery ingests prompts, responses, file paths, costs, and usage metadata. Possible credential-like content is rejected by default; `--redact-sensitive` redacts likely secrets, emails, and phone numbers before storage. `--allow-secrets` should be restricted to deliberate local use.

The HTTP API binds safely to loopback without credentials. Non-loopback binding requires `OWRP_API_TOKEN`; bearer comparison is constant-time. Browser CORS is disabled unless one exact `OWRP_CORS_ORIGIN` is configured, and preflight requests from other origins are rejected. Use TLS at the reverse proxy, restricted data-directory permissions, backups, and an explicit retention/purge policy.

Report vulnerabilities privately through the repository security-advisory mechanism.
