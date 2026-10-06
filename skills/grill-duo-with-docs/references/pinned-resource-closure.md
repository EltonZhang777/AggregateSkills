# Pinned prerequisite resource closure

Read these exact files only when their listed branch applies. The links use the revisions declared by the prerequisite metadata.

- [`/grill-duo` SKILL.md](https://github.com/EltonZhang777/AggregateSkills/blob/9fff1921337c513baefe67a938320f2a1a2b5b98/skills/grill-duo/SKILL.md) — Read to follow the direct `/grill-duo` protocol.
- [`/grilling` SKILL.md](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/productivity/grilling/SKILL.md) — Read through `/grill-duo`; this pinned file links to no additional support files.
- [`/domain-modeling` SKILL.md](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/domain-modeling/SKILL.md) — Read for the target repository's documentation workflow.
- [`GLOSSARY-FORMAT.md`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/domain-modeling/GLOSSARY-FORMAT.md) — Read when writing or updating a glossary after a term is resolved.
- [`ADR-FORMAT.md`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/domain-modeling/ADR-FORMAT.md) — Read only when all three ADR conditions in `/domain-modeling` apply and a decision will be recorded.

The transitive paths are `/grill-duo-with-docs` → `/grill-duo` → `/grilling`, and `/grill-duo-with-docs` → `/domain-modeling` → `GLOSSARY-FORMAT.md` or `ADR-FORMAT.md`. The pinned grilling file adds no outgoing file references; the two format files add no skill edges. The listed graph is acyclic and terminates at these pinned sources.
