---
name: grill-duo-with-docs
description: "Use when the user explicitly requests two-agent grilling that must maintain confirmed domain language or project decisions. Use `/grill-duo` alone when project-document maintenance is not needed."
---

# /grill-duo-with-docs

Use the portable `/grill-duo` protocol with repository-aware documentation maintenance. The host remains the only user-facing agent and the only project-document writer.

## Activation Criteria & Objective

Use this entrypoint when the user explicitly wants a grilling session that records confirmed domain terms or project decisions in project documentation. Use `/grill-duo` when no project-document maintenance is needed.

Use `/grill-duo` for the grilling protocol and use `/domain-modeling` for glossary and decision discipline. Do not copy either skill's body into this entrypoint.

## Dependencies

If any dependency is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

| Name | Type | Source |
| --- | --- | --- |
| /grill-duo | Skill | https://github.com/EltonZhang777/AggregateSkills |
| /domain-modeling | Skill | https://github.com/mattpocock/skills |
| SkillRoute CLI | Tool | https://github.com/erichare/skillroute |

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

Keep unresolved questions, host assumptions, reviewer suggestions, and unverified facts out of project documents. The reviewer must not read or write project documents, choose a destination, or communicate with the user.

When the frontier is empty, summarize the confirmed understanding and the documentation changes, then request the user's final confirmation. Do not begin the underlying implementation before confirmation.
