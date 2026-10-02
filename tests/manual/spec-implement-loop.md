# `/spec-implement-loop` manual scenarios

Run these through the user-visible skill invocation in a disposable repository
with test issues and branches. Do not use a production repository or approve
issue/status writes during scenarios that check their approval gates.

## Reuse or prepare a task branch

Start once on a clean branch dedicated to the supplied root, and once on a
shared development branch such as `dev` or `experimental`. In the second run,
use a disposable task worktree.

Confirm the first run reuses its suitable task branch. Confirm the second
prepares a dedicated branch from the clean checked-out `HEAD`, distinct from
the worktree's source branch. Supply repository or agent naming conventions
with a preferred prefix, then use a suitable branch without that prefix.
Confirm the workflow follows naming guidance but does not require the prefix.

Confirm each new task worktree has a matching remote branch, including when
the initial push creates that branch. A divergent or uncertain remote state
must be reconciled; the workflow must not force-push.

Start with uncommitted work or provide conflicting issue evidence and an
unresolved engineering choice. Confirm the workflow preserves the dirty work
and pauses on ambiguity instead of switching branches or guessing.

## Task-scoped commits and pushes

Approve one root and run two small tickets on its task branch. Confirm each
ticket gets one focused commit after its acceptance checks and review, and its
confirmed commit is pushed without a separate commit or push prompt. Confirm
the same authorization covers a task worktree and its initial branch push.

Ask the workflow to update or close a ticket, change root status, create a PR,
or merge a PR. Confirm each action retains its own approval gate. Finish the
root, then start an unrelated root and confirm the prior Git authorization
does not carry over.

## Interruption and reconciliation

Interrupt once after a commit and once after a push, then resume the same root.
Confirm the workflow re-reads the issue tree and reconciles the worktree,
branch, local commit, upstream mapping, and exact remote ref before continuing.
It must not repeat a confirmed commit or push. For an outcome that cannot be
established, confirm it blocks and asks for reconciliation.

## Push retries and partial results

In separate runs for the same ref and commit, inject a clearly transient push
failure, a permanent failure, and an uncertain result. Confirm transient
retries stop at three total attempts, permanent failures are not retried, and
uncertain results block until reconciliation. Complete one ticket
successfully before failing a later ticket; confirm the workflow preserves
the first commit, remote branch, and any created issue without deleting,
rolling back, or rewriting them.

## Ticket and root checkpoints

After a ticket passes acceptance checks and review and its commit is pushed,
confirm the workflow presents the evidence and pauses before declaring the
ticket complete or writing issue/status. After all tickets, confirm it runs
final verification and root review, presents their evidence, and pauses before
declaring the root complete. Issue/status writes still require explicit
approval at both checkpoints.
