# Security Policy

Implementation notes and pilot hardening guidance are in [docs/security.md](docs/security.md).

## Reporting Vulnerabilities

Please report vulnerabilities privately to the maintainer before opening a public issue. If no private security channel is configured yet, open a minimal public issue saying that you need a security contact, without exploit details, secrets, candidate data, raw tokens, or OTPs.

## Sensitive Data Rules

Do not include the following in issues, PRs, screenshots, logs, eval reports, or attachments:

- Real candidate resumes, transcripts, names, emails, phone numbers, or private hiring notes.
- Raw interview tokens.
- Raw OTPs.
- JWTs, API keys, passwords, SMTP credentials, database URLs with real credentials, or local `.env` files.
- Private machine paths such as user home directories.

## Interview Token And OTP Expectations

- Interview tokens and OTPs are delivery secrets.
- Raw interview tokens and OTPs may be sent through local SMTP/Mailpit during development, but must not be persisted in logs or committed artifacts.
- Persisted communication logs should use explicit redactions such as `[REDACTED_INTERVIEW_TOKEN]` and `[REDACTED_OTP]`.
- Candidate interview actions after start must preserve the client session nonce boundary.

## Supported Scope

The current MVP security scope covers local development with PostgreSQL, Mailpit, JWT/RBAC, token/OTP interview entry, redacted communication logs, and local LM Studio. It is not production-hardened.

Production use requires additional review for authentication, authorization, rate limits, retention, encryption, audit policy, secrets management, deployment isolation, legal compliance, and incident response.

## Local-Only LLM Boundary

The backend uses the OpenAI-compatible client interface to call LM Studio locally. It must not send hiring data to OpenAI cloud, Anthropic, Gemini, or another external LLM provider as a fallback.
