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

If the CLI, local backend, or catalog is unavailable, return `Unavailable`; do not present the result as evidence that a skill is absent. Give the relevant install or catalog-preparation step, but do not perform it. For temporary resolver or backend errors or unusable output, return an `Unresolved prerequisite` result, identify the exact failed check and recovery condition, and stop. Do not fall back to another discovery source.

## Source and selection safety

Invocation metadata controls who may invoke a skill; it does not block read-only access to its `SKILL.md`. When a workflow needs a prerequisite's source, read the original file regardless of its model-invocation metadata. Preserve that skill's user-only invocation, confirmation, and authorization gates before invoking it or taking action.

### Resolve an explicitly named skill

Check the exact name in the selected inventory. If it is present, inspect its original source and keep it when it fits. Never silently replace an explicitly named skill.

Treat a supplied source as part of the identity; a same-name entry from another source is not a match. If no source is supplied, select by exact name only when one inventory entry matches. If multiple entries match, return `User decision required`, show each candidate and its declared or undeclared source, and ask which to use. Do not choose by inventory order or rank.

- If a complete inventory does not contain it, return `Missing prerequisite` and show the evidence and any source hint. If the inventory is partial, return `Unavailable`; absence is unproven.
- A source hint alone does not prove absence. If source reading fails temporarily or evidence is inconclusive, return `Unresolved prerequisite` with the failed check and recovery condition. Use `Missing prerequisite` only when absence, invalidity, or permission denial is confirmed.
- If the skill exists but does not fit, return `User decision required` and explain the mismatch. Alternatives are suggestions; replacing or combining the requested skill requires the user's decision.

### Resolve an unstated skill

1. Split the request into ordered steps, each with one observable outcome.
2. Route each step independently against the selected inventory and repository context.
3. Select a skill only when exactly one candidate clearly fits and is available. A ranked list with multiple plausible candidates is not a unique result.
4. If a partial inventory prevents exhaustive routing, return `Unavailable`; do not treat its candidate list as complete.
5. Deduplicate selections and preserve prerequisite-before-consumer order.
6. Return the plan before crossing a user-confirmation or external-write gate.

If routing needs clarification or has competing candidates, ask the user rather than guessing. If a selected workflow adds an unapproved side effect or requires additional permission, return `User decision required`. `/skill-scout` reports a plan; it does not invoke selected workflows or perform their actions.

## Report

Return a compact report with:

- `Status`: `Ready`, `Needs clarification`, `Unresolved prerequisite`, `Missing prerequisite`, `User decision required`, or `Unavailable`.
- Each task step and selected skill, if any, with the inventory source and evidence.
- Prerequisites, close alternatives, and the next skill/action for the caller.

Preserve every selected skill's confirmation, authorization, security, and data-loss safeguards. `/skill-scout` does not grant permission.

## Hard boundaries

- Do not install, download, index, or modify skills automatically.
- Do not vendor or reproduce a missing skill's instructions.
- Do not claim a skill is missing from context absence or a partial inventory alone.
- Do not bypass a clarification or confirmation gate.
