---
name: skill-scout
description: Find skills from the host or caller inventory, with an optional local SkillRoute catalog, for discovery, comparison, and step-by-step routing.
metadata:
  prerequisites: '{"skills":[],"mcps":[],"tools":[{"name":"SkillRoute CLI","source":"https://github.com/erichare/skillroute","install":"uv tool install skillroute","setup":"Prepare a local catalog using the SkillRoute documentation","when":"When the user selects SkillRoute local-catalog mode for discovery or routing."}]}'
---

# /skill-scout

## Activation Criteria & Objective

Use `/skill-scout` when a workflow needs to find an installed skill, resolve a skill's prerequisites, compare similar skills, or choose skills for a task. Return a selection plan to the caller. Do not install, download, or copy a skill body.

## Dependencies

No skill prerequisites are declared. General-host discovery uses the skill inventory exposed by the host or supplied by the caller and does not require SkillRoute. SkillRoute is optional, for a user-selected local-catalog mode. Do not install the CLI or prepare/index a catalog automatically.

## General-host discovery

- Start with an installed-skill inventory exposed by the host or supplied by the caller.
- Treat an inventory as complete only when its source identifies it as covering all installed skills. A partial inventory never proves a skill is absent.
- If exhaustive discovery is needed but the inventory is partial, return `Unavailable` and request a complete inventory or the user's choice to use SkillRoute local-catalog mode.
- Use only the inventory provided for this mode. Do not scan the filesystem, search the web, or use a copied skill body to fill gaps.

## SkillRoute local-catalog mode

This optional local-catalog mode runs only when the user selects SkillRoute. It reads the local catalog only; it does not use a network backend.

Run the CLI and backend checks before routing:

```text
skillroute --version
skillroute backend status --backend local-token --json
skillroute inspect --json <skill-id>
skillroute search --backend local-token --json <query>
skillroute route --backend local-token --json --repo <repo> <request>
```

Accept JSON only when it parses and has the expected type and required fields: backend status is `ready` with a positive skill count; inspect identifies the requested skill; search returns a list of skill records; route returns candidates and a boolean clarification flag. Missing fields, wrong types, mismatched identity, or malformed output are unusable.

If the CLI, local backend, or catalog is unavailable, return `Unavailable` and name the missing part. Do not present the result as evidence that a skill is absent. Give the relevant install or catalog-preparation step, but do not perform it. The user may inspect discoverable roots with `skillroute dogfood roots` or prepare a catalog with `skillroute dogfood index`; ask before running either command. For temporary resolver or backend errors or unusable output, return an `Unresolved prerequisite` result, identify the exact failed check and recovery condition, and stop. Do not fall back to filesystem scanning, web search, a copied skill body, or another discovery source.

## Source and selection safety

### Resolve an explicitly named skill

When the user or calling skill names a skill:

1. Check the exact name in the selected inventory. In SkillRoute mode, use `skillroute inspect --json`; otherwise use the host or caller-provided metadata.
2. Compare the exact skill and close alternatives by purpose, trigger, prerequisites, and relevant evidence.
3. Keep the exact skill when it is available and fits the request.

Treat a supplied source as part of the identity; a same-name entry from another source is not a match. If no source is supplied, select by exact name only when one inventory entry matches. If multiple entries match, return `User decision required`, show each candidate and its declared or undeclared source, and ask which to use. Do not choose by inventory order or rank.

Never silently replace an explicitly named skill. If a complete inventory does not contain it, return `Missing prerequisite`, show the evidence and any source hint, and list alternatives only as suggestions. If the inventory is partial, return `Unavailable`; absence cannot be confirmed. A source hint alone does not prove absence. If reading a required source fails temporarily or evidence is inconclusive, return `Unresolved prerequisite` with the failed check and recovery condition. If the skill exists but does not fit, return `User decision required` and explain the mismatch. Replacing or combining it requires the user's decision.

### Resolve an unstated skill

When no skill is named:

1. Split the request into ordered steps, each with one observable outcome.
2. Search or route each step against the selected inventory using its purpose, trigger, and repository context. Use SkillRoute `route` only in local-catalog mode.
3. Select a candidate only when exactly one result clearly fits and is available. A ranked list with multiple plausible matches is not unique.
4. If prerequisite metadata is missing from the inventory, read the selected skill's exact source. Resolve each declared prerequisite by exact name and source; deduplicate selections and preserve prerequisite-before-consumer order.
5. Return `Unavailable` when a partial inventory prevents exhaustive routing. If routing needs clarification, has competing candidates, or finds no candidate in a complete inventory, ask rather than guess.
6. Return the plan before crossing a user-confirmation or external-write gate.

Invocation metadata controls who may invoke a skill; it does not block read-only access to its `SKILL.md`. When a workflow needs a prerequisite's source, read the original file regardless of its model-invocation metadata. Preserve that skill's user-only invocation, confirmation, and authorization gates before invoking it or taking action. If a selected workflow adds an unapproved side effect or needs additional permission, return `User decision required`. `/skill-scout` reports a plan; it does not invoke selected workflows or perform their actions.

## Report

Return a compact report with:

- `Status`: `Ready`, `Needs clarification`, `Unresolved prerequisite`, `Missing prerequisite`, `User decision required`, or `Unavailable`.
- `Inventory`: source and scope, including whether it is complete.
- Each task step and selected skill, if any, with the reason, source, and evidence.
- Prerequisites, close alternatives, and the next skill/action for the caller.

Preserve every selected skill's confirmation, authorization, security, and data-loss safeguards. `/skill-scout` does not grant permission.

## Hard boundaries

- Use the local SkillRoute backend only; do not access a network backend.
- Keep installation, catalog indexing, and skill changes under user control.
- Do not vendor or reproduce a missing skill's instructions.
- Treat the current agent context as partial; claim absence only from a complete inventory.
- Preserve each selected skill's clarification, confirmation, authorization, security, and data-loss gates.
- Do not install, download, index, or modify skills automatically.
- Do not bypass a clarification or confirmation gate.
