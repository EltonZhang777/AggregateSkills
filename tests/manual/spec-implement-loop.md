# `/spec-implement-loop` manual scenarios

Run these through the user-visible skill invocation in a disposable repository with test issues and branches. Do not use a production repository. In scenarios checking non-status write gates, withhold approval for issue creation, comments, labels, pull requests, and merges. The graph comment may proceed only under the approved root-spec scenario.

## Graph planning and reusable worktree pool

Create a root with three implementation tickets: #101 and #102 are independent; #103 is blocked by #101. Have #101 add a new file and modify an existing one. Start the skill and confirm it reads all explicit child links, issue comments, labels, and native blocker edges before scheduling. Confirm it publishes the complete blocker-to-blocked Mermaid graph on the root before assigning work, with the parent link shown as non-blocking and without a separate comment-approval pause.

Confirm the graph width is two, and that one root-specific integration worktree and two stable worker worktrees under `.wt` exist before either worker starts. Confirm worker branches are fresh, ticket-specific, local, and based on the latest integration tip. Before dispatch, confirm one task-start authorization lists the root/spec, repository, integration branch/worktree, planned assignments and worker branches/worktrees, permitted Git action categories and target refs, issue-write categories and target issue numbers, and planned cross-root operations. No worker starts while authorization is pending, and unlisted scope remains gated. Confirm the applicable grant is included with each worker assignment. Only #101 and #102 may start; #103 remains blocked until #101 is completed and its status is synced.

With ticket A and ticket B assigned different resources and actions, confirm each worker receives only the relevant part of the batch grant, and that attempts to use a sibling ticket's resources or authorization are blocked. In separate runs, leave authorization pending, explicitly declined, or incomplete because it omits a required resource or action; confirm no worker or implementation conversation starts or is dispatched until the user approves complete scope.

Start #101 and #102 in parallel. Finish #101 first while #102 is still running. Confirm the coordinator captures #101's complete reviewed diff, including the new file, applies it to the latest integration tip, reruns checks there, commits once on the integration branch, and pushes it. After the ticket checkpoint and status sync, confirm the coordinator verifies that #101's captured changes are in the latest integration history and no post-review edits remain, restores only #101's captured paths from the latest integration tip, and creates a fresh branch from the latest tip; confirm the slot is clean and has no uncommitted copy before #103 starts. If any captured change is absent from integration or any unreviewed change remains, preserve the slot and do not assign #103 there. Finish #102 and #103; confirm the coordinator alone changes branches, commits, integrates, and pushes the integration branch. Worker branches are never published. If patch application conflicts or the slot remains dirty, confirm the coordinator preserves the evidence and pauses instead of resetting or cleaning it.

## Multi-root routing, overlap, and batch completion

In one disposable run, provide several candidate roots but select only one after the read-only listing and deduplication. Confirm the workflow returns to the single-root path and still requests one task-start authorization for that frozen root before dispatch, with no additional per-root grant. In another run, select roots A and B with child #122 referenced under both, plus independent root C with child #124. Make #122's current native parent A and leave #124 without a native parent link. Confirm the complete mapping exposes #122's overlap before any link request, asks whether to assign or decompose it, pauses only A and B, and lets safe work in C continue. After the user assigns #122 to B, confirm the workflow shows the current and intended parent and asks for separate approval to change that relationship; approval for missing links must not cover this change. If supported tooling cannot apply and verify the approved change, confirm the workflow pauses for the user to resolve it rather than substituting another operation. Resume A or B only after a read-only authoritative check confirms the chosen parent; if it cannot be verified, keep them paused. After verification, refresh the complete mapping, then ask once for approval to create the remaining missing link for #124; create only that approved link and verify it.

Make B's ticket depend on prerequisite code from A. Give the coordinator ambiguous source-branch information and confirm it asks which existing source and destination branches to use, pauses B, and does not infer or perform a merge. Before dispatch, confirm one task-start authorization request lists the frozen roots/specs, each repository, integration branch and worktree, planned conversations, ticket assignments and worker branches, permitted Git action categories and target refs, issue-write categories and target issues, and the exact A-to-B integration-branch merge. Confirm no implementation conversation starts until the grant covers all listed scope and no separate per-root authorization is requested. After the user names the merge, confirm it succeeds before B's dependent ticket is dispatched; creating a ticket branch from A alone is not enough. Before the first implementation conversation, ask once for the batch-wide limit; choose two, then confirm no more than two conversations run at once, the workflow recommends unlimited or four, and it refills safely on the agreed 15-minute cadence. Pass the applicable grant with each worker assignment. A root at `root_checkpoint` releases its slot. A newly discovered root stays outside the frozen batch until renewed authorization; in-scope rework keeps the current limit, while out-of-scope rework pauses for renewed scope approval.

Introduce a conflict between the main skill and its multi-root reference for A while C remains safe. Confirm A pauses with the conflict explained, the caller does not edit skill documents, and C continues. Keep the batch open until every selected root reaches final acceptance and close; confirm status synchronization does not authorize comments, labels, new links, pull requests, or other non-status writes.

## Reuse or prepare the integration branch

Start once in a clean `.wt` worktree on a root-specific branch, and once on a shared development branch such as `dev` or `experimental`. Confirm the first run reuses its suitable `.wt` worktree as the integration worktree. In the second run, confirm it prepares a dedicated integration branch and worktree under `.wt` from the clean checked-out `HEAD`, distinct from the source branch. Supply repository or agent naming conventions with a preferred prefix, then use a root-specific name such as `<prefix>/issue-147-<feature-slug>` without hard-coding one prefix.

Confirm every integration worktree has the matching task-remote upstream, including when the initial push creates that ref. Confirm worker branches have matching upstream configuration but are never pushed. Reconcile divergent or uncertain remote state; never force-push.

Start with uncommitted work or conflicting issue evidence and an unresolved engineering choice. Confirm the workflow preserves dirty work and pauses on ambiguity instead of switching branches or guessing.

## Readiness guards

Create a ticket whose explicit blockers are closed but whose acceptance criteria are ambiguous, and another whose required permission or environment is unavailable. Confirm neither is assigned until its gap is resolved; continue only with an independent ticket whose blockers, acceptance criteria, permissions, approvals, and environment are ready.

## Task-scoped commits and pushes

Prepare one root and two small tickets, then approve one task-start authorization listing the root, repository, integration branch/worktree, ticket assignments and worker branches/worktrees, focused commits and normal pushes to the integration ref, and status sync for the root and those tickets. Confirm no ticket starts before approval, each ticket gets one focused integration commit after acceptance and internal review, and its confirmed commit is pushed without another commit or push prompt. Confirm ticket status sync follows the internal review and confirmed push under the same grant, with no per-ticket authorization request.

In a separate run, give an instruction explicitly limited to review, with no approved root implementation scope. After reviewing a patch, confirm that review permission does not authorize an integration commit or push and the workflow pauses for the applicable authorization.

With the supplied root in Repository A, include one in-repository ticket and one cross-repository ticket in Repository B. Confirm status sync changes only the root and in-repository ticket issue statuses in Repository A, only at the documented ticket and root status checkpoints; the Repository B ticket stays unchanged. Confirm status-sync authorization does not permit issue creation, comments, label changes, sub-issue links, PR creation, merges, or any other GitHub write. Finish the root, then start an unrelated root and confirm the prior authorization does not carry over.

## Interruption and reconciliation

Interrupt once after a commit and once after a push, then resume the same root. Before resuming any status write, confirm the workflow re-reads and reconciles the supplied root, ticket context, and target GitHub repository. Also reconcile the issue graph and the integration and worker worktrees, branches, local commits and changes, upstream mappings, and exact remote ref before continuing. It must not repeat a confirmed commit or push. For an outcome that cannot be established, confirm it blocks and asks for reconciliation.

## Push retries and partial results

In separate runs, inject clearly transient, permanent, and uncertain failures for pushes and ticket/root status-sync writes. Confirm transient retries stop at three total attempts, permanent failures are not retried, and uncertain push or status-write results are reconciled against remote state before retry. Complete one ticket and confirm its status sync, then fail a later independent status sync; confirm the earlier confirmed status, integration commit, remote branch, and any created issue remain without deletion, rollback, or rewrite.

## Ticket and root checkpoints

After a ticket passes acceptance and review, is integrated, and its authorized commit is pushed, confirm the ticket review checkpoint completes internally without waiting for human approval. Then confirm ticket status sync runs under the batch grant without another pause. If the grant omits that issue or status-write category, confirm the workflow stops before the write and requests renewed authorization.

After all tickets, confirm the workflow runs final verification and root review, syncs the root issue status before the separate root completion checkpoint, then presents the evidence and waits for explicit completion approval. Confirm status sync itself does not satisfy the completion checkpoint. If the root is already synced as complete while approval is pending, confirm it remains complete; if work resumes, confirm the next status sync reopens it. Confirm non-status GitHub writes retain their approval gates.

## Self-contained behavior

Confirm the workflow contains the behavior it requires and does not require or directly invoke `/implement-spec`.
