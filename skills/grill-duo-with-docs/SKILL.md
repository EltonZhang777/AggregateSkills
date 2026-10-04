---
name: grill-duo-with-docs
description: "Use when the user explicitly requests two-agent grilling that must maintain confirmed domain language or project decisions. Use `/grill-duo` alone when project-document maintenance is not needed."
metadata:
  prerequisites: '{"skills":[{"name":"grill-duo","source":"EltonZhang777/AggregateSkills"},{"name":"domain-modeling","source":"mattpocock/skills"}],"mcps":[],"tools":[{"name":"SkillRoute CLI","source":"https://github.com/erichare/skillroute","install":"uv tool install skillroute","setup":"Prepare a local catalog using the SkillRoute documentation","when":"When a prerequisite skill is absent from the available skill list or its exact source cannot be verified."}]}'
---

# /grill-duo-with-docs

Use the portable `/grill-duo` protocol with repository-aware documentation maintenance. The host remains the only user-facing agent and the only project-document writer.

## Activation Criteria & Objective

Use this entrypoint when the user explicitly wants a grilling session that records confirmed domain terms or project decisions in project documentation. Use `/grill-duo` when no project-document maintenance is needed.

## Dependencies

Resolve `/grill-duo` and `/domain-modeling` by exact identity (declared name and source). If no exact name-and-source match appears in the available skill list because the skill is absent or a same-name candidate has a missing, ambiguous, or mismatched source, use the conditional SkillRoute CLI dependency in metadata to verify its identity and source, then read the full original `SKILL.md` from the active skill roots. Read each file regardless of invocation metadata; reading permits source access only. Before invoking a dependency, follow its invocation metadata and preserve all user-confirmation, authorization, and clarification gates; if direct invocation is required, pause at that gate. Record inaccessible sources. If SkillRoute CLI, its catalog, or a required lookup/read operation is unavailable, fails, or returns an unusable result, record the affected dependency as unresolved and report it; do not guess, substitute, or invoke it. Block only work that requires the affected source and continue only independent work. Do not retry in a loop; retry only when the resolver, catalog, or source becomes available or new evidence changes the result. If no independent work remains, pause and report the exact dependency, blocked step, and recovery condition; this pause does not classify the source as missing. Stop the workflow only when a required source is confirmed absent, invalid, or permission-denied, and report its exact identity and source; do not infer or install a replacement.

Follow `/grill-duo` for activation, reviewer continuity and boundaries, round IDs, frontier handling, current-request correlation, solo fallback, and final shared-understanding confirmation. Follow `/domain-modeling` and its referenced materials for glossary and decision discipline. Do not copy either skill's body into this entrypoint.

## Read the repository's documentation map

The host owns documentation context; the reviewer does not read project documentation or its routing rules. The base review request does not require project-document context, so do not include project docs in it.

Before a documentation write, the host reads the target repository's root `AGENTS.md`, its domain-document routing rules, and the applicable glossary/context and relevant decisions. The target is the repository receiving the document. When source and target differ, do not use the source or installation `AGENTS.md` as a substitute; when they are the same repository, the shared root is the target rule. Follow target-repository routing over generic defaults. If `CONTEXT-MAP.md` exists, follow it to read the relevant context's `CONTEXT.md`; otherwise read the root `CONTEXT.md`. Read relevant `docs/adr/` files, plus context-specific `docs/adr/` files in a multi-context repository. Also read any architecture, contract, version-decision, or other authoritative files named by repository rules before choosing a destination. If the route is unclear, stop that write and ask the user rather than inventing a file location.

Before every documentation write, apply the durable-project-text language rule from the target repository's root `AGENTS.md`, using only its normative prose. Pause if the target rule has no discernible dominant language, preserve untouched passages, and report any resulting language mixture. Pass the target rule to `/grill-duo` and `/domain-modeling`; do not modify their external sources.

## Record only confirmed content

The host may update documentation as each item is confirmed; it need not wait for the entire grilling session to finish. Before each write:

1. Confirm the specific term or decision came from the user, not from an assumption, an unanswered question, or a reviewer suggestion.
2. Select the authoritative document using the repository's routing rules and the current `/domain-modeling` instructions.
3. Read its latest contents. Apply the confirmed information additively, preserving independent content and deduplicating exact repeats.
4. If the new statement conflicts semantically with existing project knowledge, do not write it or silently choose a side. Show the existing and proposed meanings to the user and pause that documentation decision until it is resolved.

Use CONTEXT.md only as a glossary; keep implementation decisions in the repository's appropriate authoritative documents. Follow the repository's convention for architecture, contract, or version decisions. Create or update an ADR only when the decision is hard to reverse, surprising without context, and a genuine trade-off; follow the repository's ADR format and routing.

Keep unresolved questions, host assumptions, reviewer suggestions, and unverified facts out of project documents. The reviewer must not read or write project documents, choose a destination, or communicate with the user.

When the frontier is empty, summarize the confirmed understanding and the documentation changes, then request the user's final confirmation. Do not begin the underlying implementation before confirmation.
