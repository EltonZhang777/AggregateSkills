---
name: conventional-git-messages
description: Draft concise commit messages and pull request text; return copy-ready text without Git or pull request operations.
metadata:
  prerequisites: '{"skills":[],"mcps":[],"tools":[]}'
---

# Conventional Git Messages

Draft only the commit or pull request text the user asks for. Never perform
any Git operation, open or edit a pull request, or post a comment.

## Commit subject

- Use `<type>(<scope>): <imperative summary>`; omit the scope when it adds
  no useful context.
- Supported types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`,
  `chore`, `build`, `ci`, `style`, and `revert`.
- For a breaking change, put `!` before the colon, such as `feat(api)!:`.
- Match capitalization after the colon to explicit repository guidance,
  then recent commit subjects supplied in the context. Ask if the convention
  is unclear or conflicting. Never run Git commands to inspect history.
- Prefer 50 characters or fewer when the meaning stays clear. Never exceed
  72 characters.
- Use an imperative summary and no trailing period.

## Commit body

- Omit the body when the subject fully explains a self-contained change.
- Add only useful, non-obvious rationale, breaking-change context, migration
  notes, or issue references.
- Always include a body for breaking changes, security fixes, data migrations,
  and reverts. For breaking changes, explain compatibility impact under
  `BREAKING CHANGE:` and give the supplied migration path. Preserve supplied
  impact and migration details; do not invent them.
- Wrap body lines at 72 characters. Use `-` for bullets.
- Put supplied issue or pull request references at the end, for example
  `Closes #42` or `Refs #17`.
- Do not write filler such as `This commit does`, `I`, `we`, `now`, or
  `currently`; do not repeat a filename already conveyed by the scope.
- If the user requests co-author credit, use a `Co-authored-by:` trailer
  instead of prose such as `As requested by...`. Do not invent author details.
- Do not add emoji or AI attribution unless the user or repository rules
  require it; if required, use the specified trailer.

## Pull request titles

- Use `<type>(<scope>): <imperative summary>` with a supported type listed
  above; add `!` before the colon for a breaking change, such as
  `feat(api)!:`. Omit a scope that adds no useful context.
- Put an evidenced repository prefix before the subject as
  `<prefix>: <type>(<scope>): <imperative summary>`, for example
  `Release: feat(mail): add retry header`.
- Use an imperative summary and no trailing period. Follow explicit
  repository capitalization guidance; if none exists, follow consistent
  same-type PR titles supplied in context. Ask if capitalization is unclear
  or the examples conflict.
- Add a repository-specific prefix only when repository guidance or
  same-type pull request titles in the supplied context support it. Clear
  repository guidance takes precedence over examples. Do not infer a pull
  request prefix from commit subjects.
- If available prefix evidence conflicts, is stale, or is too sparse to
  establish the convention, ask a brief question. If no prefix convention is
  evident, omit the prefix.
- Do not apply commit-specific title-length or body-wrapping limits.

## Pull request descriptions

- Use the shortest useful structure. Add sections only when they clarify the
  change or the user requests them; do not use a fixed template.
- Do not apply commit-specific title-length or body-wrapping limits.
- In a full description, explain the impact of breaking changes, security
  fixes, data migrations, and reverts, including supplied migration or
  mitigation steps. Ask for missing facts instead of inventing them.
- If the user asks for a title only, return only the title.

## Pull request comments

- Draft concise discussion-thread replies from the supplied conversation.
- Draft inline review comments for the specific changed line and context
  supplied by the user. Do not invent a line or finding.
- Return copy-ready text; never post the comment.

## Optional diagrams

- Consider a diagram only when it materially improves both clarity and
  concision; diagrams are optional.
- Resolve a needed diagram step through Skill Scout's local catalog. Follow
  its result and do not bypass a missing-prerequisite or clarification gate.
  Do not install, index, copy, or silently substitute a skill.
- Include only artifacts readers can access directly from the pull request
  description. Omit inaccessible artifacts; never upload or publish them.

## Output

Return the requested title, description, or comment as a code block ready to
paste. If key facts are missing or convention evidence is unclear or
conflicting, ask a brief question instead of inventing details.
