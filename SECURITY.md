# Security Policy

CloudSec Range is a security-training project. Its own application and lab infrastructure must be protected as carefully as the systems used for training.

## Reporting a vulnerability

Do not publish secrets, personal data, AWS credentials, lab access tokens or exploit details from a live environment. For this personal project, record findings privately in the project's security backlog and reproduce them only in a disposable local test environment.

## Scope

- The application, API and infrastructure in this repository.
- Intentionally provisioned and explicitly authorized CloudSec Range labs.

Out of scope:

- Public internet targets.
- Third-party systems.
- Personal devices or networks that are not explicitly part of an isolated lab.
- Production or personal AWS accounts.

## Security baseline

See `docs/security/lab-safety-model.md` and `docs/quality/definition-of-done.md`. Attack execution is not enabled in milestone 0.


## Platform authentication and progress baseline (v0.4.0)

- New passwords are hashed with Argon2id; plaintext passwords must never be logged or committed.
- Session cookies are opaque, HttpOnly, SameSite=Lax, and path-scoped to `/`. Do not add a Domain attribute.
- PostgreSQL stores only SHA-256 hashes of session and CSRF tokens. The browser receives the CSRF token in memory and must send `X-CSRF-Token` for state-changing session operations.
- Redis is required for login throttling. Authentication fails closed (503) when the rate-limiting store is unavailable.
- RBAC is enforced by API dependencies, not by frontend visibility alone.
- The initial Owner is created with an interactive CLI prompt. There is no built-in default account or public registration.
- The local HTTP development profile sets `SESSION_COOKIE_SECURE=false`. This is not a production setting. Production must use HTTPS and `SESSION_COOKIE_SECURE=true`.
- Current limitations: no MFA, password recovery, user invitation workflow, or remote append-only audit export yet.


## M2 user and learning-progress controls

- User administration is restricted by the `users:manage` permission. Public registration is not exposed. API-created accounts can receive only the `learner` and `reviewer` roles; Owner remains bootstrap-only.
- Disabling an account revokes its active sessions. Account records are soft-disabled rather than deleted so learning and audit records remain attributable.
- New progress, lab-attempt, assessment-attempt and evidence records are scoped to the authenticated `user_id`. Legacy `learner_key` data is preserved without speculative reassignment.
- Learners can report lesson completion and submit lab/assessment work; they cannot submit assessment scores or mark competencies as mastered. Reviewer permissions control grading, lab validation, evidence review and validation of competency self-assessments. Reviewers cannot review their own submissions; competency reviews require a target learner distinct from the reviewer.
- Competency mastery requires an assessment pass or accepted evidence and must meet the threshold configured by linked assessments.
- Evidence is linked only to an explicitly associated lesson, lab or assessment attempt. Artifact references are metadata; this version does not upload or scan files.
- Reviewer decisions and user-management actions generate audit events. Legacy curriculum submission routes that accepted client-supplied scores or unscoped evidence return HTTP 410 and direct clients to the per-user workflow. Audit data is currently stored in the same PostgreSQL deployment, not in an external immutable log service.
- The progress dashboard reports learner activity; lesson completion is self-reported, while lab validation, assessment scores and competency mastery are reviewer-controlled. These states must not be conflated.
