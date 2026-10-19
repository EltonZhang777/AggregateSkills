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
