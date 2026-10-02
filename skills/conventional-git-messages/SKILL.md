---
name: conventional-git-messages
description: Draft concise commit, pull request, and issue text without Git or GitHub operations.
metadata:
  prerequisites: '{"skills":[],"mcps":[],"tools":[]}'
---

# /conventional-git-messages

Draft only the commit, pull request, or issue text the user asks for. Never perform a Git operation, create or modify an issue, open or edit a pull request, or post a comment.

For GitHub issue and pull request titles, bodies, and comments, use only the normative language of the repository root AGENTS.md. Pause before drafting if it is mixed with no discernible dominant language. Preserve untouched text when revising, use the root language for new or materially rewritten passages, and report resulting language mixtures. Spelling-only and formatting-only edits and commit messages are excluded.

## Commit subject

- Use `<type>(<scope>): <imperative summary>`; omit the scope when it adds no useful context.
- Supported types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`, `style`, and `revert`.
- For a breaking change, put `!` before the colon, such as `feat(api)!:`.
- Match capitalization after the colon to explicit repository guidance, then recent commit subjects supplied in the context. Ask if the convention is unclear or conflicting. Never run Git commands to inspect history.
- Prefer 50 characters or fewer when the meaning stays clear. Never exceed 72 characters.
- Use an imperative summary and no trailing period.

## Commit body

- Omit the body when the subject fully explains a self-contained change.
- Add only useful, non-obvious rationale, breaking-change context, migration notes, or issue references.
- Always include a body for breaking changes, security fixes, data migrations, and reverts. For breaking changes, explain compatibility impact under `BREAKING CHANGE:` and give the supplied migration path. Preserve supplied impact and migration details; do not invent them.
- Wrap body lines at 72 characters. Use `-` for bullets.
- Put supplied issue or pull request references at the end, for example `Closes #42` or `Refs #17`.
- Do not write filler such as `This commit does`, `I`, `we`, `now`, or `currently`; do not repeat a filename already conveyed by the scope.
- If the user requests co-author credit, use a `Co-authored-by:` trailer instead of prose such as `As requested by...`. Do not invent author details.
- Do not add emoji or AI attribution unless the user or repository rules require it; if required, use the specified trailer.

## Pull request titles

- Use `<type>(<scope>): <imperative summary>` with a supported type listed above; add `!` before the colon for a breaking change, such as `feat(api)!:`. Omit a scope that adds no useful context.
- Put an evidenced repository prefix before the subject as `<prefix>: <type>(<scope>): <imperative summary>`, for example `Release: feat(mail): add retry header`.
- Use an imperative summary and no trailing period. Follow explicit repository capitalization guidance; if none exists, follow consistent same-type PR titles supplied in context. Ask if capitalization is unclear or the examples conflict.
- Add a repository-specific prefix only when repository guidance or same-type pull request titles in the supplied context support it. Clear repository guidance takes precedence over examples. Do not infer a pull request prefix from commit subjects.
- If available prefix evidence conflicts, is stale, or is too sparse to establish the convention, ask a brief question. If no prefix convention is evident, omit the prefix.
- Do not apply commit-specific title-length or body-wrapping limits.

## Pull request descriptions

- Use the shortest useful structure. Add sections only when they clarify the change or the user requests them; do not use a fixed template.
- Do not apply commit-specific title-length or body-wrapping limits.
- In a full description, explain the impact of breaking changes, security fixes, data migrations, and reverts, including supplied migration or mitigation steps. Ask for missing facts instead of inventing them.
- If the user asks for a title only, return only the title.

## Pull request comments

- Draft concise discussion-thread replies from the supplied conversation.
- Draft inline review comments for the specific changed line and context supplied by the user. Do not invent a line or finding.
- Return copy-ready text; never post the comment.

## Issue titles

- Reuse the PR title rules above for the Conventional Commit format, type, scope, breaking `!`, capitalization, imperative summary, and punctuation.
- Resolve issue-title prefixes from explicit repository guidance that applies to issues, then same-type issue titles supplied in context. Do not infer an issue prefix from PR titles or commit subjects.
- Add an issue prefix only when that evidence supports it. If evidence conflicts, is stale, or is too sparse to establish the convention, ask a brief question. If no issue prefix convention is evident, omit it.
- Do not apply commit-specific title-length or body-wrapping limits.

## Issue descriptions

- Use the shortest useful structure for the reported problem and supplied context. Add sections only when they clarify the issue or the user requests them; do not use a fixed template or commit-specific numeric limits.
- In a full description, explain the supplied impact of breaking changes, security fixes, data migrations, and reverts, including relevant mitigation or follow-up. Ask for missing facts instead of inventing them.
- If the user asks for a title only, return only the title.

## Issue comments

- Draft concise comments from the supplied issue discussion.
- Return copy-ready text; never post the comment.

## Optional diagrams

- Consider a diagram only when it materially improves both clarity and concision; diagrams are optional.
- If a needed diagram requires `/skill-scout`, read its current `SKILL.md` regardless of invocation metadata; metadata governs invocation, not source access. Use its local catalog and follow its result, preserving any user-only invocation, confirmation, clarification, or missing-prerequisite gate. Do not install, index, copy, or silently substitute a skill.
- Include only artifacts readers can access directly from the pull request description. Omit inaccessible artifacts; never upload or publish them.

## Output

Return the requested commit message, pull request text, or issue text in a code block ready to paste. If key facts are missing or convention evidence is unclear or conflicting, ask a brief question instead of inventing details.
