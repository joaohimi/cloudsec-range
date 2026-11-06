# Architecture Overview

## Context

CloudSec Range is a single-user-first learning and professional-practice platform. It will later support additional reviewer/administrator identities, but authorization must be designed server-side from the beginning.

## Architectural style

Start with a modular monolith for the product API and a separate execution boundary for labs. The lab runner must not share the API's database credentials, application secrets, Docker socket or unrestricted host access.

## Logical components

1. Web UI (Next.js): user interface and server-rendered pages.
2. API (FastAPI): curriculum, competencies, tickets, assessments, evidence and audit use cases.
3. PostgreSQL: durable application data.
4. Redis: transient coordination and future job queue; do not treat Redis as the source of truth.
5. Lab Controller: validates requests and policies.
6. Lab Worker: disposable executor, deployed separately from the API.
7. Lab environments: local containers for low-risk scenarios; disposable VMs for kernel/privilege experiments; dedicated AWS sandbox for real cloud services.

## Network zones

- `frontend_plane`: browser-facing web app and API.
- `data_plane`: database and Redis; not directly exposed to the host except loopback-bound development ports.
- Future `lab_plane`: isolated from the app and data planes; egress-deny by default.

## Data ownership

PostgreSQL is authoritative for users, curriculum, progress, tickets, assessments and evidence metadata. Binary evidence files should move to controlled object storage when required; database rows store metadata and checksums, not arbitrary executable content.

## Security boundaries

- No arbitrary shell command endpoint in the API.
- No Docker socket mounted into vulnerable lab containers.
- No host home directory, SSH agent, browser profile or cloud credentials mounted into labs.
- Lab images are allowlisted and versioned.
- Each lab has CPU, memory, process, disk, time and network limits.
- Lab targets are explicit and isolated; public IP targets are prohibited by default.
- Cleanup is idempotent and independently verifiable.
- AWS uses a dedicated account, temporary role sessions, region/service allowlists, budgets and cleanup verification.

## Current implementation boundary

Milestone 0 only starts web, API, PostgreSQL and Redis. It does not provision labs, configure AWS, or provide real user authentication. These omissions are intentional and tracked in the roadmap.
