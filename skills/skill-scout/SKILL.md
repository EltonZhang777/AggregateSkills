---
name: skill-scout
description: Find suitable installed Agent Skills from the host's available inventory, with optional SkillRoute support for local-catalog discovery and routing.
metadata:
  prerequisites: '{"skills":[],"mcps":[],"tools":[["SkillRoute CLI","https://github.com/erichare/skillroute","uv tool install skillroute","Prepare a local catalog using the SkillRoute documentation"]]}'
---

# /skill-scout

Use `/skill-scout` when a workflow needs to find an installed skill, resolve prerequisites, compare similar skills, or choose skills for a task. Return a selection plan to the caller. The selected skill's own instructions govern any later work.

## General-host discovery

Start with an installed-skill inventory exposed by the host or supplied by the caller. Use its names, descriptions, and prerequisite metadata to find candidates. Treat an inventory as complete only when its source identifies it as covering all installed skills; the skills in the agent's current context are a partial view.

Read source instructions only for the exact skill and shortlisted alternatives. Invocation metadata controls who may invoke a skill; it does not block read-only access to its `SKILL.md`. Preserve each prerequisite's user-only invocation, confirmation, and authorization gates.

If no complete inventory is available, describe only the skills visible in the available sources. When the requested decision requires exhaustive host-wide discovery, return `Unavailable`, state which inventory is missing, and ask the user to provide one or choose local SkillRoute discovery. A partial inventory never proves a skill is absent.

## SkillRoute local-catalog mode

Use this mode when the user requests SkillRoute, needs its prepared local catalog or routing behavior, or chooses it after general-host discovery is unavailable. SkillRoute is an optional local tool for this workflow; it does not define a general Agent Skills host API.

Run the version and backend checks before a SkillRoute query. Continue only when the CLI is runnable, the local backend is ready, and the catalog contains skills:

```text
skillroute --version
skillroute backend status --backend local-token --json
skillroute inspect --json <skill-id>
skillroute search --backend local-token --json <query>
skillroute route --backend local-token --json --repo <repo> <request>
```

For each command that requests JSON, require valid JSON with the expected fields: backend status `ready` and a positive skill count; an inspect result identifying the requested skill; a search result containing a list of skill records; and a route result containing a candidate list and boolean clarification flag. Missing fields, wrong types, or a mismatched skill identity make that result unusable.

If the CLI, local backend, or catalog is unavailable, return `Unavailable` and name the missing part. Explain that SkillRoute CLI installation and local catalog preparation are required for this mode; do not present the result as evidence that a skill is absent. The user may inspect discoverable roots with `skillroute dogfood roots` or prepare a catalog with `skillroute dogfood index`; ask before running either command. Do not switch to filesystem scanning, web search, or a copied skill body.

## Workflow

### Resolve an explicitly named skill

When the user or calling skill names a skill:

1. Check the exact name in the selected inventory. In SkillRoute mode, use `skillroute inspect --json`; otherwise use the host or caller-provided metadata.
2. Compare the exact skill and close alternatives by purpose, trigger, prerequisites, and relevant evidence.
3. Keep the exact skill when it is available and fits the request.

Never silently replace an explicitly named skill. If a complete inventory does not contain it, return `Missing prerequisite`, say it was not found in that inventory, and give any available source hint; list alternatives only as suggestions. If the inventory is partial, return `Unavailable` because absence cannot be confirmed. If the skill exists but does not fit the requested work, return `User decision required` and explain the mismatch. Replacing it, combining it with another skill, or changing the requested workflow requires the user's decision.

### Resolve an unstated skill

When no skill is named:

1. Split the request into ordered steps, each with one observable outcome.
2. Search the selected inventory for each step using its purpose, trigger, and repository context. Use SkillRoute `route` only in local-catalog mode.
3. Select a candidate only when exactly one result clearly fits and is locally available. A ranked list with multiple plausible matches is not a unique result, even when one candidate ranks first.
4. Read the selected skill's exact source when its prerequisite metadata is missing from the inventory. Resolve each declared skill prerequisite by exact name and source, deduplicate selections, and preserve prerequisite-before-consumer order.
5. Return the plan before crossing a user-confirmation or external-write gate.

If a required prerequisite is absent from a complete inventory, return `Missing prerequisite` with its exact name and any supplied source hint. If the inventory is partial, return `Unavailable` for that step. If search returns clarification questions, competing candidates, or no candidate in a complete inventory, stop at that step and ask the user. If using a selected skill would add a side effect outside the request or needs permission the user has not granted, return `User decision required`. `/skill-scout` returns a plan; it does not invoke selected workflows or perform their actions.

### 4. Report the result

Return a compact report containing:

- `Status`: `Ready`, `Needs clarification`, `Missing prerequisite`, `User decision required`, or `Unavailable`.
- `Inventory`: source and scope, including whether it is complete.
- Each task step and its selected skill, if any.
- The reason and SkillRoute evidence for each selection.
- Prerequisites and close alternatives.
- The next skill/action the caller should use after the report.

Preserve every selected skill's own confirmation, authorization, security, and data-loss safeguards. `/skill-scout` resolves and explains choices; it does not grant permission or perform the selected workflow on the user's behalf.

## Hard boundaries

- Use the local SkillRoute backend only; do not access a network backend.
- Keep installation, catalog indexing, and skill changes under user control.
- Do not vendor or reproduce a missing skill's instructions.
- Treat the current agent context as partial; claim absence only from a complete inventory.
- Preserve each selected skill's clarification, confirmation, authorization, security, and data-loss gates.
