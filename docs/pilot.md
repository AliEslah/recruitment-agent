# Pilot Guidance

Do not run a real-candidate pilot until legal, security, privacy, accessibility, and operational reviews are complete.

## Minimum Review Areas

- Employment-law and bias-risk review for the intended jurisdiction.
- Privacy notice, consent, retention, deletion, and data-subject request handling.
- Authentication, authorization, secret management, network isolation, and TLS.
- Rate limits for candidate entry, OTP, uploads, and admin APIs.
- Backup, restore, migration rollback, incident response, and audit-log review.
- Accessibility review for recruiter, manager, admin, and candidate pages.
- Human review workflow and final decision ownership.

## Data Rules

Use synthetic data until the pilot is approved. Do not publish real resumes, transcripts, emails, raw tokens, OTPs, screenshots, logs, or reports.

## Local-First Boundary

Pilot plans should preserve the local LM Studio boundary unless a separate deployment review and commercial agreement explicitly define another architecture. No cloud LLM fallback is part of the public AGPL release.
