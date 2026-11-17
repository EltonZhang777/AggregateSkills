# Release notes

Draft one copy-ready release-notes block from an explicit list of user-supplied
change facts. Draft text only; never perform a Git or GitHub operation, create
a tag, Release, or CHANGELOG entry, or perform release-note publication.

## Inputs

- Require one explicit set of change facts. A fact may include the affected
  users, problem, change, impact, breaking-change details, and deprecation
  details.
- Accept optional product, version, and date metadata only when the user
  supplies it. Do not invent missing metadata.
- Default to general end users. Repository-owned text follows the target
  repository root `AGENTS.md` language rule.
- If the supplied facts do not support a requested statement, ask for the
  missing fact instead of guessing.

## Classification and copy-ready output

Classify each item into exactly one section. Use this section order and
precedence: Breaking Changes, Deprecations, Features, Fixes, Maintenance.
Omit every section without items. Place a performance change under Feature or
Fix according to the supplied effect.

Return the release notes in one fenced `markdown` block.

- Include a level-one title only when the supplied facts support it. Use only
  the supplied product, version, and date fields.
- If a title is present, follow it with a one-to-three-sentence overview
  grounded in the supplied change facts. If no title is present, begin with
  the overview.
- Use compact Problem, Change, and Impact information when the supplied facts
  support each label. Omit the Problem label when no problem is supplied.
- Use one canonical section per item. Do not repeat an item across sections.
- Produce no placeholders or `TBD` markers. Do not use tables or JSON.
- Return text only.

## Example

Supplied facts: the legacy import command is removed; existing automation that
calls it stops working; users must switch to the supported import command. The
user also supplies product Workbench, version 2.4, and date 2026-12-01.

```markdown
# Workbench 2.4 - 2026-12-01

Workbench 2.4 changes how imports are invoked.

## Breaking Changes

- **Legacy import command removed** — Problem: Existing automation can no
  longer call the command it uses today. Change: The legacy import command is
  removed. Impact: Automations that call it stop working and must switch to the
  supported import command before upgrading.
```
