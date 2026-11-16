# `/extra-setup-matt-pocock-skills` manual scenarios

Run these through the user-visible skill in a disposable repository. Do not use
live GitHub writes or a production repository. Static checks do not prove that
the interactive scenario ran.

Cover one-section-at-a-time confirmation, the complete draft and first-run
migration diff, managed-section preservation, rerun behavior, missing setup,
rejected themes, missing markers, changed legacy text, approval consumption,
no-cache behavior, and PARTIAL/runtime evidence cases.

## Repository deployment

Use `EltonZhang777/AggregateSkills` only as the read-only review target for
the recorded deployment. Do not run the setup skill in this checkout. Run any
write-capable deployment scenario in a disposable copy first. Confirm
`AGENTS.md` has one managed session/checkout/handoff section,
`docs/agents/issue-tracker.md` has one managed issue-operations section, and
`GLOSSARY.md` has one managed English terminology section. Confirm all three
managed sections equal their reviewed templates after replacing the
instruction-file placeholder.

Confirm the tracker migration removes the three legacy full-read defaults and
leaves links to the one issue-operations section. Confirm the glossary retains
its existing mixed-language entries unchanged, `docs/agents/domain.md` remains
untouched, and a rerun changes bytes only inside the three managed ranges.

## Discovery and section confirmation

Start once with the existing `/setup-matt-pocock-skills` output and once with
the issue-tracker guide removed. Confirm the first run explores before asking,
shows repository, tracker, checkout, shell, verification, handoff, and existing
managed-section facts with evidence, and asks one section at a time. Confirm the
missing setup reports the missing prerequisite, tells the user to run the setup
skill, and stops without installing or modifying it.

Reject one theme and confirm the draft omits only that theme and its dependent
text. Give an uncertain answer and confirm the section remains disabled or
simplified instead of being enabled by default. Accept checkout while rejecting
handoff, then reject both. Accept summary reads while rejecting issue-write
rereads, then reverse those decisions. Confirm only the confirmed subsections
appear inside each shared managed block.

## Complete draft and first-run migration

Accept the recommendations and confirm the skill presents a complete draft
before any write. Verify the draft uses `references/tracker-migration.md` and
shows the exact first-run migration diff for the issue-read bullet, issue-list
command, and repeated fetch-ticket command. Confirm all three legacy read
defaults are redirected to one unique managed issue-operations section, the
session/checkout/handoff and glossary sections are shown as insertions, and no
write occurs before approval.

Repeat the first run with summary-first issue reads rejected and issue-write
rereads accepted. Confirm the legacy read commands remain unchanged and the
issue block does not claim to own them, while the shared issue-content trust
boundary remains present.

Use a non-GitHub tracker guide. Enable summary-first issue reads and confirm the
GitHub migration is skipped while the tracker-neutral summary rules are still
shown in the complete draft.

Decline the draft once and confirm every target file is unchanged. Approve the
next unchanged draft and confirm the three managed sections have one complete
marker pair each.

## Managed-section preservation and rerun

Add sentinel text immediately before and after each managed section, then rerun
the workflow. Confirm the rerun reads the existing markers, shows only the
managed replacements, preserves both sentinels byte-for-byte, and leaves the
legacy commands absent.

Create a duplicate start marker, remove an end marker, reverse a marker pair,
and introduce one ambiguous managed range in separate clean copies. Confirm
each case stops before writing. Reject the proposed draft once more and confirm
the files remain unchanged.

## Changed legacy text

Change one legacy issue command so it no longer matches the recorded first-run
migration. Confirm the workflow reports changed legacy text, identifies the
affected command, and stops instead of guessing or creating a second default.

Perform the same check with two legacy commands carrying the conflicting full
read. Confirm the duplicate is treated as ambiguous ownership and no migration
is written.

## Tracker, cache, and evidence examples

Confirm the target tracker states that the persistent issue cache is disabled.
Confirm summary reads request `number`, `title`, `state`, `labels`,
`assignees`, `updatedAt`, and `url`; body or comments are requested only for a
named need. Exercise a write with an ambiguous outcome and confirm the workflow
re-reads authoritative state before any retry.

Review the optional navigation-only cache template separately. Opt in once and
confirm it remains non-authoritative for writes, assignment, labels, closure,
and verification. In the default run, confirm no navigation-cache managed
section is deployed.

## Approval consumption and closure evidence

Exercise a `one-time` approval with a pre-execution sandbox or technical denial
and confirm the approval is not consumed. Repeat with an uncertain outcome that
may have reached the external system and confirm it is consumed. Exercise a
`task` approval and confirm it ends at task completion, withdrawal, or an
invalidator and does not become thread-wide authority. Confirm a handoff uses
`source`, `action`, `normalized_target`, `lifetime`, and `invalidators` without
renamed required fields. Confirm
consumption state is stored separately and secrets are never recorded.

Record a passing result for an exact repository-native full object ID and tested
tree state, then change the object or content and confirm the old evidence
becomes stale. Remove one required evidence item and confirm the result is
`PARTIAL`, not `PASS`. Confirm PARTIAL keeps the issue open without a separate,
explicit closure approval; when that approval is supplied, require delivered
scope, remaining scope, and follow-up coverage or accepted risk.

Exercise `runtime: N/A` once for a text-only change with non-runtime evidence
and once for an executable or agent-workflow change. Confirm the second case
still requires automated tests, static checks, and manual acceptance.

## Glossary composition

Enable checkout and closure evidence while rejecting handoff, issue reads,
issue writes, and the optional cache. Confirm the glossary contains only the
checkout, tested tree state, and PARTIAL closure evidence terms and leaves the
same instruction-file link placeholder replacement as the other sections.
Translate the target headings once and confirm every glossary link still uses
the explicit language-independent anchors.

## Portability

Repeat in repositories with and without Git, with a non-GitHub tracker, with a
shared checkout and without worktrees. Confirm the deployed rules use only the
detected surfaces and do not require PowerShell, Git, GitHub, a worktree, or
runtime smoke. Confirm object identifiers retain the repository-native form and
length.
