# CloudSec Range

**Personal Cloud Security Academy & Professional Internship Cyber Range**

CloudSec Range is a learning and professional-practice platform designed to accompany the user's existing study map from infrastructure fundamentals to Cloud Security and, later, Cloud Security Architecture.

The platform has two equally important sides:

- **Learning Center:** complete theory, official documentation, guided practice, independent exercises, troubleshooting and assessments.
- **Internship Center:** a persistent fictional company, realistic infrastructure, work tickets, incidents, change requests, technical reviews and evidence-based evaluations.

The platform must preserve the user's canonical curriculum. DevOps content is limited to what is necessary to understand, build, operate and secure cloud infrastructure.

> Current repository status: **CloudSec Range v0.4.0 — Curriculum Engine + first learning unit + Platform Core + User Management & Learning Progress**. The Linux and Networking source maps are preserved in the catalogue. Linux L1 / M1 now has six authored lessons, six competencies, two safe labs, one fully scoped simulated company ticket, nine official references and a 100-point assessment. The unit remains in draft until the learner completes the work and receives review. Full ticket workflow, controlled lab execution and AWS provisioning remain future increments.

## 1. Architecture at a glance

- Frontend: Next.js 16 + React + TypeScript.
- API: Python 3.12 + FastAPI.
- Database: PostgreSQL 18.
- Cache/queue foundation: Redis 8.
- Local orchestration: Docker Compose.
- Future lab execution: isolated worker plane, initially local and later disposable VMs/AWS sandbox.

The first implementation is a **modular monolith** plus a separately deployable lab-worker boundary. It avoids premature microservices while keeping the future lab execution plane separated from the application.

## 2. Prerequisites on Windows / WSL 2

Use the Ubuntu 24.04 distribution inside WSL 2. Keep the repository in the Linux filesystem, for example `~/projects/cloudsec-range`, rather than under `/mnt/c`, for better filesystem performance and fewer permission issues.

Required:

- WSL 2 with Ubuntu 24.04.
- Docker Desktop with WSL integration enabled, or Docker Engine + Compose plugin inside WSL.
- Git.
- A web browser.

The application services run in containers. You do not need to install PostgreSQL, Redis, Node.js or Python globally just to start this development stack.

## 3. First start

Open Ubuntu (WSL), then run:

```bash
mkdir -p ~/projects
cd ~/projects
```

Extract or clone this repository into `~/projects/cloudsec-range`, then:

```bash
cd ~/projects/cloudsec-range
cp .env.example .env
```

Edit `.env` and replace both placeholder passwords with long, unique random values. Keep the values URL-safe (letters and numbers are easiest for the initial local setup). Never commit `.env`.

Validate and start:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Open:

- Frontend: <http://localhost:3000>
- API documentation: <http://localhost:8000/docs>
- API liveness: <http://localhost:8000/health/live>
- API readiness: <http://localhost:8000/health/ready>

Useful commands:

```bash
docker compose logs -f --tail=100
docker compose logs -f api
docker compose logs -f web
docker compose down
```

`docker compose down` stops and removes containers but keeps named data volumes. **Do not run `docker compose down -v` unless you intentionally want to delete the local PostgreSQL and Redis data.**

## 4. Repository structure

```text
apps/
  api/                 FastAPI application, SQLAlchemy models and Alembic migrations
  web/                 Next.js frontend
services/
  lab-worker/          Reserved boundary for future isolated lab execution
content/
  curriculum/          Canonical curriculum, authored lessons and coverage policy
  labs/                Lab specifications (not executable attack payloads)
docs/
  architecture/        System architecture
  adr/                 Architecture Decision Records
  curriculum/          Curriculum preservation and traceability
  security/             Security boundaries and lab safety
  operations/           Local setup and operational procedures
  quality/              Definition of Done and quality gates
infrastructure/
  docker/              Container-related configuration
  terraform/           Reserved for future sandbox infrastructure
scripts/               Local developer utilities
```

## 5. Important design rules

1. The canonical study map is the source of truth; this repository must not silently reorder or invent curriculum modules.
2. Every competency gets consistent depth in both Learning Center and Internship Center.
3. Foundational topics (including disk devices, partitions, filesystems, mount points, `/etc/fstab`, LVM, inodes, quotas, backups and storage troubleshooting) are first-class content, not optional extras.
4. A competency is not mastered because a lesson was viewed. It requires explanation, practical execution, diagnosis and evidence.
5. The fictional company must provide work context and tickets from the fundamentals onward, not only in advanced Cloud Security modules.
6. Vulnerable environments must never share trust boundaries with the application, database or personal host data.
7. AWS exercises use a dedicated sandbox account, temporary credentials, explicit allowlists, cost controls and automatic cleanup.
8. No attack simulation against public, third-party or personal systems. Labs are restricted to intentionally provisioned, authorized targets.
9. The platform must distinguish real service behavior from simulated telemetry or mock data.
10. Official documentation is attached to each lesson and lab with product/version context and review date.

## 6. Development milestones

- M0: engineering foundation and repository — completed.
- M1: Platform Core (authentication, sessions, RBAC and audit foundation) — implemented; local login validated.
- M2: User Management & Learning Progress — implemented in v0.4.0; pending live migration/build and workflow validation in the local WSL environment.
- M3: fictional company, CMDB, tickets, tasks, incidents and change/review workflow.
- M4: safe local Lab Engine lifecycle (start, observe, stop, cleanup).
- M5: Linux, networking and infrastructure security lab catalogue.
- M6: AWS sandbox and cloud labs.
- M7: controlled attack/defense scenarios and incident workflows.
- M8: professional assessments, evidence governance and portfolio export.

See `docs/roadmap.md` and the ADRs before changing architectural boundaries.

## 7. Current implementation status

Working in this scaffold:

- Learning Center catalogue and per-module traceability pages, backed by FastAPI.
- Platform Core login/session management, owner bootstrap and RBAC.
- Owner user-management UI/API for creating Learner/Reviewer accounts, changing status/roles and revoking sessions.
- Per-user lesson progress and lab-attempt history; assessment submissions are manually reviewed and competency mastery is reviewer-controlled.
- Learning Progress dashboard and Reviewer queue for lab submissions, assessment grading and evidence review.
- First authored learning unit: Linux L1 / M1 with six lessons, six competencies, two local-safe labs, nine official resources, one company ticket and one 100-point assessment.
- Internship Center read view for the authored ticket, linked to its learning unit.
- Canonical Linux map: 28 modules across 9 blocks; Lab 0 is a separate 6-hour environment lab.
- Canonical Networking map: 23 topics across 7 phases.
- Additive Alembic migration and idempotent curriculum import.
- Relational models for topics, competencies, prerequisites, lessons, official resources, labs, tickets, assessments, progress, coverage and evidence.
- API operations to create and associate core learning/internship records.
- Backend API/content/model/security tests (33 tests in the v0.4.0 build workspace).

Still not implemented:

- Email invitations, self-service password recovery, MFA or SSO.
- Authoring and review of the remaining curriculum units; Linux L1 / M1 remains draft until practical execution and independent review.
- Full Internship Center workflow, CMDB, ticket submission and production-like company asset lifecycle.
- Isolated lab provisioning/execution, automated validation, attack simulation or AWS sandbox integration.
- Automatic scoring of free-text answers; assessment grading remains an explicit reviewer action.
- Portfolio export and external immutable audit shipping.

Do not interpret an imported module title or an empty traceability section as completed learning content. See `docs/implementation/curriculum-engine-v1.md` and `docs/implementation/milestone-0-status.md` for exact scope, validation and limitations.

## 8. Official references

- [Next.js installation and requirements](https://nextjs.org/docs/app/getting-started/installation)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [PostgreSQL documentation](https://www.postgresql.org/docs/)
- [Python 3.12 documentation](https://docs.python.org/3.12/)
- [AWS documentation](https://docs.aws.amazon.com/)

For password values in `.env`, generate URL-safe random strings with:

```bash
openssl rand -hex 32
```

Use a different value for `POSTGRES_PASSWORD` and `REDIS_PASSWORD`.


## 7. Platform Core — first account and authentication

Version 0.3.0 adds:
- Argon2id password hashing through `pwdlib`.
- Opaque server-side sessions. The browser receives only an `HttpOnly` cookie; the database stores a SHA-256 verifier, not the raw cookie value.
- CSRF token verification for state-changing session operations.
- Redis-backed login rate limiting.
- RBAC roles `owner`, `learner`, and `reviewer`, with permissions seeded by Alembic migration `0003_platform_core`.
- Audit events for successful/failed login, logout, bootstrap owner creation and session revocation.
- Authenticated frontend shell and login route.

After starting the updated stack and applying migrations, create the first owner interactively:

```bash
docker compose exec api python -m app.scripts.create_owner \
  --email owner@example.local \
  --name "Platform Owner"
```

Enter a password of at least 15 characters when prompted. It is entered interactively, not in the shell command. The bootstrap command refuses to create another initial owner once an owner already exists. There is deliberately no public registration endpoint.

Open <http://localhost:3000/login> and sign in. The local development cookie is not marked `Secure` because the stack uses HTTP on localhost. For production, set `SESSION_COOKIE_SECURE=true`, serve the entire application over HTTPS, configure exact CORS origins, use strong unique database/Redis credentials, and rotate secrets according to operations policy.

## 8. M2 — User Management & Learning Progress (v0.4.0)

The `0004_learning_progress` migration adds user-scoped lesson progress and lab attempts, and connects assessment attempts, competency progress and evidence to real `users.id` values. Existing legacy rows using `learner_key` are preserved and are deliberately not assigned to the Owner account automatically.

Main routes:

- `GET/POST /api/v1/users` — Owner user directory and account creation.
- `PATCH /api/v1/users/{id}` and `PUT /api/v1/users/{id}/roles` — status/profile and role management.
- `GET /api/v1/learning/me/progress` — current user's progress summary.
- `GET /api/v1/learning/modules/{code}/progress` — progress within one module.
- `PUT /api/v1/learning/lessons/{id}/progress` — learner-reported lesson status.
- `POST /api/v1/learning/labs/{id}/attempts` and `PATCH /api/v1/learning/lab-attempts/{id}/submit` — start and submit lab work; validation remains reviewer-controlled.
- `POST /api/v1/learning/assessments/{id}/attempts` — submit answers without submitting a score.
- `GET /api/v1/learning/review-queue` — Reviewer queue for labs, assessments, evidence and competency self-assessments.
- `POST /api/v1/learning/competencies/{id}/review` — Reviewer validates another learner’s demonstrated/mastered/reinforcement state; self-review is prohibited.
- `POST /api/v1/learning/evidence` and `POST /api/v1/learning/evidence/{id}/review` — own evidence submission and separate reviewer decision.

Frontend routes: `/progress`, `/admin/users`, `/reviews`, and progress controls within each Learning Center module. The Reviewer workspace needs a separate Reviewer account to test least-privilege behavior. Reviewers cannot review their own lab, assessment, evidence or competency submissions; Owner cannot bypass this separation-of-duties rule for their own work.

Apply new migrations only after code/database backups. Do not use `docker compose down -v`.
