# CloudSec Range — Product Specification v1.1

## Product mission

Build a complete personal academy and professional internship simulation for the user's path to Cloud Security. Learning Center and Internship Center must provide equal rigor from fundamentals through Cloud Security Architecture.

## Product areas

1. Learning Center — complete lessons, terminology, official documentation, examples, guided practice, independent exercises, troubleshooting and assessments.
2. Internship Center — a persistent fictional company (Nexus Digital Services), assets, departments, projects, tickets, incidents, change management, reviews, deliverables and professional evaluations.
3. Laboratory Engine — reproducible environments, manifests, controlled execution, resource limits, telemetry, verification and cleanup.
4. Attack & Defense Range — authorized Red Team emulation, Blue Team detection, investigation, containment and remediation.
5. Assessment Center — objective checks, practical examinations, accumulated tests, rubrics and mastery evidence.
6. Portfolio Center — sanitized code, diagrams, reports, evidence and projects.
7. Security & Quality Governance — product security, lab safety, curriculum traceability, official-source review and audit.

## Curriculum rule

The user's original study map is canonical. Preserve order, titles, blocks, module identifiers and study hours. Do not create replacement modules or expand DevOps beyond what is needed to understand and secure Cloud infrastructure. Import and validate the exact source map before populating the curriculum database.

## Equal-depth rule

Every competency must have complete learning treatment and a corresponding professional application. The exact form may differ by subject, but foundational competencies must not receive less attention than advanced Cloud Security topics.

Learning coverage: definition, purpose, prerequisites, terminology, internal behavior, standards/protocols, official documentation, real examples, guided lab, independent exercise, troubleshooting, assessment and evidence.

Internship coverage: company context, role, assets, business impact, ticket/service request/incident/change, investigation, execution, troubleshooting, safety scope, measurable acceptance criteria, validation, technical review, documentation and evidence.

Attack simulation is required only where technically relevant and must use authorized isolated targets. Operational troubleshooting is required even when offensive simulation is not relevant.

## Non-negotiable examples of foundational coverage

Linux storage must include block devices, partitions, MBR/GPT, filesystems, inodes, formatting, mounting, unmounting, `/etc/fstab`, UUIDs, mount options, LVM, swap, RAID concepts, quotas, NFS, space/inode exhaustion, I/O diagnostics, backup, snapshot and recovery. It must map to realistic company tickets and connect later to AWS EBS/EFS/S3 without conflating block, file and object storage.

Networking must include OSI/TCP-IP, Ethernet, switching, routing, IPv4/IPv6, subnetting, TCP/UDP, DNS, DHCP, NAT, firewalls, SSH/VPN, HTTP, TLS/PKI, reverse proxies, load balancing, packet analysis and troubleshooting.

Other domains receive the same coverage standard according to their actual scope: Python, Git/GitHub, required DevOps, Cloud foundations, AWS, DevSecOps, Cloud Security and Cloud Security Architecture.

## Fictional company

Nexus Digital Services is a simulated technology company whose environment evolves with the learner. It has systems, networks, Linux servers, storage, applications, databases, repositories, pipelines, AWS accounts, identities, monitoring, backups and security controls. Work tickets begin at foundational infrastructure topics and become more complex as competencies are demonstrated.

## Mastery

A competency is mastered only when the learner can explain it, apply it independently, troubleshoot it and demonstrate a verifiable result. Lesson completion or multiple-choice score alone is insufficient.

## Safety

No offensive activity against public, third-party or personal systems. Vulnerable labs are isolated, disposable, synthetic-data-only, deny-egress by default and resource-limited. Risky kernel/privilege exercises use disposable VMs. AWS labs use a dedicated sandbox account, temporary credentials, allowlists, budgets and cleanup verification.

## Initial implementation boundary

The current 0.2.0 increment supplies the web/API/data foundation, canonical Linux and Networking catalogue, relational competency traceability, and the first authored unit (Linux L1 / M1). The first unit includes six lessons, six competencies, two read-only/local-documentation labs, nine official references, one scoped Nexus Digital Services ticket and a 100-point assessment. It remains in draft until learner execution and review. Real authentication, ticket submission/review workflow, lab execution, attack simulation and AWS provisioning are not yet implemented.
