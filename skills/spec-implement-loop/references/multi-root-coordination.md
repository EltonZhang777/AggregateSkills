# Multi-root coordination

Use this reference only when read-only intake and deduplication in the [main skill](../SKILL.md) leave more than one distinct candidate root. The main skill remains authoritative for shared procedures; this reference defines the multi-root stages from listing through batch completion. If the documents conflict, pause only affected roots and ask the user. The caller must not edit skill documents during the run.

## 1. List and validate roots

- Follow the main skill's [intake and frontier](../SKILL.md#intake-and-frontier) rules to identify roots and discover descendants from explicit issue evidence. Do not infer roots, tickets, or relationships.
- Present the proposed root-to-ticket mapping with root entries in issue-number order; within each root, list explicitly referenced child tickets in issue-number order. Include tickets without native sub-issue links, cite each child reference, show blocker edges separately, and preserve each root's source.
- Before asking to create sub-issue links, detect child tickets listed under multiple roots. Show each overlap and its affected roots; ask the user to choose one owning root or decompose the ticket. Pause only affected roots until resolved, while unaffected roots may continue under their existing authorizations. Do not link an overlapping ticket until ownership or decomposition is resolved; refresh the mapping after resolution.
- Mark each ticket described as a child task when it lacks a native GitHub sub-issue link to its root. Ask once whether to link all missing cases in the validated roots or a specified subset. Create only approved links, verify the resulting native links, and return to the complete root-to-ticket listing before selection.
- If evidence is contradictory, a dependency cycle exists, or documentation conflicts, pause the affected root with the evidence and resume condition. Continue safe independent roots.

## 2. Select and freeze the batch

- Ask the user to select eligible roots from the complete, validated listing. If only one root remains selected, continue the main skill's single-root flow with that validated root: apply its [root readiness checks](../SKILL.md#intake-and-frontier), then its [graph and worker-pool procedure](../SKILL.md#plan-the-graph-and-reusable-worktree-pool). Do not restart candidate-root intake or the multi-root selection.
- When multiple roots remain, freeze that selected set at batch-start approval. A newly discovered root stays out of the batch until the user approves the scope change and renewed batch start.

## 3. Prepare and authorize the batch

- Before requesting batch-start approval, follow the main skill's [graph and worker-pool procedure](../SKILL.md#plan-the-graph-and-reusable-worktree-pool) for every selected root. Resolve and verify its current integration branch and required worktree; confirm the existing task-scoped write authorization and record its exact scope. Record explicit prerequisite edges, calculate graph width, and size the stable worker slots to that width. Prepare or reconcile only worktrees whose bases do not require cross-root operations, using coordinator-selected bases; do not disturb active workers. Before dependent work is dispatched, refresh a clean idle slot from the latest target integration branch; wait if no safe slot is available.
- Resolve every explicit cross-root dependency into a specific source-root-to-dependent-root operation. Name the source root and branch, the dependent root and exact destination branch or worktree, and whether the operation creates a dependent ticket branch from the source or merges the source branch into the dependent integration branch.
- Request one batch-start approval listing the frozen roots, each root's integration branch and required worktree, planned worker implementation conversations and ticket assignments, each root's task-scoped write scope, and every specific cross-root operation. Do not create or start implementation conversations before this approval. After approval, perform only the listed cross-root operations, prepare all required worktrees on the bases recorded in the plan, and then create or start the planned conversations. The approval authorizes only the listed cross-root operations in addition to the existing per-root grants; all other Git and GitHub writes keep the main skill's approval gates.
- Perform cross-root base or merge operations only when [ADR-0003](../../../docs/adr/0003-task-scoped-write-authorization.md) or an explicitly superseding decision documents this narrow scope and the batch-start approval names each operation and its refs. The ADR sets the boundary; the approval names the operations. Preserve the existing per-root authorization limits.
- Ask once for the implementation-conversation parallel limit before the first dispatch. Recommend unlimited or four, then apply the chosen limit to dispatches and refills throughout the batch.

## 4. Schedule queues and gate prerequisites

- Keep each root's queue independent unless an explicit dependency joins them. Fill safe worker slots from eligible queues in dependency order, then supplied root order and issue number. Follow the main skill's [ticket loop](../SKILL.md#issue-loop) for implementation, integration, review, and checkpoints.
- Dispatch a dependent ticket only after its prerequisite changes have been reviewed and integrated into the source root branch, then merge that branch into the dependent root as authorized. Do not wait for the source root's full queue or final acceptance. A blocked prerequisite pauses only dependent work; continue other roots with ready tickets.
- When roots are waiting for capacity, check quietly no more often than every 15 minutes and fill newly available slots. Stop these checks once every approved root has an implementation conversation.

## 5. Track acceptance, closure, and rework

- Keep tracking every selected root through final acceptance and root close. A root releases its worker slot at `root_checkpoint`; waiting for final acceptance or closure does not hold a slot. Use the main skill's [root-run lifecycle](../SKILL.md#root-run-lifecycle), [ticket loop](../SKILL.md#issue-loop), and [final review](../SKILL.md#final-review) for each root.
- In-scope acceptance rework returns to the current batch and the same parallel limit. Out-of-scope rework, scope expansion, or adding a root pauses for renewed authorization.
- If a newly found root blocks only some selected roots, pause those roots and continue unaffected roots. Do not silently expand the frozen batch.

## 6. Complete the batch

The batch stays open until every selected root has reached its completion checkpoint and root close. Confirm each root's acceptance, required reviews, and status synchronization through the main skill's [completion and report procedure](../SKILL.md#completion-and-report); then report the batch complete.
