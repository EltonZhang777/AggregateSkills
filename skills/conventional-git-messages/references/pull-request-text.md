# Pull request text

## Pull request drafting

- Use the supplied current diff, target repository's PR title and description guidance, supplied change facts, and supplied recent same-type PR examples when drafting or revising PR titles and bodies. Ask when required facts or prefix conventions are unclear.
- Update existing PR text only when it is inaccurate, materially incomplete, or clearly inconsistent with current repository guidance.

## Pull request titles

- Delegate only type, scope, breaking `!`, imperative summary, and no trailing period to the canonical [Commit subject](commit-messages.md#commit-subject) rules.
- Put an evidenced repository prefix before the subject, for example `Release: feat(mail): add retry header`.
- Follow explicit repository capitalization guidance; if none exists, follow consistent same-type PR titles supplied in context. Do not infer PR-title capitalization from commit subjects. Ask if capitalization is unclear or the examples conflict.
- Add a repository-specific prefix only when explicit PR-title guidance or consistent same-type PR titles supplied in context support it. Clear explicit PR-title guidance takes precedence over examples. Never infer a PR-title prefix from commit subjects.
- If available prefix evidence conflicts, is stale, or is too sparse to establish the convention, ask a brief question. If no prefix convention is evident, omit the prefix.
- Do not apply the canonical commit-subject length limits to PR titles.

## Pull request descriptions

- Before drafting a PR body, check that `/pr` is available; if not, report the missing prerequisite and stop PR-body drafting. When available, invoke it and follow its Summary, Evidence, and Merge Danger template. This gate does not apply to PR titles, PR comments, or other output routes.
- Begin the PR body with all supplied related issue references, before the existing `/pr` Summary, Evidence, and Merge Danger template. Apply the shared issue-reference semantics in [Issue references](issue-references.md) to those issue references. Preserve the template after the reference block.
- Do not apply commit-specific title-length or body-wrapping limits.
- In a full description, explain the impact of breaking changes, security fixes, data migrations, and reverts, including supplied migration or mitigation steps. Ask for missing facts instead of inventing them.
- If the user asks for a title only, return only the title.

## Pull request comments

- Draft concise discussion-thread replies from the supplied conversation.
- Draft inline review comments for the specific changed line and context supplied by the user. Do not invent a line or finding.
- Return copy-ready text; never post the comment.

## Optional diagrams

- Consider a diagram only when it materially improves clarity. Use an accessible `/show-me` or `/archify` skill; if no suitable skill is accessible, follow the shared Optional diagrams guidance to discover one when its gates permit, and omit the diagram if none is accessible.
- When discovery is needed, confirm `/skill-scout` is available before invoking it, then follow `/skill-scout`'s general-host flow with host/caller inventory. Use its SkillRoute local-catalog mode only when the user selects it, and confirm the CLI is available before running it. Follow its missing-prerequisite gates and omit the optional diagram when discovery cannot proceed. Preserve its user-only invocation and confirmation and clarification gates. Do not install, index, copy, or silently substitute a skill.
- Include only artifacts readers can access directly from the PR description; omit inaccessible artifacts and never upload or publish them.
