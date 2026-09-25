---
name: grill-duo-with-docs
description: "Use when the user explicitly requests two-agent grilling that must maintain confirmed domain language or project decisions. Use `/grill-duo` alone when project-document maintenance is not needed."
metadata:
  prerequisites: '{"skills":[["grill-duo","EltonZhang777/AggregateSkills"],["domain-modeling","mattpocock/skills"]],"mcps":[],"tools":[]}'
---

# `/grill-duo-with-docs`

Use the portable `/grill-duo` protocol with repository-aware documentation maintenance. The host remains the only user-facing agent and the only project-document writer.

## Activation and dependencies

Use this entrypoint when the user explicitly wants a grilling session that records confirmed domain terms or project decisions in project documentation. Use `/grill-duo` when no project-document maintenance is needed.

Before starting, resolve the exact `/grill-duo` and `/domain-modeling` skills through an authoritative, complete skill catalog or runtime, then read their current original SKILL.md files. Use Skill Scout when available; otherwise use the host runtime's complete skill-discovery facility. Do not infer that either dependency is missing from the loaded-skills list alone, and do not vendor or silently replace either skill. If a dependency cannot be resolved, stop and tell the user how to install it:

    npx skills@latest add EltonZhang777/AggregateSkills --skill=grill-duo
    npx skills@latest add mattpocock/skills --skill=domain-modeling

Follow `/grill-duo` for activation, reviewer continuity and boundaries, round IDs, frontier handling, current-request correlation, solo fallback, and final shared-understanding confirmation. Follow the current `/domain-modeling` skill and its referenced materials for glossary and decision discipline. Do not copy either skill's body into this entrypoint.

## Read the repository's documentation map

The host owns documentation context; the reviewer does not read project documentation or its routing rules. The base review request does not require project-document context, so do not include project docs in it.

Before a documentation write, the host reads the active repository's AGENTS.md, its domain-document routing rules, and the applicable glossary/context and relevant decisions. Follow repository-owned routing over generic defaults. If CONTEXT-MAP.md exists, follow it to read the relevant context's CONTEXT.md; otherwise read the root CONTEXT.md. Read relevant docs/adr/ files, plus context-specific docs/adr/ files in a multi-context repository. Also read any architecture, contract, version-decision, or other authoritative files named by repository rules before choosing a destination. If the route is unclear, stop that write and ask the user rather than inventing a file location.

## Record only confirmed content

The host may update documentation as each item is confirmed; it need not wait for the entire grilling session to finish. Before each write:

1. Confirm the specific term or decision came from the user, not from an assumption, an unanswered question, or a reviewer suggestion.
2. Select the authoritative document using the repository's routing rules and the current `/domain-modeling` instructions.
3. Read its latest contents. Apply the confirmed information additively, preserving independent content and deduplicating exact repeats.
4. If the new statement conflicts semantically with existing project knowledge, do not write it or silently choose a side. Show the existing and proposed meanings to the user and pause that documentation decision until it is resolved.

Use CONTEXT.md only as a glossary; keep implementation decisions in the repository's appropriate authoritative documents. Follow the repository's convention for architecture, contract, or version decisions. Create or update an ADR only when the decision is hard to reverse, surprising without context, and a genuine trade-off; follow the repository's ADR format and routing.

Keep unresolved questions, host assumptions, reviewer suggestions, and unverified facts out of project documents. The reviewer must not read or write project documents, choose a destination, or communicate with the user.

When the frontier is empty, summarize the confirmed understanding and the documentation changes, then request the user's final confirmation. Do not begin the underlying implementation before confirmation.