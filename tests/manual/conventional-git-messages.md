# `conventional-git-messages` manual scenarios

Run these through the user-visible skill invocation. Supply each scenario's
change context and any repository rules or examples it names. Inspect the
returned text and confirm no Git operation runs.

## Conventional subject and useful body

Ask for a commit message for a new `GET /users/:id/profile` endpoint. Supply
the rationale that the mobile client needs profile data without the full
user payload, plus `Closes #128`. Supply project guidance that summaries use
lowercase after the colon and a recent lowercase commit subject as context.

Confirm:

- The subject uses `feat(api):` and an imperative, lowercase summary without
  a trailing period.
- The subject is concise (preferably at or below 50 characters) and never
  exceeds 72 characters.
- The body contains the useful rationale, wraps at 72 columns, and ends with
  `Closes #128`.

## Conflicting capitalization examples

Supply two recent commit subjects with conflicting capitalization after the
colon, and no explicit project rule. Ask for a commit message.

Confirm the skill asks which convention to use instead of guessing.

## Subject length limits

Ask for a subject for a change that adds tenant-specific configurable
retention windows for archived transfer bundles. Explicitly request an
80-character subject.

Confirm the skill preserves the essential meaning but keeps the subject at
or below 72 characters. It may exceed 50 when shortening further would make
the meaning unclear; otherwise it prefers 50 or fewer.

## Self-explanatory change

Ask for a commit message for a small parser change that rejects empty input
generally, with no subsystem scope that adds useful context.

Confirm the skill omits the scope and body, returning a concise subject such
as `fix: reject empty input`.

## Mandatory body cases

Run once for each supplied change: a breaking API change, a security fix,
a data migration, and a revert. Provide the concrete impact and required
follow-up for each.

Confirm every result has a body that preserves that context, even when the
subject seems sufficient. For the breaking change, include a
`BREAKING CHANGE:` explanation. Do not invent facts.

## Existing body and trailer rules

Ask for a commit message with a multi-line rationale, a supplied issue
reference, and a supplied co-author. Use enough rationale to require wrapping.

Confirm body lines wrap at 72 columns, bullets use `-`, issue references
appear in the trailing trailer block, and requested co-author credit uses a
`Co-authored-by:` trailer. Do not add emoji, AI attribution, filler, or
filenames already conveyed by the scope.

## Missing context and operation boundary

Ask for a security-fix message without enough information to describe the
impact, and ask the skill to commit it after drafting.

Confirm the skill asks a brief question instead of inventing facts, drafts
text only, and performs no staging, commit, amend, push, or other Git
operation.

## Pull request title conventions

Ask for a pull request title for adding a retry header to email delivery.
Supply repository guidance that PR titles use the `Release:` prefix and
lowercase summaries, plus the same-type PR title
`Task: feat(mail): add retry header`. Also supply the commit subject
`Fix: add retry header`.

Confirm the title follows the PR guidance and Conventional Commit subject
format, with a supported type, useful scope, imperative lowercase summary,
and no trailing period. The explicit guidance wins over the conflicting PR
example; do not borrow the prefix from the commit subject.

Then provide these two recent PR titles with a consistent `Work:` prefix and
no explicit repository rule:

- `Work: feat(mail): add retry header`
- `Work: feat(mail): retry transient sends`

Confirm the skill infers that prefix and places it before the Conventional
Commit subject as `Work: feat(mail): ...`.

Then ask for a PR title with no applicable prefix guidance or examples.
Confirm the title uses the Conventional Commit subject without a prefix.

Ask for a title with no repository rule and only this same-type example from
an archived release project three years ago: `Legacy: feat(mail): add retry
header`. Confirm the skill asks whether the old prefix still applies instead
of assuming it is current.

Ask for a title for a breaking API change. Confirm the Conventional Commit
subject marks it with `!` before the colon, such as `feat(api)!: remove the
legacy field`.

## Conflicting PR title examples

Supply these same-type PR titles with different prefixes and no explicit
repository rule:

- `Release: feat(mail): add retry header`
- `Work: feat(mail): retry transient sends`

Ask for a new PR title.

Confirm the skill asks which convention to use rather than guessing.

## Pull request descriptions

Ask for a concise PR description for a small fix, supplying the change and
its non-obvious rationale. Include this 100-plus-character fact:
`The worker resumes partially uploaded bundles after a transient restart so
callers do not need to resend the complete archive.` Request the shortest
useful structure.

Confirm it has no mandatory headings and does not apply commit-only title
limits or 72-column body wrapping. Preserve the complete supplied rationale
without truncating it at a commit-message limit.

Then make an explicit title-only request for the same change. Confirm the
skill returns only a title, with no description.

## Full descriptions for important changes

Run once each for a breaking change, a security fix, a data migration, and a
revert. Supply the concrete impact and any required migration or mitigation
steps.

Confirm each full description explains the supplied impact and follow-up
without inventing missing details. An explicit title-only request still
returns only a title.

Ask for a full description for a security fix, providing only that it fixes
an authentication vulnerability. Do not provide affected versions, impact,
or mitigation. Confirm the skill asks for the missing facts and does not
invent them.

## Pull request comments

Draft a discussion reply to this thread:

- Reviewer: `Why does this stop after three delivery attempts?`
- Author: `The provider contract allows at most three attempts; more can
  create duplicate sends.`

Then draft an inline review comment on the changed line
`if (attempts >= 3) return failure;`, using the supplied fact that the
provider permits at most three attempts.

Confirm both are concise and copy-ready, the inline comment addresses the
supplied line, and neither comment invents facts or is posted.

## Optional diagrams and operation boundary

Ask for a PR description for a simple one-line fix, then for a complex flow
whose relationships are clearer in a diagram.

Confirm no diagram is added to the simple description. Use show-me or
archify only if a diagram materially improves both clarity and concision; do
not resolve a diagram skill for the simple fix. For the complex flow, resolve
the step through Skill Scout. Confirm a unique available match is required,
and that a missing prerequisite stops with that result while ambiguous
resolution asks for clarification; neither gate is bypassed.

For the complex flow, provide a diagram result at a local-only path that PR
readers cannot access.

Confirm the inaccessible artifact is omitted and no upload or publication
is attempted.

Ask the skill to open a PR and post one of the drafted comments.

Confirm it returns drafts only and performs no Git, PR, or comment operation.

## Issue title conventions

Ask for an issue title for adding a retry header to email delivery. Supply
repository guidance that issue titles use the `Ticket:` prefix and lowercase
summaries, plus the same-type issue title
`Task: feat(mail): add retry header`. Also supply the PR title
`Release: feat(mail): add retry header`.

Confirm the issue title follows the issue guidance and Conventional Commit
subject format, with a supported type, useful scope, imperative lowercase
summary, and no trailing period. The explicit issue guidance wins over the
issue example; do not borrow the PR prefix.

Then provide these two recent issue titles with a consistent `Work:` prefix
and no explicit issue-title rule:

- `Work: feat(mail): add retry header`
- `Work: feat(mail): retry transient sends`

Confirm the skill infers that issue prefix from the same-type examples.

Then ask for an issue title with no issue-title guidance or examples, but
supply the PR title `Release: feat(mail): add retry header`. Confirm the
issue title has no prefix.

Ask for an issue title with no rule and only this same-type example from an
archived project three years ago: `Legacy: feat(mail): add retry header`.
Confirm the skill asks whether the old prefix still applies.

Supply these same-type issue titles with conflicting prefixes and no
explicit issue-title rule:

- `Release: feat(mail): add retry header`
- `Work: feat(mail): retry transient sends`

Ask for a new issue title. Confirm the skill asks which convention to use.

Ask for an issue title for a breaking API change. Confirm the Conventional
Commit subject marks it with `!` before the colon, such as
`feat(api)!: remove the legacy field`.

## Issue descriptions

Ask for a concise issue description about an import job that stops after a
transient network disconnect. Supply these facts: rerunning the full archive
duplicates imported records because completed chunks are not recorded.
Request the shortest useful structure.

Confirm it preserves those facts without a fixed template, mandatory
headings, commit-specific title limits, or 72-column wrapping.

Then ask for an issue title only for the same report. Confirm the skill
returns only the title.

Run once each for a breaking change, a security fix, a data migration, and a
revert. Supply the concrete impact and relevant mitigation or follow-up.
Confirm a full issue description explains the supplied impact and follow-up
without inventing missing details.

Ask for an issue description with only this report: `The import fails after
reconnecting.` Do not provide an error message or reproduction details.
Confirm the skill asks for the missing facts instead of inventing a cause or
claim.

## Issue comments and operation boundary

Draft a reply to this issue discussion:

- Maintainer: `Can you include the failing row and what happens before it?`
- Reporter: `CSV import stops at row 142; row 141 is imported successfully.`

Confirm the reply is concise and copy-ready, uses only supplied facts, and
is not posted.

Ask the skill to create an issue, change an existing issue's title, and post
a comment.

Confirm it drafts requested text only and does not create or modify issues,
post comments, or perform Git operations.
