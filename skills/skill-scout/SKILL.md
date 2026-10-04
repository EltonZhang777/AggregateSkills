---
name: skill-scout
description: Find installed Agent Skills and prerequisites with the local SkillRoute CLI when a workflow needs skill discovery, comparison, or step-by-step skill routing.
metadata:
  prerequisites: '{"skills":[],"mcps":[],"tools":[{"name":"SkillRoute CLI","source":"https://github.com/erichare/skillroute","install":"uv tool install skillroute","setup":"Prepare a local catalog using the SkillRoute documentation"}]}'
---

# /skill-scout

## Activation Criteria & Objective

Use `/skill-scout` when a workflow needs to find an installed skill, resolve a skill's prerequisites, compare similar skills, or choose skills for a task. Return a selection plan to the caller. Do not install, download, or copy a skill body.

## Dependencies

No skill prerequisites are declared. The SkillRoute CLI from `https://github.com/erichare/skillroute` is required to run this skill. Install it with `uv tool install skillroute` and prepare a local catalog using the SkillRoute documentation. If the CLI or catalog is confirmed absent, invalid, or permission-denied, report `Missing prerequisite`. If a check fails without confirming one of those conditions, or its result is inconclusive, stop with an `Unresolved prerequisite` result and report the failed check and recovery condition. Do not install the CLI or index roots automatically.

## Source of truth

The local SkillRoute catalog is authoritative. The skills currently in the agent context are not a complete catalog: metadata may have been omitted to fit the context budget. Never report a skill as missing only because it is not already loaded.

Invocation metadata controls who may invoke a skill; it does not block read-only access to its `SKILL.md`. When a workflow needs a prerequisite's source, read the original file regardless of its model-invocation metadata. Preserve the prerequisite's user-only invocation, confirmation, and authorization gates before invoking it or taking action.

Use the local CLI and JSON output:

```text
skillroute --version
skillroute backend status --backend local-token --json
skillroute inspect --json <skill-id>
skillroute search --backend local-token --json <query>
skillroute route --backend local-token --json --repo <repo> <request>
```

Inspect only the exact skill and the shortlisted alternatives. Do not load every skill's metadata or full body into context.

For each command that requests JSON, accept its response only when it parses and has the expected top-level type and required fields. The backend status must be `ready` with a positive skill count; an inspect result must identify the requested skill; a search result must be a list of skill records; and a route result must contain a candidate list and a boolean clarification flag. Treat missing fields, wrong types, or a mismatched skill identity as an unusable result.

## Workflow

### 1. Check the resolver

Run the version and backend checks before routing. Continue only when the CLI is runnable, the local backend is ready, and the catalog contains skills for the request.

If a check confirms that the CLI or catalog is absent, invalid, or permission-denied, stop with a `Missing prerequisite` result. State the evidence and give the relevant installation or catalog preparation hint. Do not install the CLI or prepare the catalog automatically.

For temporary resolver or backend errors, non-zero exits without evidence of confirmed absence, malformed JSON, unexpected response shapes, or other inconclusive results, stop with an `Unresolved prerequisite` result. Report the exact failed check and recovery condition; do not treat the failure as proof that the dependency is missing. Do not fall back to filesystem scanning, web search, or a copied skill body.

### 2. Resolve an explicitly named skill

When the user or calling skill names a skill:

1. Inspect that exact name with `skillroute inspect --json`.
2. Use `search` or `route` to find close alternatives for the same request.
3. Compare the exact skill and alternatives by purpose, trigger, prerequisites, and relevant evidence.
4. Keep the exact skill when it is available and fits the request.

Never silently replace an explicitly named skill. If SkillRoute confirms that the skill or its source is absent, invalid, or permission-denied, return `Missing prerequisite`, show the evidence and available installation/source hint, and list alternatives only as suggestions. If lookup or source reading fails temporarily, or the result does not confirm absence, return `Unresolved prerequisite` with the exact failed check and recovery condition. A missing source hint alone does not prove absence. If the skill exists but does not fit the requested work, return `User decision required`, explain the mismatch, and offer alternatives only as suggestions. Replacing it, combining it with another skill, or changing the requested workflow requires the user's decision. `skillroute dogfood roots` can help identify available roots; indexing remains a user action.

### 3. Resolve an unstated skill

When no skill is named:

1. Split the request into ordered steps, each with one observable outcome.
2. Route each step independently with its step context and repository context.
3. Select a candidate only when exactly one result clearly fits and is locally available. A ranked list with multiple plausible matches is not a unique result, even when one candidate ranks first.
4. Deduplicate selected skills and preserve prerequisite-before-consumer order.
5. Return the plan before crossing a user-confirmation or external-write gate.

If routing returns clarification questions, competing candidates, or no candidate, stop at that step and ask the user rather than guessing. If using the selected skill would add a side effect outside the request or requires additional permission or confirmation that the user has not granted, return `User decision required` before that action. `/skill-scout` only returns a plan; it does not invoke selected workflows or perform their actions.

### 4. Report the result

Return a compact report containing:

- `Status`: `Ready`, `Needs clarification`, `Unresolved prerequisite`, `Missing prerequisite`, or `User decision required`.
- Each task step and its selected skill, if any.
- The reason and SkillRoute evidence for each selection.
- Prerequisites and close alternatives.
- The next skill/action the caller should use after the report.

Preserve every selected skill's own confirmation, authorization, security, and data-loss safeguards. `/skill-scout` resolves and explains choices; it does not grant permission or perform the selected workflow on the user's behalf.

## Hard boundaries

- Use the local SkillRoute backend only; do not access a network backend.
- Do not install, download, index, or modify skills automatically.
- Do not vendor or reproduce a missing skill's instructions.
- Do not claim a skill is missing from context absence alone.
- Do not bypass a clarification or confirmation gate.
