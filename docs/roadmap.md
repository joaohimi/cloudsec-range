# Product Roadmap

## M0 — Engineering Foundation (current)

- Monorepo, documentation, Compose, Next.js, FastAPI, PostgreSQL, Redis.
- Liveness/readiness endpoints, baseline models and migration.
- Local startup and basic tests.

Exit criteria: all services start; API readiness checks PostgreSQL and Redis; web is reachable; migration runs; baseline tests pass.

## M1 — Platform Core

- Authentication and session lifecycle.
- Server-side authorization and data-access layer.
- Audit events and secure settings.
- API error model and pagination.
- CI checks and dependency lockfiles.

## M2 — Learning Center (in progress)

- [x] Import the currently available canonical Linux and Networking maps.
- [x] Version, track, block and module catalogue.
- [x] Relational models for competencies, prerequisites, lessons, resources, labs, assessments, progress and evidence.
- [x] Coverage checklist model for both learning and internship treatment.
- [x] First complete content package: Linux L1 / M1 (six lessons, six competencies, two local-safe labs, one professional ticket, one 100-point assessment).
- [ ] Author and validate the remaining topics/competencies with official documentation.
- [ ] Complete lesson, exercise, lab, revision and mastery workflows.

## M3 — Internship Center (traceability foundation started)

- [x] Extend internship tickets with asset/business context, role, state, investigation, execution, validation and safety scope.
- [x] Associate tickets with curriculum competencies.
- [x] First fully scoped Nexus Digital Services simulated ticket linked to Linux L1 / M1.
- [ ] Full Nexus Digital Services company environment and CMDB.
- Asset register/CMDB, departments and projects.
- Tickets, service requests, incidents and change requests.
- Submission, review, acceptance criteria and evidence.

## M4 — Local Lab Engine

- Lab catalog and signed/versioned manifests.
- Controller/worker boundary.
- Safe container labs for low-risk exercises.
- Disposable VM strategy for OS/kernel-level exercises.
- Resource limits, isolation, logs and cleanup verification.

## M5 — Fundamentals and Infrastructure Labs

- Networking and Linux labs, including full storage/filesystem coverage.
- Python and Git/GitHub security practice.
- DevOps technologies only to the depth required for Cloud Security.

## M6 — AWS Sandbox

- Dedicated account, temporary role sessions and policy guardrails.
- AWS IAM, VPC, EC2, EBS/EFS/S3, KMS, logging and detection labs.
- Cost limits and orphan-resource cleanup.

## M7 — Attack/Defense and Cloud Security Operations

- Safe attack emulation, detection, incident investigation and remediation.
- Threat hunting, vulnerability management and security posture scenarios.

## M8 — Professional Assessments and Portfolio

- End-to-end company missions.
- Technical reviews and competency gates.
- Sanitized portfolio exports and final architecture project.

The roadmap is a product implementation sequence, not a replacement or reordering of the learner's academic curriculum.
