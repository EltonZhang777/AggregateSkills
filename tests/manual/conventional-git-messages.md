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
