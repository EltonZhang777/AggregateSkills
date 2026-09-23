---
name: skill-scout
description: Find installed Agent Skills and prerequisites with the local SkillRoute CLI when a workflow needs skill discovery, comparison, or step-by-step skill routing.
---

# Skill Scout

Use this skill when a workflow needs to find an installed skill, resolve a
skill's prerequisites, compare similar skills, or choose skills for a task.
Return a selection plan to the caller. Do not install, download, or copy a
skill body.

## Source of truth

The local SkillRoute catalog is authoritative. The skills currently in the
agent context are not a complete catalog: metadata may have been omitted to
fit the context budget. Never report a skill as missing only because it is not
already loaded.

Use the local CLI and JSON output:

```text
skillroute --version
skillroute backend status --backend local-token --json
skillroute inspect --json <skill-id>
skillroute search --backend local-token --json <query>
skillroute route --backend local-token --json --repo <repo> <request>
```

Inspect only the exact skill and the shortlisted alternatives. Do not load
every skill's metadata or full body into context.

For each command that requests JSON, accept its response only when it parses
and has the expected
top-level type and required fields. The backend status must be `ready` with a
positive skill count; an inspect result must identify the requested skill; a
search result must be a list of skill records; and a route result must contain
a candidate list and a boolean clarification flag. Treat missing fields,
wrong types, or a mismatched skill identity as an unusable result.

## Workflow

### 1. Check the resolver

Run the version and backend checks before routing. Continue only when the CLI
is runnable, the local backend is ready, and the catalog contains skills for
the request.

If the CLI, backend, or catalog is unavailable, stop with a
`Missing prerequisite` result and state which dependency is unavailable. Tell
the user to install/configure SkillRoute or prepare the local catalog.
`skillroute dogfood roots` may be used to inspect discoverable roots and
`skillroute dogfood index` may be used to prepare the catalog, but do not run
either automatically.

Treat a non-zero exit, malformed JSON, or an unexpected response shape as the
same stopped state. Give the user the relevant installation or catalog
preparation hint. Do not fall back to filesystem scanning, web search, or a
copied skill body.

### 2. Resolve an explicitly named skill

When the user or calling skill names a skill:

1. Inspect that exact name with `skillroute inspect --json`.
2. Use `search` or `route` to find close alternatives for the same request.
3. Compare the exact skill and alternatives by purpose, trigger, prerequisites,
   and relevant evidence.
4. Keep the exact skill when it is available and fits the request.

Never silently replace an explicitly named skill. If it is unavailable, return
`Missing prerequisite`, show the installation/source hint available in the
SkillRoute result, and list alternatives only as suggestions. If it exists but
does not fit the requested work, return `User decision required`, explain the
mismatch, and offer alternatives only as suggestions. Replacing it, combining
it with another skill, or changing the requested workflow requires the user's
decision.
When the result has no source hint, tell the user the named skill is absent
from the prepared local catalog and ask them to make its existing source
discoverable before retrying. `skillroute dogfood roots` can help identify
available roots; indexing remains a user action.

### 3. Resolve an unstated skill

When no skill is named:

1. Split the request into ordered steps, each with one observable outcome.
2. Route each step independently with its step context and repository context.
3. Select a candidate only when exactly one result clearly fits and is locally
   available. A ranked list with multiple plausible matches is not a unique
   result, even when one candidate ranks first.
4. Deduplicate selected skills and preserve prerequisite-before-consumer order.
5. Return the plan before crossing a user-confirmation or external-write gate.

If routing returns clarification questions, competing candidates, or no
candidate, stop at that step and ask the user rather than guessing.
If using the selected skill would add a side effect outside the request or
requires additional permission or confirmation that the user has not granted,
return `User decision required` before that action. Skill Scout only returns a
plan; it does not invoke selected workflows or perform their actions.

### 4. Report the result

Return a compact report containing:

- `Status`: `Ready`, `Needs clarification`, `Missing prerequisite`, or `User decision required`.
- Each task step and its selected skill, if any.
- The reason and SkillRoute evidence for each selection.
- Prerequisites and close alternatives.
- The next skill/action the caller should use after the report.

Preserve every selected skill's own confirmation, authorization, security, and
data-loss safeguards. Skill Scout resolves and explains choices; it does not
grant permission or perform the selected workflow on the user's behalf.

## Hard boundaries

- Use the local SkillRoute backend only; do not access a network backend.
- Do not install, download, index, or modify skills automatically.
- Do not vendor or reproduce a missing skill's instructions.
- Do not claim a skill is missing from context absence alone.
- Do not bypass a clarification or confirmation gate.
