# `/requirements-to-spec-tickets` manual scenarios

Run through the user-visible workflow in a disposable repository and test
issue tree. Do not use production issues, branches, or important worktrees.

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
confirm the group artifacts receive a focused commit and normal push under
the group's standing authorization, including an initial push that creates
the remote branch.

## Explicit worktree request

Ask for a worktree for a local-artifact group. Confirm its task branch differs
from its source branch and the exact task ref exists remotely after the normal
push. Do not create a worktree when the user did not request one.

## Multiple groups in a shared checkout

Approve two independent groups that both write local files in the shared
checkout. Confirm their local file-writing phases run sequentially and the
workflow does not switch branches while another group may write. Confirm an
issue-only group can proceed without waiting for a branch.

## Approval boundaries and recovery

Ask the workflow to create an issue, update status, or link a sub-issue.
Confirm each retains its existing approval gate and that seam,
ticket-granularity, blocking-edge, and publication confirmations are
unchanged. Confirm pull requests and merges remain outside this workflow.

Interrupt after a local commit and after a push, then resume. Confirm the
workflow reconciles the group, checkout, branch, local commit, upstream, and
exact remote ref before continuing. For the same ref and commit, inject a
transient failure, a permanent failure, and an uncertain result in separate
runs. Confirm retries stop at three total for a transient failure, permanent
failures are not retried, and uncertain results block until reconciled.
Complete one group before failing another; confirm the workflow preserves
the first group's artifacts, commits, remote branch, and created issues
without deletion or rollback.
