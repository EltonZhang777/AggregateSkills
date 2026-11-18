# `/extra-setup-matt-pocock-skills` manual scenarios

Run these through the user-visible skill in a disposable repository. Do not use live GitHub writes or a production repository. Static checks do not prove that the interactive scenario ran.

Cover one-section-at-a-time confirmation, the complete draft and first-run migration diff, managed-section preservation, rerun behavior, missing setup, rejected themes, missing markers, changed legacy text, approval consumption, no-cache behavior, and PARTIAL/runtime evidence cases.

## Repository deployment

Use `EltonZhang777/AggregateSkills` only as the read-only review target for the recorded deployment. Do not run the setup skill in this checkout. Run any write-capable deployment scenario in a disposable copy first. Confirm `AGENTS.md` has one managed session/checkout/handoff section, `docs/agents/issue-tracker.md` has one managed issue-operations section, and `GLOSSARY.md` has one managed English terminology section. Confirm all three managed sections equal their reviewed templates with no placeholder substitution. Confirm the glossary links target the root `AGENTS.md`.

Confirm the tracker migration replaces every recognized legacy tracker default with its reviewed replacement and leaves one issue-operations section. Confirm the glossary retains its existing mixed-language entries unchanged, `docs/agents/domain.md` remains untouched, and a rerun changes bytes only inside the three managed ranges.

## Discovery and section confirmation

Start once with the existing `/setup-matt-pocock-skills` output and once with the issue-tracker guide removed. Confirm the first run explores before asking, shows repository, tracker, checkout, shell, verification, handoff, and existing managed-section facts with evidence, and asks one section at a time. Confirm the missing setup reports the missing prerequisite, tells the user to run the setup skill, and stops without installing or modifying it.

Start once without a root `AGENTS.md`, once without its `## Agent skills` configuration, once with conflicting `## Agent skills` configurations, and once with no discernible dominant language in its normative prose. Confirm each run stops before composing the draft or writing and asks the user instead of accepting another agent file.

Reject one theme and confirm the draft omits only that theme and its dependent text. Give an uncertain answer and confirm the section remains disabled or simplified instead of being enabled by default. Accept checkout while rejecting handoff, then reject both. Accept summary reads while rejecting issue-write rereads, then reverse those decisions. Confirm only the confirmed subsections appear inside each shared managed block.

## Complete draft and first-run migration

Accept the recommendations and confirm the skill presents a complete draft before any write. Confirm exploration labels the tracker `unmigrated`. Verify the draft uses `references/tracker-migration.md` and shows the exact first-run migration diff for the issue read/list commands, repeated fetch-ticket command, PR detail and triage commands, bare issue-or-PR fallback, and Wayfinding frontier. Confirm every reviewed replacement occurs once, the issue-family defaults delegate to one managed issue-operations section, the session/checkout/handoff and glossary sections are shown as insertions, and no write occurs before approval.

On a tracker that already has the managed issue-operations section, run with summary-first issue reads rejected and issue-write rereads accepted. Confirm the legacy read commands remain unchanged and the issue block does not claim to own them, while the shared issue-content trust boundary remains present. Rerun with the same decision and confirm the workflow classifies the result as `unmigrated`, updates only the managed issue section, and leaves every recognized legacy command unchanged. Then opt into summary-first reads and confirm the exact migration occurs once before later reruns use the `fully migrated` path.

Use a non-GitHub tracker guide. Enable summary-first issue reads and confirm the GitHub migration is skipped and the rerun matrix is bypassed while the tracker-neutral summary rules are still shown in the complete draft.

Decline the draft once and confirm every target file is unchanged. Approve the next unchanged draft and confirm the three managed sections have one complete marker pair each.

## Managed-section preservation and rerun

Add sentinel text immediately before and after each managed section, then rerun the workflow with summary-first reads enabled. Confirm the rerun detects `fully migrated`, reads the existing markers, shows only the managed replacements, preserves every reviewed replacement and both sentinels byte-for-byte, and leaves the legacy commands absent.

Repeat that rerun with summary-first reads disabled. Confirm the workflow reports the conflicting decision and stops before writing. Separately create an `ambiguous` tracker with one legacy command missing, a duplicate replacement pointer, and a partial managed marker set in distinct clean copies. Confirm each state stops before drafting or writing.

Create a duplicate start marker, remove an end marker, reverse a marker pair, corrupt one marker suffix, and introduce one crossed managed range in separate clean copies. Repeat separately with a newline after the opening delimiter, extra whitespace before the namespace, and a missing closing delimiter; also wrap a marker's closing delimiter onto the next line. Confirm each case is classified as `ambiguous` and stops before drafting or writing. Reject the proposed draft once more and confirm the files remain unchanged.

## Changed legacy text

Change one legacy issue command so it no longer matches the recorded first-run migration. Confirm the workflow reports changed legacy text, identifies the affected command, and stops instead of guessing or creating a second default.

Perform the same check with two legacy commands carrying the conflicting full read. Confirm the duplicate is treated as ambiguous ownership and no migration is written.

## Tracker, cache, and evidence examples

Confirm the target tracker states that the persistent issue cache is disabled. Confirm summary reads request `number`, `title`, `state`, `labels`, `assignees`, `updatedAt`, and `url`; body or comments are requested only for a named need. Exercise a write with an ambiguous outcome and confirm the workflow re-reads authoritative state before any retry.

Resolve a bare issue-or-PR number once. Confirm the PR summary is tried before the issue summary and neither path requests a body or comments. Exercise an external-PR list and a Wayfinding frontier query. Confirm each list uses `--limit <bound>` (or explicit pagination), the external-PR list requests the shared summary fields plus `authorAssociation` without bodies or comments, and the frontier reads only `number,state,blockedBy` for each candidate first. When native dependencies are unavailable, confirm the focused body escalation reads only the top `Blocked by:` line and an open issue referenced by the fallback removes that candidate. Pass the valid commands and each unsafe full-body, unbounded-list, and fixed-length negative fixture through the contract validator; confirm every unsafe fixture fails even when valid commands are present.

Review the optional navigation-only cache template separately. Opt in once and confirm it remains non-authoritative for writes, assignment, labels, closure, and verification. In the default run, confirm no navigation-cache managed section is deployed.

## Approval consumption and closure evidence

Exercise a `one-time` approval with a pre-execution sandbox or technical denial and confirm the approval is not consumed. Repeat with an uncertain outcome that may have reached the external system and confirm it is consumed. Exercise a `task` approval and confirm it ends at task completion, withdrawal, or an invalidator and does not become thread-wide authority. Confirm a handoff uses `source`, `action`, `normalized_target`, `lifetime`, and `invalidators` without renamed required fields. Confirm consumption state is stored separately and secrets are never recorded.

Record a passing result for an exact repository-native full object ID and tested tree state, then change the object or content and confirm the old evidence becomes stale. Remove one required evidence item after all original ticket deliverables are complete, and confirm the result is `PARTIAL`, not `PASS`. Repeat with remaining scope that has a clearly linked follow-up issue. Confirm PARTIAL keeps the issue open without separate, explicit closure approval; when that approval is supplied, require delivered scope, remaining scope, and current or linked follow-up coverage. Confirm unlinked accepted risk does not authorize closure.

Exercise `runtime: N/A` once for a text-only change with non-runtime evidence and once for an executable or agent-workflow change. Confirm the second case still requires automated tests, static checks, and manual acceptance.

## Glossary composition

Enable checkout and closure evidence while rejecting handoff, issue reads, issue writes, and the optional cache. Confirm the glossary contains only the checkout, tested tree state, and PARTIAL closure evidence terms and links to the root `AGENTS.md` as in the other sections. Translate the target headings once and confirm every glossary link still uses the explicit language-independent anchors.

## Portability

Repeat in repositories with and without Git, with a non-GitHub tracker, with a shared checkout and without worktrees. Confirm the deployed rules use only the detected surfaces and do not require PowerShell, Git, GitHub, a worktree, or runtime smoke. Confirm object identifiers retain the repository-native form and length and that no fixed numeric object-ID length is required.
