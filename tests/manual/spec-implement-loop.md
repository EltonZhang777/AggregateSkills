# `/spec-implement-loop` manual scenarios

Run these through the user-visible skill invocation in a disposable repository with test issues and branches. Do not use a production repository. In scenarios checking non-status write gates, withhold approval for issue creation, comments, labels, pull requests, and merges. The graph comment may proceed only under the approved root-spec scenario.

## Graph planning and reusable worktree pool

Create a root with three implementation tickets: #101 and #102 are independent; #103 is blocked by #101. Have #101 add a new file and modify an existing one. Start the skill and confirm it reads all explicit child links, issue comments, labels, and native blocker edges before scheduling. Confirm it publishes the complete blocker-to-blocked Mermaid graph on the root before assigning work, with the parent link shown as non-blocking and without a separate comment-approval pause.

Confirm the graph width is two, and that one root-specific integration worktree and two stable worker worktrees under `.wt` exist before either worker starts. Confirm worker branches are fresh, ticket-specific, local, and based on the latest integration tip. Only #101 and #102 may start; #103 remains blocked until #101 is completed and its status is synced.

Start #101 and #102 in parallel. Finish #101 first while #102 is still running. Confirm the coordinator captures #101's complete reviewed diff, including the new file, applies it to the latest integration tip, reruns checks there, commits once on the integration branch, and pushes it. After the ticket checkpoint and status sync, confirm the coordinator verifies that #101's captured changes are in the latest integration history and no post-review edits remain, restores only #101's captured paths from the latest integration tip, and creates a fresh branch from the latest tip; confirm the slot is clean and has no uncommitted copy before #103 starts. If any captured change is absent from integration or any unreviewed change remains, preserve the slot and do not assign #103 there. Finish #102 and #103; confirm the coordinator alone changes branches, commits, integrates, and pushes the integration branch. Worker branches are never published. If patch application conflicts or the slot remains dirty, confirm the coordinator preserves the evidence and pauses instead of resetting or cleaning it.

## Reuse or prepare the integration branch

Start once in a clean `.wt` worktree on a root-specific branch, and once on a shared development branch such as `dev` or `experimental`. Confirm the first run reuses its suitable `.wt` worktree as the integration worktree. In the second run, confirm it prepares a dedicated integration branch and worktree under `.wt` from the clean checked-out `HEAD`, distinct from the source branch. Supply repository or agent naming conventions with a preferred prefix, then use a root-specific name such as `<prefix>/issue-147-<feature-slug>` without hard-coding one prefix.

Confirm every integration worktree has the matching task-remote upstream, including when the initial push creates that ref. Confirm worker branches have matching upstream configuration but are never pushed. Reconcile divergent or uncertain remote state; never force-push.

Start with uncommitted work or conflicting issue evidence and an unresolved engineering choice. Confirm the workflow preserves dirty work and pauses on ambiguity instead of switching branches or guessing.

## Readiness guards

Create a ticket whose explicit blockers are closed but whose acceptance criteria are ambiguous, and another whose required permission or environment is unavailable. Confirm neither is assigned until its gap is resolved; continue only with an independent ticket whose blockers, acceptance criteria, permissions, approvals, and environment are ready.

## Task-scoped commits and pushes

Approve one root and run two small tickets. Confirm each ticket gets one focused integration commit after acceptance and review, and its confirmed commit is pushed without a separate commit or push prompt. Confirm the same authorization covers the integration worktree and its initial branch push.

Confirm ticket and root status synchronization follows issue #143 without an extra status-approval pause. Ask the workflow to create an issue, add a comment other than the authorized graph comment, change labels, create a PR, or merge a PR; confirm each non-status action retains its approval gate. Finish the root, then start an unrelated root and confirm the prior Git authorization does not carry over.

## Interruption and reconciliation

Interrupt once after a commit and once after a push, then resume the same root. Confirm the workflow rereads the issue graph and reconciles the integration and worker worktrees, branches, local commits and changes, upstream mappings, and exact remote ref before continuing. It must not repeat a confirmed commit or push. For an outcome that cannot be established, confirm it blocks and asks for reconciliation.

## Push retries and partial results

In separate runs for the same ref and commit, inject a clearly transient push failure, a permanent failure, and an uncertain result. Confirm transient retries stop at three total attempts, permanent failures are not retried, and uncertain results block until reconciliation. Complete one ticket successfully before failing a later ticket; confirm the workflow preserves the first integration commit, remote branch, and any created issue without deleting, rolling back, or rewriting them.

## Ticket and root checkpoints

After a ticket passes acceptance and review, is integrated, and its commit is pushed, confirm the existing ticket review checkpoint remains. After that checkpoint is approved, confirm ticket and root progress status sync runs without another pause or approval.

After all tickets, confirm the workflow runs final verification and root review, syncs the root issue status before the separate root completion checkpoint, then presents the evidence and waits for explicit completion approval. If the root is already synced as complete while approval is pending, confirm it remains complete; if work resumes, confirm the next status sync reopens it. Confirm issue creation, comments other than the authorized graph comment, labels, PR operations, and other non-status writes retain their approval gates.

## Self-contained behavior

Confirm the workflow contains the behavior it requires and does not require or directly invoke `/implement-spec`.
