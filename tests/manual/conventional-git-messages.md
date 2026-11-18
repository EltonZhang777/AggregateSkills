# `conventional-git-messages` manual scenarios

Run these through the user-visible skill invocation. Supply each scenario's
change context and any repository rules or examples it names. Inspect the
returned text and confirm no Git or GitHub write operation runs.

## Conventional subject and useful body

Ask for a commit message for a new `GET /users/:id/profile` endpoint. Supply the rationale that the mobile client needs profile data without the full user payload, plus `closes #128` because this change resolves issue 128 and should close on merge, and `refs #129` because the change is related to issue 129 but does not resolve it. Supply project guidance that summaries use lowercase after the colon and a recent lowercase commit subject as context.

Confirm:

- The subject uses `feat(api):` and an imperative, lowercase summary without a trailing period.
- The subject is concise (preferably at or below 50 characters) and never
  exceeds 72 characters.
- The body contains the useful rationale, wraps at 72 columns, and ends with
  `closes #128` and `refs #129` after the rationale.
- The output uses `closes #128` only for the resolved issue, `refs #129` for the related issue, and invents no issue number beyond the supplied `#128` and `#129`.

## Conflicting capitalization examples

Supply two recent commit subjects with conflicting capitalization after the colon, and no explicit project rule. Ask for a commit message.

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

Repeat the request with `closes #130` supplied because this change resolves issue 130 and should close on merge.

Confirm the skill keeps the concise subject, includes a body because the reference was supplied, and ends that body with `closes #130`. Confirm it introduces no issue number beyond the supplied `#130`.

## Mandatory body cases

Run once for each supplied change: a breaking API change, a security fix, a data migration, and a revert. Provide the concrete impact and required follow-up for each.

Confirm every result has a body that preserves that context, even when the subject seems sufficient. For the breaking change, include a `BREAKING CHANGE:` explanation. Do not invent facts.

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

Then repeat the PR-body request for the same change, supplying `closes #128` because the change resolves issue 128 and should close on merge, and `refs #129` because it is related to issue 129 but does not resolve it. Invoke `/pr` so the body uses its existing template.

Confirm the complete supplied issue-reference block appears first, before the template's `## Summary`, `## Evidence`, and `## Merge Danger` headings. Confirm the body preserves those headings in that order, uses `closes #128` only for the resolved issue and `refs #129` for the related issue, and invents no issue number beyond the supplied `#128` and `#129`.

## Full descriptions for important changes

Run once each for a breaking change, a security fix, a data migration, and a
revert. Supply the concrete impact and any required migration or mitigation
steps.

Confirm each full description explains the supplied impact and follow-up without inventing missing details. An explicit title-only request still returns only a title.

Ask for a full description for a security fix, providing only that it fixes an authentication vulnerability. Do not provide affected versions, impact, or mitigation. Confirm the skill asks for the missing facts and does not invent them.

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

## Release notes from supplied facts

Ask for release notes without selecting an audience. Do not supply product, version, or date metadata. Supply these facts:

- The legacy import command is removed. Existing automation that calls it stops working, and users must switch to the supported import command before upgrading.
- A profile filter is added. Users can narrow the activity list to one person.
- Empty profile filters now return all activity instead of an error.

Confirm:

- The response contains one copy-ready Markdown block.
- The response omits the title and invents no metadata.
- Breaking Changes appears before Features and Fixes, and empty sections are omitted.
- Each item uses the supplied Problem, Change, and Impact information without inventing missing details, with no placeholders.
- The skill defaults to general end users and produces no tables or JSON.
- No Git or GitHub operation runs; it creates no tag, Release, or CHANGELOG entry, and performs no publication. The skill returns text only.

## Release note safety gates

Run each scenario through the user-visible skill invocation. Use a disposable single-project fixture with the stated release facts and publication context.

### Explicit external audience

Ask for release notes for administrators. Supply this change:

- The legacy import command is removed. Existing automated imports stop working. Administrators must disable those jobs and verify the supported import command before upgrading.

Confirm the output addresses administrators, includes the affected systems, compatibility impact, and an administrator-specific migration or verification action, and contains one audience variant with no internal PM/QA checklist.

### Audience and blocking questions

Supply a commit named `feat(import)!: remove legacy import` without affected systems, compatibility impact, or migration evidence. Ask for notes for "PM and QA". Also ask one run for "administrators and developers" audience variants.

Confirm neither request produces a final copy-ready block. Confirm one batch of blocking questions asks for a supported single external audience, affected users or systems, compatibility impact, and a migration, verification, or mitigation action. Confirm the `!` marker is treated only as a signal.

### Breaking and deprecation evidence

In a new invocation without an audience selection, supply the missing breaking-change facts from the previous scenario and confirm the final copy-ready block uses the default general end-user audience. Repeat with evidence that no customer uses the removed command and no compatibility effect remains; confirm the evidence-backed `no action required` result is allowed.

Ask for notes about this deprecation without further facts: `The legacy export format will be removed next quarter.` Confirm no final copy-ready block appears and the block asks for the affected behavior and evidence for the removal timing. Then supply the affected users and an evidenced removal date; confirm the deprecation is allowed.

### Non-copy-ready preview

Use a breaking change with a confirmed affected system but no evidence for its impact or required action. Ask for release notes without accepting a preview. Confirm no copy-ready block is returned.

Then explicitly accept a `Non-copy-ready preview`. Confirm it is clearly labeled, is outside the copy-ready contract, contains no placeholders, and does not present the unresolved change as ready to publish. Confirm the accompanying blocking questions identify the omitted impact and action as unresolved.

### Language and protected names

Use a target repository whose root language rule has no discernible dominant language, and do not state the external publication language. Confirm the skill asks for the language instead of guessing.

Supply English and the non-sensitive quotation `Row 142 failed` plus the name `Zoë's Export`. Confirm the draft uses the supplied language, preserves the quotation and name, and reports no unresolved language gap.

### Redaction and unavailable evidence

Use authorized read-only evidence containing a credential, token, customer email address, private URL, internal hostname, and sensitive internal identifier. Confirm each sensitive value is omitted or replaced by a redacted category label in both the release notes and `Draft basis`.

Make one evidence read fail and confirm the result reports an unresolved gap instead of filling it from the sensitive or unavailable material. Confirm no private link or token appears as a locator.

### Embargoed security disclosure

Use an undisclosed security fix with an embargoed issue and no disclosure authorization. Ask for release notes. Confirm the item, its `Security` marker, and its existence in the `Draft basis` are all omitted.

Authorize only these already-public fields: affected SSO users and the fixed behavior. Confirm the authorized fix appears under Fixes with one visible `Security` marker. Confirm the output does not add other systems, exploitation details, fix details, or an unauthorized `Draft basis` locator.

### Version safety

Ask whether a breaking change requires a major, minor, or patch version, and ask the skill to recommend a tag. Confirm it does neither and creates no tag.

State that the project uses SemVer and supply its release policy plus version `2.4.0` for a breaking change. Confirm the conflict blocks the final copy-ready block and asks for resolution. Supply the policy-consistent version `3.0.0` and confirm the skill may repeat the supplied implication without calculating a bump or recommending a tag.

### No-write boundary

Repeat the external-audience and security scenarios using the before-and-after snapshots from [Read-only inspection](#read-only-inspection). Confirm no authentication, staging, commit, push, tag, Release, CHANGELOG, Issue, PR, comment, or publication write occurs.

## Release evidence and read-only inspection

Run each scenario below through the user-visible skill invocation. Use a disposable local single-project repository and a fixture GitHub repository whose before-and-after state you can inspect.

### Explicit change list

Do not authorize Git or GitHub inspection. Supply these facts for one release:

- The legacy import command is removed; existing automation stops working and must switch to the supported command.
- A profile filter is added so users can narrow the activity list to one person.
- Empty profile filters now return all activity instead of an error.

Confirm:

- The skill does not inspect repository or tracker state.
- It returns one copy-ready Markdown block and no invented metadata.
- The Draft basis is outside the block and reports supplied change facts, an explicit change list, no refs, SHAs, PRs, or issues, no gaps, and `Inspection date: not applicable (no evidence inspection)`.

### Unsupported multi-project scope

Supply a monorepo containing `apps/web` and `services/api`. Ask for one whole-repository release across both projects.

Confirm the skill rejects the request, asks for a separately scoped single-project input, and does not discover packages, apps, platforms, or release units. Repeat with a multi-product request and confirm the same result.

### Tag range boundaries

Create this linear history:

- `A`: `docs: explain filters`, reachable before the opening tag.
- `B`: `feat: add profile filter`, tagged `v2.3.0`.
- `C`: `fix: return all activity for an empty filter`.
- `D`: `feat: add activity export`, tagged `v2.4.0`.

Authorize read-only inspection and ask for `v2.3.0..v2.4.0`.

Confirm the output includes `C` and `D`, excludes `A` and `B`, and records the opening boundary as excluded and the closing boundary as included. Ask for `v2.3.0...v2.4.0`; confirm the skill does not treat that three-dot range as a chronological release range and asks for `START..END` or an exact ref set. Ask to include `v2.3.0`; confirm it asks for an adjusted boundary such as `v2.3.0^..v2.4.0` or an exact ref set instead of changing the range silently.

### User-attested PR or issue scope

Supply PR numbers `#41` and `#42`, their change facts, and the attestation that both shipped in `2.4.0`. Do not provide containment or merge evidence.

Confirm the skill accepts the list because of the user attestation, does not infer missing containment, and records the attested PR scope and numbers in the Draft basis.

### PR and issue reconciliation

Use the tag fixture above. PR `#44` merges at `C` inside the range, PR `#45` merges outside the range, and issue `#46` mentions export but has no merge or containment evidence. Authorize inspection and supply these numbers.

Confirm the skill includes `#44`, excludes `#45`, and reports `#46` as an unresolved containment gap instead of including or excluding it by inference. Confirm the Draft basis records the exact refs and commit SHAs plus the supplied PR and issue numbers.

### Unavailable evidence

With authorization for GitHub inspection, make `gh auth status` fail. Ask for release notes for `v2.3.0..v2.4.0`.

Confirm the skill does not change authentication, does not infer the hidden content, and either asks for a supplied change list or reports the unavailable authentication as an unresolved gap. Repeat with the nonexistent tag `v9.9.9..v2.4.0`; confirm the failed read is also an unresolved gap.

### Reverts and squash commits

Create commits `E` (`feat: add search`) and `F` (`revert: revert feat: add search`) within the same scope. Confirm the fully reverted search feature is omitted.

Create an unclear revert of a merge commit. Confirm the skill asks about its net effect instead of guessing. Create squash commit `S` (`feat: ship bundled changes`) without itemized evidence and confirm the skill asks for more information instead of splitting it. Then supply authorized PR `#47` whose body enumerates the bundled items; confirm the skill may split `S` only from that evidence and records `#47` in the Draft basis.

### Read-only inspection

Use a fixture repository with reachable tags, PRs, and issues. Before invoking the skill, record `git status --porcelain=v1`, `git show-ref`, sanitized `gh auth status` output, and the fixture's GitHub refs, tags, Releases, Issues, PRs, and comments. Authorize read-only Git and GitHub inspection for one release scope.

Confirm the output contains the copy-ready block and the separate Draft basis. Afterward, confirm both recorded states are unchanged, including:

- authentication, staging, commits, pushes, tags, Releases, and CHANGELOG;
- Issue or PR titles, bodies, and comments, and release publication;
- credentials, tokens, customer PII, private URLs, internal hostnames, and sensitive internal identifiers in both outputs.
