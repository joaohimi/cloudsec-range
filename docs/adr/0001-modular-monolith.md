# ADR-0001: Start with a modular monolith and separate lab execution plane

- Status: Accepted
- Date: 2026-11-02

## Context

The product has many domains (curriculum, assessments, internship, tickets, evidence, labs and security operations). Starting with microservices would add deployment, network and observability overhead before domain boundaries are understood. However, lab execution has a fundamentally different risk profile from ordinary application requests.

## Decision

Build the product API as a modular monolith with clearly separated Python packages/use cases. Keep lab execution behind a separate Lab Controller/Worker boundary. The worker will be deployed independently and will not receive application database credentials or unrestricted access to the host.

## Consequences

Positive:
- Easier local development and debugging.
- Fewer moving parts during the first milestones.
- Clear domain boundaries and future extraction path.
- High-risk execution can be isolated independently.

Trade-offs:
- The API must maintain disciplined module boundaries.
- Future scaling may require extracting the lab controller, evidence service or audit pipeline.
