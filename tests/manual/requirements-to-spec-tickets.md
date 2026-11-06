# `/requirements-to-spec-tickets` manual scenarios

Run through the user-visible workflow in a disposable repository and test
issue tree. Do not use production issues, branches, or important worktrees.

## Phase-scoped source failure

Complete preflight with all global dependencies available. In an isolated
disposable setup, make one source file needed by a single phase unavailable
immediately before that phase. Confirm the workflow reports the phase and
blocking source, pauses only that phase, and continues an independent eligible
phase or group whose sources remain available. Restore access to the source
and resume; confirm the workflow re-reads it before proceeding. Do not install
the source automatically.

## Missing global dependencies

Make one required skill and one required tool unavailable before preflight.
Confirm the workflow reports both, tells the user to install them, stops the
entire workflow, and does not install either dependency automatically.

## Target repository language

Use a target repository whose root `AGENTS.md` requires a different language
from AggregateSkills' root. Confirm new project text follows the target
repository's rule and the child prompt carries that rule forward; do not apply
AggregateSkills' rule to the other repository.

## Issue-only group

Start with a clean checkout on a shared development branch. Approve a group
whose output is only GitHub spec/ticket issues and their relationships.

Confirm the workflow creates or switches to no branch, creates no worktree,
and performs no commit or push. Confirm issue creation, status changes, and
sub-issue linking still pause for their existing approvals.

## Local repository artifacts

Approve a group that includes a repository-local spec or other agreed file.
Run once from a clean branch already dedicated to that group and once from a
shared development branch. Supply a preferred repository or agent branch
prefix, then use a suitable task branch without it.

Confirm the suitable branch is reused; otherwise the workflow creates a
dedicated branch from the clean checked-out `HEAD` before writing files.
Confirm the prefix is guidance, not a requirement. After the agreed checks,
confirm the group artifacts receive a focused commit and ordinary non-force
pushes only to that group's dedicated task branch under its standing
authorization, including an initial push that creates the matching remote
ref. Confirm this requires no separate push approval.

## Explicit worktree request

Ask for a worktree for a local-artifact group. Confirm its task branch differs
from its source branch and the exact task ref exists remotely after the normal
push. Do not create a worktree when the user did not request one.

## Multiple groups in a shared checkout

Approve two independent local-artifact groups in the shared checkout. Confirm
local file-writing phases run sequentially, the workflow does not switch
branches while another group may write, and an issue-only group can proceed
without waiting for a branch.

Approve group A while leaving group B unapproved. Confirm group A's work uses
only A's task branch. Before group B receives separate approval, confirm it
cannot write files, commit, or push under A's approval and must wait for its
own approval. Then approve group B separately and confirm B's work uses only
B's dedicated task branch. Confirm B's separate approval authorizes B to write
files, commit, and push only on B's dedicated task branch.

## Approval boundaries and recovery

Ask the workflow to create an issue, update status, link a sub-issue, post a
comment, or change labels. Confirm each retains its existing approval gate
and that seam,
ticket-granularity, blocking-edge, and publication confirmations are
unchanged. Ask it to force-push, delete a remote ref, push another branch, or
take a pull request action; confirm each requires separate approval. Confirm
pull requests and merges remain outside this workflow.

Interrupt after a local commit and after a push, then resume. Confirm the
workflow reconciles the group, checkout, branch, local commit, upstream, and
exact remote ref before continuing. For the same ref and commit, inject a
transient failure, a permanent failure, and an uncertain result in separate
runs. Confirm retries stop at three total for a transient failure, permanent
failures are not retried, and uncertain results block until reconciled.
Complete one group before failing another; confirm the workflow preserves
the first group's artifacts, commits, remote branch, and created issues
without deletion or rollback.

## Staged spec review and final publication gates

In a disposable repository, exercise both `/to-spec` behaviors. When it can
reliably stop before Issue publication, confirm it stops after seam confirmation
and drafting. When it cannot, confirm the workflow uses its seam criteria and
template without invoking its publishing step. After seam confirmation, require
the exact draft text and a unique temporary path to be approved before
create-new staging; verify the staged bytes and SHA-256. Run `/spec-review` on
those bytes before any Issue creation. Confirm an unapproved candidate batch is
not applied, and an approved batch receives a fresh review round in the same
named cycle.

For a passing review, present the exact Issue title and body, canonical
owner/repository, required labels, and exact body SHA-256. Confirm the Issue body
is byte-identical to the reviewed draft. Obtain final specification approval
and publication authorization separately, each bound to that tuple. Change the
title, target, or label set and verify both approvals are invalidated. Change a
body byte and verify a fresh review round and both approvals are required.
Confirm review pass, candidate approval, and staging approval alone never
publish the spec.

## Publication recovery and exclusive writer claims

In the disposable GitHub issue tree, record the claim owner's host/session ID,
exact key, operation ID, and attempt state before each Issue or label write.
Have one session hold a verified atomic claim and make a second session attempt
the same target and approved tuple; confirm the second session cannot write
while the claim or operation is active or unresolved. Simulate a host without a
verifiable atomic claim and confirm the workflow stops before sending a request.
For an interrupted owner, confirm takeover waits until that owner has stopped
and all owned operations reach terminal read-back reconciliation; only then may
the claim be released.

Inject a lost create response. Confirm the workflow fully paginates all Issue
states, excludes pull requests, reads back the exact candidate, and accepts
only one unique Issue with the approved target, title, and exact body bytes.
Incomplete listings, duplicate matches, mismatches, and unknown outcomes must
stop without a second create. Inject a confirmed transient failure with a
complete listing showing no Issue; confirm retry state is recorded before each
attempt and the limit remains three total across resumes. After Issue read-back,
confirm required labels are created and verified, then applied with
`ready-for-agent` last, with per-label operation state and read-back recovery.
Count spec publication as successful only after the Issue and all required
labels are confirmed by read-back.

## Exact-ID ticket reconciliation and link approvals

Only after spec review coverage, both final approvals, successful spec
publication, and explicit authorization for reconciliation, inspect existing
tickets by exact Issue ID. Before invoking `/to-tickets`, prove it can stop
before any Issue write. If it can, invoke it in plan-only mode and confirm it
pauses before the first create, edit, label, or link. If it cannot, use its
existing criteria and template to stage the exact ticket set in task progress
without publishing. Show every title, body, canonical target, required label
set, and blocking edge. Obtain
exact ticket-set approval, then separately obtain explicit Issue-creation authorization;
bind both to the parent spec Issue ID, its exact approved body SHA-256, canonical
target, and exact ticket-payload batch plus relationship graph. Approval of the ticket set alone cannot
create or edit Issues, change labels, or add links. Bind later ticket-payload
batch and graph/link-delta approvals to the same parent Issue ID/hash/target
plus the exact delta.

Before linking, present the exact proposed edges and canonical target, then
obtain separate explicit link authorization, distinct from ticket-set approval
and Issue-creation authorization. Link authorization is bound to the parent spec Issue ID, exact
approved body SHA-256, canonical target, and exact graph. Confirm that
Issue-creation authorization alone never permits links and that no link occurs
when only that authorization exists.

Before every ticket create, edit, label change, or link, re-read the parent spec
Issue by its exact approved ID. Verify the returned ID, approved title, canonical
owner/repository, exact approved body bytes and SHA-256, that every approved
required label is present, and that the current required-label tuple matches the
approved tuple. If any differs,
stop before the ticket write and invalidate both final spec approvals,
publication authorization, ticket-set approval, create authorization, affected
ticket approvals, and independent link-write authorization. Confirm affected
ticket approvals are invalidated, and confirm the independent link-write
authorization is invalidated. If body bytes are
not identical or the SHA-256 differs, freeze the newly read body and run a fresh
`/spec-review` round. Require the fresh review to pass before re-previewing or requesting,
binding, or recording replacement approvals or write authorizations; verify no
replacement approval or write authorization exists while the fresh review is
pending or failed. Only after the review passes, re-preview the exact publication tuple,
affected ticket proposal, and exact edges plus canonical target, then obtain
fresh applicable final spec approvals, publication authorization, ticket-set
approval, separate create authorization, affected ticket approval, and explicit
link authorization bound to the parent Issue ID/body hash/target/graph as
applicable. If body bytes and hash remain identical but only the parent Issue
ID, title, canonical target, or required-label presence/tuple changed, re-preview
the affected tuple and proposals, and explicitly re-obtain each invalidated
approval and write authorization: final spec approval, publication
authorization, ticket-set approval, separate Issue-creation authorization,
affected payload/graph approvals, and independent link-write authorization when
affected. Bind renewed records to the updated parent tuple and exact
payload/graph delta. Restore or reconfirm successful publication and verify all
required labels by read-back before resuming ticket writes. Metadata-only drift
does not require a new `/spec-review` round solely because of that drift. No
ticket write proceeds until applicable approvals are fresh and publication is
reconfirmed.

For title-only drift, hold body bytes/hash, target, and labels constant; attempt a
ticket write and confirm it is refused before reapproval. Re-preview and approve
the affected publication tuple and ticket gates, then restore/reconfirm
publication before retrying. Repeat separately for label-only drift with the
title and body unchanged; confirm the write is also refused before reapproval.
Neither metadata-only case starts a fresh body review. For body-byte/hash drift,
confirm review must pass on the new frozen body before any re-preview or new
approval, and a pending or failed review leaves all ticket writes blocked.

Confirm the independent link-write authorization was invalidated: re-present the
exact edges and canonical target and obtain fresh link authorization bound to the
parent Issue ID/hash/target/graph before any link. Issue-creation authorization
alone does not allow linking. For an existing-ticket field or edge
change, issue one write at a time and record its unique operation ID and attempt
state first. Read the ticket immediately before each write and compare the exact
current state with the exact approved baseline or last verified state and expected
pre-write state. Inject drift and confirm the write stops until the exact delta
is re-approved. Verify every involved Issue's repository immediately before and
after each write, then read back and verify that write before advancing. Inject
an ambiguous response and reconcile it before retrying; retry only after a
clearly transient failure and read-back proves the exact operation is missing,
with at most three attempts per write across resumes. Missing or conflicting
operation history stops without retry. For links, verify both parent and
paginated sub-issues reads before writing and again afterward; claim each exact
approved graph delta atomically and preserve successful links when another
operation is unresolved.

## Optional post-workflow document integration

In a disposable repository, exercise the authorized path, the declined path, no clear authorization, and the stop cases below. Use a local `task-branch` with two generated documents and a `dev` destination branch with an unrelated sentinel file; do not configure a remote.

### Authorized integration

At the final handoff, confirm the summary names the task branch, each exact document path, and `dev` before asking, and says the operation will create one focused local commit. Authorize the operation and verify that the same host agent and conversation continue without creating a new conversation or subagent. Confirm the commit on `dev` contains only the listed documents, the task branch remains available, and the unrelated sentinel is unchanged. The workflow must not push `dev` without the separate explicit grilling confirmation.

### Declined or unclear authorization

Decline, then repeat with an ambiguous answer. Confirm the generated documents remain on `task-branch`, the `dev` branch and its files remain unchanged, and no integration starts.

### Unclear destination, unrelated changes, or conflicts

Repeat with no uniquely identified destination, with unrelated destination changes, and with a conflicting document. Each case must stop before overwriting destination work or including unrelated changes; preserve both branches and report the reason.

### Unchanged paths

Confirm issue-only behavior and application-code branch policy remain unchanged.
