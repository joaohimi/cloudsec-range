# Curriculum Engine v1 — Implementation Notes

Date: 2026-11-02

## Scope delivered

This document describes the v1 foundation delivered before the first authored unit. The current repository version is 0.2.0; Linux L1 / M1 content is recorded separately in `linux-l1-m01-architecture.md` and `milestone-0-status.md`.

This increment turns the curriculum placeholders into a data-backed catalogue and traceability foundation.

- A versioned import manifest for the exact Linux and Networking roadmap currently available.
- Relational blocks and modules, with the original order, source IDs, titles and estimated hours.
- Topics and competencies, including explicit prerequisite edges.
- Lessons and official learning resources.
- Labs with an explicit local-safe / isolated-VM safety profile.
- Internship tickets linked to competencies and modules, with business context, role, initial state, investigation, execution, validation, safety scope and acceptance criteria.
- Assessments, attempts, threshold result and competency progress records.
- Coverage requirements for both Learning Center and Internship Center.
- Evidence records that must reference an item already associated with the same competency.
- Read API for the catalogue, module traceability and competency traceability, plus write endpoints for authoring core records.
- Learning Center server-rendered catalogue and module detail pages.
- Version 0.2.0 adds the first authored unit: six lessons, six competencies, two local-safe labs, nine official resources, one detailed simulated internship ticket and one 100-point assessment.

## Canonical import

The import manifest is `content/curriculum/canonical-roadmap-v1.json`.

| Track | Blocks/phases | Modules/topics | Module-hours |
|---|---:|---:|---:|
| Linux | 9 | 28 | 312 |
| Linux Lab 0 | — | Separate lab | 6 |
| Networking | 7 | 23 | 214 |

The Linux total is 318 hours when Lab 0 is included. The 28 Linux modules remain separate from Lab 0. The API catalogue sums module-hours separately and displays Lab 0 as an environment lab.

Only the Linux and Networking roadmap has been imported because these are the canonical source documents currently available in the project. The other career domains are not fabricated or seeded by this increment.

## Database additions

Alembic revision: `0002_curriculum_engine` (additive after `0001_initial`).

New tables include `curriculum_versions`, `curriculum_blocks`, `curriculum_topics`, `lessons`, `labs`, `assessments`, `assessment_attempts`, `coverage_requirements`, `competency_progress`, `evidence`, and the association tables `lesson_competencies`, `lab_competencies`, `ticket_competencies`, `assessment_competencies`, `competency_prerequisites`.

Existing tables are extended with version/block/topic/module references and richer internship-ticket fields. The migration does not drop existing tables or existing curriculum/ticket rows.

## API

Base URL: `/api/v1/curriculum`

- `GET /catalog` — version, tracks, blocks, modules, source hours and actual record counts.
- `GET /modules/{module_code}` — module, competencies, topics, resources, lessons, labs, tickets and assessments.
- `GET /coverage/summary` — learning and internship coverage state.
- `GET /competencies/{competency_code}/traceability` — prerequisites, mapped lessons/labs/tickets/assessments, coverage, evidence and progress.
- `POST /modules/{module_code}/topics`
- `POST /modules/{module_code}/competencies` — automatically creates the standard coverage checklist for both centers and can map prerequisites.
- `POST /modules/{module_code}/resources`
- `POST /modules/{module_code}/lessons`
- `POST /modules/{module_code}/labs`
- `POST /modules/{module_code}/tickets`
- `POST /modules/{module_code}/assessments`
- `POST /assessments/{assessment_id}/attempts`
- `POST /evidence` — validates that the referenced source object is already associated with the competency.
- `PATCH /coverage/{coverage_id}` — permits `missing`, `draft` or `ready`; `verified` is reserved for an authenticated review workflow.

The complete interactive API schema is available from `/docs` in development mode.

## Local startup behavior

The API startup command now runs:

1. `alembic upgrade head`
2. `python -m app.scripts.seed_curriculum`
3. `uvicorn ...`

The import is idempotent. It is safe to restart the API; do not use volume deletion as a migration procedure.

## Explicit limitations

- Real authentication and authorization are not implemented. The learner progress key currently defaults to the local profile key `primary`.
- Other modules still have catalogue records only; detailed lessons, topic breakdowns, competencies, official source links, labs, Nexus tickets and assessments have not yet been authored for them. Linux L1 / M1 is the first completed content package, but remains in draft pending learner execution and review.
- No `verified` coverage transition or real reviewer identity exists yet.
- Lab records are metadata only. There is no lab execution worker, container/VM provisioning, or AWS provisioning.
- `aws-sandbox-approved` is intentionally not an accepted lab safety profile. AWS execution must wait for the separate sandbox account, IAM boundaries, egress controls, budgets and cleanup validation.
- The Internship Center can display the authored ticket, but workflow state transitions, CMDB, ticket submissions, technical review and evidence review are not complete.
- The frontend source has been updated, but a Next.js build/typecheck was not run in the build workspace because `node_modules` are not present. The API Python tests and Alembic SQL generation were run.

## Acceptance checks performed

- Python source compilation: passed.
- API and authored-content test suite (current v0.2.0 workspace): 12 passed.
- Alembic upgrade SQL generation through revision `0002_curriculum_engine`: passed.
- FastAPI OpenAPI schema generation with all curriculum endpoints: passed.
- Canonical manifest assertions: 28 Linux modules / 9 blocks / 312 module-hours; separate Lab 0 / 6 hours; 23 Networking topics / 7 phases / 214 hours.
- Docker image build and migration against a live PostgreSQL 18 service: not run in the build workspace.
