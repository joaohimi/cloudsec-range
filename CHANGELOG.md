## 0.4.0 — 2026-11-03

### Added
- Additive Alembic migration `0004_learning_progress` for per-user lesson progress, lab attempts and user-linked assessment, competency and evidence history.
- Case-insensitive uniqueness for normalized user email addresses.
- Owner-only user directory API and Next.js administration page: create Learner/Reviewer accounts, update display names/statuses, replace non-Owner roles and revoke a user's active sessions.
- Per-user Learning Progress API and dashboard with module summaries, lesson completion, lab validation, submitted assessments, competency state and evidence counts.
- Learner actions to record lesson progress, start/submit lab attempts, submit assessment answers, self-assess competencies and submit traceable evidence.
- Reviewer queue and UI for lab submissions, manual assessment grading, evidence acceptance/return/rejection and competency self-assessment validation.
- Dedicated `labs:review` permission for Owner and Reviewer roles.
- Progress controls integrated into each curriculum module page; home dashboard metrics now use the authenticated learner's actual records rather than placeholder zeros.
- API contract tests for new routes, schemas, model ownership, role boundaries, separation of duties and migration chain.
- Retired legacy curriculum submission routes with HTTP 410 so old callers cannot inject assessment scores or create unscoped evidence.
- Scoped competency traceability evidence/progress to the authenticated user and preserved curriculum track ordering in the progress dashboard.

### Security and data-integrity decisions
- New progress records are linked to authenticated `user_id`; legacy `learner_key` records remain preserved and are not silently assigned to an account.
- Learners cannot submit a score or mark a competency as mastered. Scores and competency validation are set only through reviewer endpoints.
- Reviewers cannot review their own lab attempts, assessment attempts, evidence or competency progress; a competency review must target another active learner with a submitted self-assessment.
- Mastery requires the linked assessment threshold and at least one reviewed passing assessment or accepted evidence.
- User accounts are disabled rather than deleted; disabling an account revokes its active sessions. Owner assignment remains bootstrap-only.
- Evidence source links must match explicit lesson/lab/assessment-to-competency associations.

### Validation
- API model imports and Python compilation: passed.
- OpenAPI route registration: passed for user management, progress, submissions and review queue.
- Alembic offline SQL generation through `0004_learning_progress`: passed.
- Backend tests: 33 passed, including API contracts, migration chain, identity scoping and separation-of-duties checks.
- Full Next.js typecheck/build was not run in this build environment because npm dependency installation timed out; it must be verified in the local Docker build.
- Live migration against the user's PostgreSQL database was not run here; apply it locally after taking backups.

### Not included yet
- Email-based invitation and password recovery, MFA, SSO or external identity provider.
- Executable/isolated Lab Engine, automated lab validation, ticket submission workflow or cloud sandbox provisioning.
- Automatic evidence scanning or immutable external audit-log shipping.

## 0.2.0 — 2026-11-02

### Added
- First authored curriculum unit: Linux L1 / M1 — Arquitetura e ecossistema.
- Six lessons mapped to six demonstrable competencies and six topics.
- Nine official documentation references.
- Two WSL 2 / Ubuntu 24.04 labs limited to read-only inventory and local documentation.
- Nexus Digital Services simulated ticket `NDS-LNX-001`, linked to all six competencies.
- Mixed 100-point assessment with scoring rubric, threshold and critical-error rules.
- Additive, idempotent content importer executed after canonical curriculum import.
- Learning Center detail rendering for lessons, labs, company ticket, assessment and official references.
- Internship Center read view for authored tickets.

### Changed
- Application version and visible UI version updated to 0.2.0.
- Repository status and implementation documentation updated to distinguish completed content from future workflows.

### Validation
- Python API/content tests: 12 passed.
- Python compilation and Alembic SQL generation through `0002_curriculum_engine`: passed.
- TSX syntax transpilation: passed for modified pages and app shell.
- Full Next.js build/typecheck and live Docker/PostgreSQL import were not run in the build workspace.
