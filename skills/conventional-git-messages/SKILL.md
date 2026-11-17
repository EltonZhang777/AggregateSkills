---
name: conventional-git-messages
description: Draft concise commit, pull request, issue, and release-note text without Git or GitHub writes.
---

# /conventional-git-messages

## Activation Criteria & Objective

Draft only the commit, pull request, issue, or release-note text the user asks for. Only release-notes drafting may inspect Git or GitHub, and only when the user explicitly authorizes read-only evidence inspection for a named repository and release scope. Do not inspect repository or tracker state otherwise. Never stage, commit, or push. Do not create a tag, GitHub Release, or CHANGELOG entry; write an issue or pull request; change authentication; post a comment; or publish.

For GitHub issue and pull request titles, bodies, and comments, use only the normative prose in the root `AGENTS.md` of the target repository that will own the issue or pull request. If the target differs from this skill's source repository, do not use the source or installation `AGENTS.md` as target policy; if both are the same repository, use its root file as the target policy. Pause before drafting if the target rule has no discernible dominant language. Preserve untouched text when revising, use the target language for new or materially rewritten passages, and report resulting language mixtures. Spelling-only and formatting-only edits and commit messages are excluded.

## Dependencies

When this skill's own workflow explicitly reaches a call to one of its directly declared Skill prerequisites, the call is explicit and may proceed even if that prerequisite disables implicit invocation. This waives only that invocation gate. It does not waive other prerequisite instructions or confirmation, authorization, security, or safety gates. It does not authorize transitive calls, create new call steps, or override an explicit prohibition on invoking another skill.

If any dependency is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

| Name | Type | Source |
| --- | --- | --- |
| /pr | Skill | https://github.com/mattpocock/skills |
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
| Release notes | The user asks for release notes from supplied facts or authorized read-only evidence. | [Release notes](references/release-notes.md) |

## Output

Return the requested text in a code block ready to paste. When the selected guidance requires supplementary output, return that outside the code block as specified. If key facts are missing or convention evidence is unclear or conflicting, ask a brief question instead of inventing details.
