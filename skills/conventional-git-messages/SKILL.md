---
name: conventional-git-messages
description: Draft concise commit, pull request, and issue text without Git or GitHub operations.
---

# /conventional-git-messages

## Activation Criteria & Objective

Draft only the commit, pull request, or issue text the user asks for. Never perform a Git operation, create or modify an issue, open or edit a pull request, or post a comment.

For GitHub issue and pull request titles, bodies, and comments, use only the normative prose in the root `AGENTS.md` of the target repository that will own the issue or pull request. If the target differs from this skill's source repository, do not use the source or installation `AGENTS.md` as target policy; if both are the same repository, use its root file as the target policy. Pause before drafting if the target rule has no discernible dominant language. Preserve untouched text when revising, use the target language for new or materially rewritten passages, and report resulting language mixtures. Spelling-only and formatting-only edits and commit messages are excluded.

## Dependencies

If any dependency is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

| Name | Type | Source |
| --- | --- | --- |
| /skill-scout | Skill | https://github.com/EltonZhang777/AggregateSkills |
| SkillRoute CLI | Tool | https://github.com/erichare/skillroute |

## Guidance routes

Read the reference for the requested output and follow its links only for rules
it reuses.

| Request | Trigger | Guidance |
| --- | --- | --- |
| Commit message | The user asks for a commit message. | [Commit messages](references/commit-messages.md) |
| Pull request text | The user asks for a pull request title, description, or comment. | [Pull request text](references/pull-request-text.md) |
| Issue text | The user asks for an issue title, description, or comment. | [Issue text](references/issue-text.md) |

## Output

Return the requested text in a code block ready to paste. If key facts are missing or convention evidence is unclear or conflicting, ask a brief question instead of inventing details.
