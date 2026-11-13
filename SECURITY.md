# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in **LeadBet**, please do not open a public issue with exploit details. Instead, report it privately via GitHub Security Advisories on this repository.

## Security Practices

- No API keys, database credentials, or OAuth secrets are stored in this repository.
- CORS origins in `apps/api/src/main.py` are explicitly allowlisted via `CORS_ORIGINS`.
- Input payloads in FastAPI are validated strictly with Pydantic models.
- No `eval()` or unsafe HTML injection (`dangerouslySetInnerHTML`) is used in application source files.
