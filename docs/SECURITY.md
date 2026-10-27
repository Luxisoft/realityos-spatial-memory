# Security and privacy

- Passwords use salted scrypt; access tokens expire and refresh tokens rotate
  with server-side revocation records.
- Every workspace route checks membership and role. Media bytes receive the same
  check.
- Original bytes are in PostgreSQL, avoiding accidental public object links.
  Hashes provide integrity/deduplication, not encryption at rest.
- Capture requires consent and open session. Query cannot write evidence.
- Secrets are environment variables. .env, keystores and local media are ignored
  by Git. Do not log MODEL_API_KEY, JWT secrets or user media.
- Production needs TLS, a rotated JWT_SECRET, constrained CORS, tested backups
  and hosting-provider encryption at rest.
- Device ingestion does not require a human account. An administrator enrolls a
  public device ID and receives a high-entropy companion key once; the server
  stores only a `DEVICE_CREDENTIAL_PEPPER`-derived hash. Rotation and revocation
  are audited. Never reuse `MODEL_API_KEY` as a device credential.
- Device/operator labels and inventory analytics are restricted to workspace
  administrators. They are provenance metadata, never biometric identity.
- Live SAM Video calls use temporary Files API uploads and become `uncertain`
  rather than being automatically replayed after an ambiguous provider failure.

There is no deletion workflow yet; retention, export and erasure require product
policy and implementation before customer data.
