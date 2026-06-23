# Security

The public security policy is in [SECURITY.md](../SECURITY.md). This guide summarizes implementation boundaries for local development and pilot planning.

## Sensitive Data Rules

Do not commit, attach, or paste:

- Real candidate resumes, transcripts, names, emails, phone numbers, or private hiring notes.
- Raw interview tokens.
- Raw OTPs.
- JWTs, API keys, passwords, SMTP credentials, database URLs with real credentials, or local `.env` files.
- Runtime uploads, local databases, logs, caches, or private machine paths.

## Current Controls

- JWT authentication and role checks for recruiter, manager, and admin APIs.
- Public candidate interview-entry endpoints protected by invite token, OTP, and active-session nonce boundaries.
- Raw invite tokens and OTPs are redacted before communication logs are persisted.
- Interview tokens and OTPs are stored as hashes.
- LLM, audit, and communication logs are available through admin-only endpoints.
- The LLM boundary is local LM Studio only.

## Production Gaps

The MVP is not production hardened. Before real candidate use, review rate limits, retention, encryption, backup/restore, secrets management, deployment isolation, audit policies, incident response, accessibility, legal compliance, and bias monitoring.

## Disclosure

Report vulnerabilities privately to the maintainer. If no private security channel is configured, open a minimal public issue requesting contact without exploit details or sensitive data.
