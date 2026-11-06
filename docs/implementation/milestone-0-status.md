# Engineering Foundation and Curriculum Engine — Implementation Status

Date: 2026-11-02
Version: 0.2.0 — first authored Linux learning unit

## Implemented

- Monorepo and Compose application foundation.
- Next.js Learning Center catalogue and per-module traceability views, backed by the API.
- FastAPI liveness/readiness and system information endpoints.
- PostgreSQL 18 and Redis 8 services, separated Compose networks and localhost-only published ports.
- SQLAlchemy models and Alembic `0001_initial` + additive `0002_curriculum_engine`.
- Canonical import manifest for Linux and Networking.
- Idempotent seeding of source version, tracks, blocks, modules and the separate Linux Lab 0.
- First authored unit: Linux L1 / M1 with 6 lessons, 6 competencies, 2 read-only/local-documentation labs, 9 official resources, one fully scoped Nexus Digital Services ticket and a 100-point mixed assessment.
- Expanded module detail API and Learning Center page to render lesson content, lab manifests, ticket procedure, assessment questions/rubric and official references.
- Internship Center now lists registered simulated tickets from the API.
- Relational curriculum graph: topics, competencies, prerequisites, lessons, official resources, labs, internship tickets, assessments, progress, coverage and evidence.
- API create/read operations for the main content entities and traceability.
- Coverage checklist creation for both Learning Center and Internship Center whenever a competency is created.
- API tests and canonical manifest integrity tests.

## Validation performed in the build workspace

- Python compilation: passed.
- API tests: 12 passed (including first-unit content manifest and curriculum contract tests).
- FastAPI OpenAPI generation: passed.
- Alembic SQL generation through `0002_curriculum_engine`: passed.
- Canonical map checks: passed (Linux 28 modules/9 blocks; Lab 0 separate; Networking 23 topics/7 phases).

## Not validated in this workspace

- Docker build or Compose startup: Docker CLI/daemon was unavailable.
- Migration against a live PostgreSQL 18 instance: not run.
- Frontend `npm install`, Next.js build and TypeScript typecheck: not run because `node_modules` were not present.

## Not implemented yet

- Authentication, authorization, reviewer identities and immutable audit-event trail.
- Content development and review for the remaining modules; L1/M1 is authored but remains in draft pending learner execution and review.
- Detailed Internship Center workflow, full Nexus Digital Services asset inventory/CMDB, ticket state transitions, submissions and technical-review UI.
- Lab execution worker, isolation controller, disposable VM management and cleanup verification.
- AWS sandbox account integration, cost guardrails and provisioning.
- Interactive assessment submissions and correction workflow; attack/defense execution and portfolio export workflow.

The current increment establishes curriculum data and traceability. It does not claim the full academy or simulated internship is complete.
