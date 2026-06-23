# Deployment

The current project is designed for local development and controlled pilots. It is not production hardened.

## Local Docker Services

Docker Compose provides PostgreSQL, Mailpit, the backend, and a one-shot migration service. LM Studio runs separately on the host.

```bash
docker compose up -d postgres mailpit
docker compose --profile tools run --rm migrate
docker compose up --build backend
```

For a Docker backend to reach LM Studio on the host:

```bash
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

## Production Work Required

Before production or real candidate use, add or review:

- Secure secret storage and rotation.
- TLS and network isolation.
- Database backups and restore tests.
- Migration rollback procedure.
- Upload storage isolation and malware scanning policy.
- Retention and deletion policies.
- Rate limiting and abuse protection.
- Centralized logs with sensitive-data redaction.
- Monitoring and incident response.
- Accessibility, privacy, employment-law, and bias-risk review.

## Licensing

The public code is `AGPL-3.0-only`. Organizations that need private deployment, managed hosting, proprietary integration, or enterprise support terms should review [COMMERCIAL.md](../COMMERCIAL.md).
