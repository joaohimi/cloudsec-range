# Canonical Curriculum Import

The canonical import manifest is `canonical-roadmap-v1.json`.

It preserves the source map currently available in the project:

- Linux: 9 blocks (`L1`–`L9`), 28 numbered modules and 312 module-hours.
- Linux Lab 0: a separate 6-hour environment lab; it is not counted as a 29th module.
- Networking: 7 phases (`F1`–`F7`), 23 numbered topics and 214 hours.

The import preserves the original sequence, source module identifiers, titles and per-module study-hour estimates. It does not seed competencies, lessons or tickets from module titles alone. Those require a separate content-authoring and validation pass using official documentation and the agreed quality policy.

## Import behavior

`apps/api/app/scripts/seed_curriculum.py` imports the manifest idempotently. It creates or updates version, tracks, blocks and modules without deleting unrelated rows. Existing module authoring status is not reset when the seed script is run again.

The API container receives the manifest as a read-only volume at `/workspace-content/curriculum` during local Compose development. The image also packages a copy for non-development deployments.

## Integrity rules

1. Do not create replacement module IDs, reorder modules, change source titles or invent hours.
2. The Linux Lab 0 remains a lab, not an additional curriculum module.
3. Do not seed unverified modules for Python, Git/GitHub, Cloud, DevOps, DevSecOps or Cloud Security until their canonical source map is available and validated.
4. Every competency must have learning and internship coverage requirements.
5. A competency may be mapped to multiple lessons, labs, tickets and assessments. These mappings are stored in explicit relational association tables.
6. Coverage is not considered verified solely because a record exists. It requires review and evidence; the current local API deliberately does not expose a route to mark coverage as `verified`.

## Primeiro módulo com conteúdo desenvolvido

`linux-l1-m01/` contém a unidade inicial Linux L1 / M1 (Arquitetura e ecossistema): seis aulas, seis competências, dois laboratórios WSL2 seguros, referências oficiais, um ticket simulado e uma avaliação mista. A importação é executada após o mapa canónico e é aditiva. O estado inicial é `draft`; não marca competências como dominadas. Ver `docs/curriculum/linux-l1-m01-architecture.md`.
