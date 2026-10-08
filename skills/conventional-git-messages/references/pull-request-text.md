# Pull request text

## Pull request drafting

- Use the current diff, target repository's PR title and description guidance, supplied change facts, and recent same-type PR examples when drafting or revising PR titles and bodies. Ask when required facts or prefix conventions are unclear.
- Update existing PR text only when it is inaccurate, materially incomplete, or clearly inconsistent with current repository guidance.

## Pull request titles

- Use `<type>(<scope>): <imperative summary>` with a supported type listed in [Commit subject](commit-messages.md#commit-subject); add `!` before the colon for a breaking change, such as `feat(api)!:`. Omit a scope that adds no useful context.
- Put an evidenced repository prefix before the subject as `<prefix>: <type>(<scope>): <imperative summary>`, for example `Release: feat(mail): add retry header`.
- Use an imperative summary and no trailing period. Follow explicit repository capitalization guidance; if none exists, follow consistent same-type PR titles supplied in context. Ask if capitalization is unclear or the examples conflict.
- Add a repository-specific prefix only when repository guidance or same-type pull request titles in the supplied context support it. Clear repository guidance takes precedence over examples. Do not infer a pull request prefix from commit subjects.
- If available prefix evidence conflicts, is stale, or is too sparse to establish the convention, ask a brief question. If no prefix convention is evident, omit the prefix.
- Do not apply commit-specific title-length or body-wrapping limits.

## Pull request descriptions

- Invoke `/pr` before drafting any PR body and follow its Summary, Evidence, and Merge Danger template.
- Do not apply commit-specific title-length or body-wrapping limits.
- In a full description, explain the impact of breaking changes, security fixes, data migrations, and reverts, including supplied migration or mitigation steps. Ask for missing facts instead of inventing them.
- If the user asks for a title only, return only the title.

## Pull request comments

- Draft concise discussion-thread replies from the supplied conversation.
- Draft inline review comments for the specific changed line and context supplied by the user. Do not invent a line or finding.
- Return copy-ready text; never post the comment.

## Optional diagrams

- Consider a diagram only when it materially improves clarity. Use an accessible `/show-me` or `/archify` skill; if no suitable skill is accessible, follow the shared Optional diagrams guidance to discover one when its gates permit, and omit the diagram if none is accessible.
- When discovery is needed, follow `/skill-scout`'s general-host flow with host/caller inventory. Use its SkillRoute local-catalog mode only when the user selects it. Preserve its user-only invocation, confirmation, clarification, and missing-prerequisite gates. Do not install, index, copy, or silently substitute a skill.
- Include only artifacts readers can access directly from the PR description; omit inaccessible artifacts and never upload or publish them.
