# ADR-0002: Runtime and data-service baseline

- Status: Accepted for development scaffold
- Date: 2026-11-02

## Decision

- Next.js 16.4.x with React 19.3.x and TypeScript.
- Node.js 26 LTS in the frontend container.
- Python 3.12 in the API container to align with Ubuntu 24.04 and the current supported Python lifecycle.
- PostgreSQL 18.6 for durable state.
- Redis 8 for transient coordination.

## Rationale

The selected lines are supported as of the project baseline date. Exact dependency resolution will be captured in lockfiles during the first dependency-install/build step. Production images must later be pinned by immutable digest and patched on a defined schedule.

## Compatibility note

Next.js documents Node.js 20.9 as its minimum. Node.js 26 is the active LTS line as of 2026-11-02. Python 3.12 remains in security-fix support and is the native baseline for Ubuntu 24.04.
