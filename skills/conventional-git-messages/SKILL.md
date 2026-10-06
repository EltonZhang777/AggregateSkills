---
name: conventional-git-messages
description: Draft concise commit, pull request, and issue text without Git or GitHub operations.
metadata:
  prerequisites: '{"skills":[{"name":"skill-scout","source":"EltonZhang777/AggregateSkills","when":"When a requested diagram requires skill discovery.","source_url":"https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/skill-scout","install":"npx skills@latest add https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/skill-scout"}],"mcps":[],"tools":[{"name":"SkillRoute CLI","source":"https://github.com/erichare/skillroute","install":"uv tool install skillroute","setup":"Prepare a local catalog using the SkillRoute documentation","when":"When a prerequisite skill is absent from the available skill list or its exact source cannot be verified."}]}'
---

# /conventional-git-messages

## Activation Criteria & Objective

Draft only the commit, pull request, or issue text the user asks for. Never perform a Git operation, create or modify an issue, open or edit a pull request, or post a comment.

For GitHub issue and pull request titles, bodies, and comments, use only the normative prose in the root `AGENTS.md` of the target repository that will own the issue or pull request. If the target differs from this skill's source repository, do not use the source or installation `AGENTS.md` as target policy; if both are the same repository, use its root file as the target policy. Pause before drafting if the target rule has no discernible dominant language. Preserve untouched text when revising, use the target language for new or materially rewritten passages, and report resulting language mixtures. Spelling-only and formatting-only edits and commit messages are excluded.

Treat a missing or unreadable target `AGENTS.md` as a missing-input condition: ask the user to provide the target's prose policy and pause drafting until it is available.
## Dependencies

Resolve and read the original `SKILL.md` for each direct skill declared in this file's `metadata.prerequisites.skills` array by exact identity (declared name and source). If no exact name-and-source match appears in the available skill list because the skill is absent or a same-name candidate has a missing, ambiguous, or mismatched source, use the conditional SkillRoute CLI dependency in metadata to verify its identity and source, then read the full original file from the active skill roots. Read it regardless of invocation metadata; reading permits source access only. Before invoking the dependency, follow its invocation metadata and preserve all user-confirmation, authorization, and clarification gates; if direct invocation is required, pause at that gate. Record inaccessible sources. If SkillRoute CLI, its catalog, or a required lookup/read operation is unavailable, fails, or returns an unusable result, record the affected dependency as unresolved and report it; do not guess, substitute, or invoke it. Block only work that requires the affected source and continue only independent work. Do not retry in a loop; retry only when the resolver, catalog, or source becomes available or new evidence changes the result. If no independent work remains, pause and report the exact dependency, blocked step, and recovery condition; this pause does not classify the source as missing. Stop the workflow only when the required source is confirmed absent, invalid, or permission-denied, and report its exact identity and source; do not infer or substitute another skill.

The /skill-scout prerequisite is needed only when a requested diagram requires skill discovery. The conditional SkillRoute CLI tool is only for verifying that prerequisite's identity and source.

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
- For a diagram, use an accessible artifact supplied by the user or created with an available host capability. If neither is available, omit the optional diagram; the copy-ready text remains the complete deliverable.
- When a needed diagram requires skill discovery, follow `/skill-scout`'s general-host flow with host/caller inventory. Use its SkillRoute local-catalog mode only when the user selects it. Preserve its user-only invocation, confirmation, clarification, and missing-prerequisite gates. Do not install, index, copy, or silently substitute a skill.
- Include only artifacts readers can access directly from the pull request description. Omit inaccessible artifacts; never upload or publish them.

## Output

Return the requested commit message, pull request text, or issue text in a code block ready to paste. If key facts are missing or convention evidence is unclear or conflicting, ask a brief question instead of inventing details.
