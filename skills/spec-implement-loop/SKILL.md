---
name: spec-implement-loop
description: Run an explicitly approved root spec or ticket tree through implementation, verification, commit, push, status sync, and bounded review remediation.
disable-model-invocation: true
---

# /spec-implement-loop

## Activation Criteria & Objective

Run an explicitly approved root spec or ticket tree to verified delivery in the current branch or worktree. Keep the scope to the supplied roots and stop at approval, ambiguity, security, permission, or external-state gates.

## Dependencies

When this skill's own workflow explicitly reaches a call to one of its directly declared Skill prerequisites, the call is explicit and may proceed even if that prerequisite disables implicit invocation. This waives only that invocation gate. It does not waive other prerequisite instructions or confirmation, authorization, security, or safety gates. It does not authorize transitive calls, create new call steps, or override an explicit prohibition on invoking another skill.

If any dependency is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

| Name | Type | Source |
| --- | --- | --- |
| /implement | Skill | https://github.com/mattpocock/skills |
| /tdd | Skill | https://github.com/mattpocock/skills |
| /code-review | Skill | https://github.com/mattpocock/skills |
| /grill-duo-with-docs | Skill | https://github.com/EltonZhang777/AggregateSkills |
| /to-spec | Skill | https://github.com/mattpocock/skills |
| /to-tickets | Skill | https://github.com/mattpocock/skills |
| /setup-matt-pocock-skills | Skill | https://github.com/mattpocock/skills |
| /parallel-code-review | Skill | https://github.com/EltonZhang777/AggregateSkills |
| /conventional-git-messages | Skill | https://github.com/EltonZhang777/AggregateSkills |
| /show-me | Skill | Not declared |
| /archify | Skill | Not declared |
| SkillRoute CLI | Tool | https://github.com/erichare/skillroute |

## Preflight

After every dependency in the table is available, complete the repository and tracker checks before ticket work. Read each original skill file before invoking it; reading permits source access only. Follow invocation metadata, including user-confirmation, authorization, and clarification gates, and load the original file again at its workflow step when needed. Verify the configured issue-tracker files and vocabulary required by `/to-spec` and `/to-tickets`, using `/setup-matt-pocock-skills` as the source. Do not run setup automatically. If setup or tracker configuration is missing or invalid, stop.

Also require:

- a clean worktree;
- a non-detached current branch;
- a resolvable task remote and branch-to-remote mapping; a new remote ref may be created by the task's first push.

Record the starting `HEAD` for review and commit accounting. Do not re-check dependency origins over the network during normal execution.

## Plan the graph and reusable worktree pool

Before implementation starts:

1. Read the root, every explicitly linked ticket, comments and labels, and each ticket's native blocker edges. Add external blockers to the graph, but count only implementation items: child tickets and a root only when it is itself selected as the implementation item. Exclude an aggregating root and external blockers. Draw blocking edges from blocker to blocked ticket; show parent links as dashed, non-blocking edges. Stop on missing or contradictory issue evidence or a dependency cycle.
2. Calculate the graph's width: the largest set of implementation tickets where no ticket depends on another, directly or transitively. This is the maximum planned parallel ticket count. For a larger graph, compute the width as the ticket count minus a maximum matching on the transitive-closure bipartite graph; do not estimate from the total ticket count. If the exact width is unclear, stop and report the graph.
3. Publish the complete Mermaid graph as a root issue comment before assigning tickets. An explicit root-spec authorization covers this graph comment only. Confirm publication or reconcile its result before continuing; other comments and issue writes keep their approval gates.
4. Designate one root-specific integration branch and worktree. Reuse a current worktree only when it is clean, is under the repository's required `.wt` directory, and is already on a root-specific branch mapped to the task remote. Otherwise create a dedicated integration worktree under `.wt` on a root-specific branch such as `issue-147-<feature-slug>`, distinct from its source branch, with the exact task-remote upstream mapping.
5. Create one stable worker worktree per planned parallel slot under `.wt` before assigning any ticket. On resume, reconcile and reuse the existing integration worktree and slots; preserve dirty or uncertain work. Do not create more worker slots than the graph width.
6. Prepare only tickets whose explicit blockers are closed and whose acceptance criteria, required approvals, permissions, and environment are ready. Assign each ticket a fresh local, ticket-specific branch from the latest integration tip in an available stable slot. Apply the repository's upstream mapping rule without pushing worker branches. Do not start implementation conversations yet.
7. Freeze the complete selected root set and ticket plan, then request one task-start authorization for the batch before dispatching any implementation task. List every root/spec, repository, integration branch and worktree, planned ticket assignment and worker branch/worktree, permitted Git action categories and exact target refs, issue-write categories and exact issue targets, and every planned cross-root operation with its source and destination. Dispatch nothing until one grant covers all required scope; unlisted actions and resources remain gated. If approval is pending or declined, or the grant is incomplete because it omits any required resource or action, dispatch no implementation conversation and pause the affected batch until the user approves the complete scope. Do not fall back to per-root authorization requests. If required scope is missing or later changes, pause the affected work and obtain renewed authorization before dispatch or the uncovered write. For multi-root runs, Section 3 of the multi-root coordination reference specifies this same single request; do not request again in the main path or once per root. After approval and any required batch-wide scheduling limit, dispatch only ready tickets within the grant. Give each worker only the part of the grant that applies to its ticket's named resources and permitted actions; a worker must not rely on another ticket's authorization. Workers edit and verify only their assigned scope under that grant; only the coordinator changes branches, commits, integrates, or pushes.
8. After acceptance and review, the coordinator captures the complete worker diff and applies it to the latest integration tip; mark new files intent-to-add before capture so they are included. Resolve only in-scope conflicts, rerun relevant checks, and create one focused commit on the integration branch. Push only that branch. After the push is confirmed, complete the internal ticket checkpoint and status sync under the batch grant. Reuse the slot only when another ticket enters the current ready frontier, the worker has no post-review or unrelated changes, and the captured ticket changes are confirmed in the latest integration history. Use path-scoped `git restore --source=<latest-tip> --staged --worktree -- <captured-paths>` in the worker slot; never reset or clean the whole worktree. Then create the next ticket's fresh branch from that tip using a normal branch switch and verify the slot is clean. If any unreviewed change remains, the slot stays dirty, or patch application/integration is uncertain, preserve the slot and reconcile.

The task-start grant covers only the named roots/specs, repositories, branches/worktrees, action categories, and issue targets. It may authorize focused integration commits and ordinary non-force pushes only to listed integration branches, including the initial push that creates a matching remote ref; worker branches remain local and unpublished. It may authorize status synchronization only for listed root/ticket issues in the repository containing each root and at the documented checkpoints. Status-sync authorization changes issue status only; it does not authorize issue creation, comments other than the graph comment explicitly authorized in step 3, labels, sub-issue links, unlisted merges, pull requests, or other GitHub writes. A cross-root base or merge is authorized only when the exact source root and branch, dependent root, destination branch or worktree, and operation are listed. The grant does not authorize force-pushes, remote-ref deletion, unlisted branches or resources, or unlisted issue-write categories. Do not fall back to per-root authorization requests. Scope changes require renewed authorization for affected work; a narrower instruction takes precedence.

Ticket and root status-sync writes use the same bounded retry rules: reconcile an uncertain outcome before retrying, retry only transient failures up to three total attempts, and do not retry permanent failures. Preserve confirmed independent status updates if a later status sync fails; do not roll them back.

After an interruption, re-read the root and ticket graph, then reconcile the integration and worker worktrees, branches, local commits and changes, upstream mappings, and exact remote integration ref. Never repeat a commit, push, or issue write until evidence proves whether it succeeded.

## Root-run lifecycle

Track the active root, ticket, lifecycle state, and resume point in the current session. Reconstruct them from the authoritative source after interruption; do not create a local authoritative state database. The table is a navigation map: the linked rules define transitions and gates.

| State | Artifacts | Canonical rules |
| --- | --- | --- |
| intake | Approved input; graph comment; integration worktree; worker slots | [Graph and worker-pool planning](#plan-the-graph-and-reusable-worktree-pool); [Intake and frontier](#intake-and-frontier) |
| ready | Frozen batch; task-start authorization; ticket branches | [Graph and worker-pool planning](#plan-the-graph-and-reusable-worktree-pool) |
| implement | Ticket diff in its worker slot | [Issue loop](#issue-loop) |
| verify | Acceptance and verification evidence | [Issue loop](#issue-loop) |
| review | Ticket review; final-review manifest; complete, blocked, or incomplete track reports | [Final-review invocation](#final-review); [complete-report handoff](references/final-review-remediation.md#complete-report-handoff) |
| remediate | Approved repair tickets and diffs | [Remediation procedure](references/final-review-remediation.md#remediation-procedure) |
| commit | Focused integration commit | [Graph and worker-pool planning](#plan-the-graph-and-reusable-worktree-pool); [Issue loop](#issue-loop) |
| push | Confirmed remote integration ref | [Issue loop](#issue-loop) |
| ticket_checkpoint | Ticket acceptance, review, commit, and push evidence | [Issue loop](#issue-loop) |
| status_sync | Synced ticket status; ready frontier | [Issue loop](#issue-loop) |
| root_exception | One-track partial result; per-root exception; append-only record | [Partial results and per-root exceptions](references/final-review-remediation.md#partial-results-and-per-root-exceptions); [permanent append-only records](references/final-review-remediation.md#permanent-append-only-records) |
| root_status_sync | Synced root status | [Retry and reconciliation](references/final-review-remediation.md#retry-and-reconciliation); [completion gate](references/final-review-remediation.md#completion-gate) |
| root_checkpoint | Final evidence; completion approval | [Completion gate](references/final-review-remediation.md#completion-gate) |
| blocked | Reason class; evidence; recovery condition; safe resume state | [Issue loop](#issue-loop) |
| completed | Completed-ticket, verification, review, push, and status evidence | [Completion and report](#completion-and-report); [completion gate](references/final-review-remediation.md#completion-gate) |

Classify dependency when a required blocker remains unsatisfied; technical for an implementation or verification failure; external-service for a known service or network failure; operator-decision when a required user decision is unresolved, such as approval for a non-status issue write or pull request; decomposition when scope needs further ticketing; and needs-reconcile when a side-effect result is uncertain. A review repair uses remediate, not a generic blocked state. A blocker pauses only its dependent work.

Ticket review checkpoints are internal workflow reviews and do not require human approval. Follow the [completion gate](references/final-review-remediation.md#completion-gate) for final-review and root-completion approvals. All other GitHub writes retain their existing approval gates.

For GitHub inputs, the Issue task contract and native dependency edges are authoritative; use the ready guard above when checking dependency completion. Read comments and labels as relevant evidence. Keep durable decisions, blocker evidence, and handoffs in the repository-approved Issue record; never overwrite an Issue body as a progress log or add status labels. For inline and local-file inputs, the supplied source remains authoritative. Session lifecycle state is temporary execution state, not a second source of truth.

After a restart or interruption, before resuming any status write, re-read and reconcile the supplied root, ticket context, and target GitHub repository, including relevant issue comments, labels, child links, and dependency edges. Inspect the current integration and worker worktrees, branches, local commits and changes, upstream mappings, and exact remote ref before resuming. Before retrying an operation whose result is uncertain, reconcile its authoritative evidence. If confirmed successful, continue without repeating it; if confirmed not applied, retry only a clearly transient operation within its bound; if unresolved, stop with needs-reconcile. Never repeat a commit, push, or issue write until reconciliation proves it did not succeed.

## Intake and frontier

Accept one or more inline specs, local spec/ticket paths, or GitHub issue URLs/identifiers. After read-only intake and deduplication, if more than one distinct root remains, follow the [multi-root coordination reference](references/multi-root-coordination.md). With one root, continue the single-root workflow below. This skill remains authoritative for procedures shared by both paths.

Discover descendants only from explicit parent/child links, checklists, issue links, or blocking/dependency edges. Do not infer tickets from titles or invent relationships.

- Treat a root itself as an implementation item when it has clear acceptance criteria and is a manageable size.
- If a root is clearly too large for one implementation round, pause and ask for approval to load and run `/to-tickets`.
- If a root is only planning material and has no clear acceptance criteria, pause and report; do not create tickets automatically.

Use the source-specific ready guard above. Fill the planned worker pool from the current ready frontier, prioritizing dependency order and then root order or issue number. Run independent ready tickets concurrently up to the calculated pool width. Exclude tickets generated and marked `deferred` during the current run.

## Issue loop

For new or materially rewritten project text, use only the normative prose in the root `AGENTS.md` of the target repository receiving that text. When source and target differ, do not use the source or installation `AGENTS.md` as target policy; when they are the same repository, the shared root is the target rule. If the target differs from the current checkout, read the target's root file before drafting. Pause if the target rule has no discernible dominant language, preserve untouched text, and report resulting language mixtures. Pass the target rule to `/grill-duo-with-docs`, `/to-spec`, `/to-tickets`, and `/conventional-git-messages` whenever invoked.

For each ready ticket:

1. Assign a fresh ticket-specific branch in an available worker slot from the latest integration tip. Read and follow the original `SKILL.md` for `/implement`; use its `/tdd` and `/code-review` discipline at the agreed seams. Ticket review remains on this `/code-review` path and does not invoke `/parallel-code-review` or add a second review track. Workers change only the assigned ticket files and do not switch branches, stage, commit, or push.
2. Run the ticket's acceptance checks and specified verification. Review the full ticket change. If a check fails, enter `blocked` with the cause, evidence, and safe resume point. Resume a technical fix only when it stays within the approved scope.
3. Read the original `SKILL.md` for `/conventional-git-messages` and use its commit mode. Resolve `/show-me` or `/archify` dynamically and use its smallest useful view to explain the commit's effect with the missing context restored.
4. After acceptance and review pass, follow step 8 in the graph plan to integrate the complete reviewed worker diff, including new files. Reconcile Git first if any result is uncertain; stop and preserve the slot if unrelated or uncommitted changes remain or a conflict cannot be resolved within scope.
5. Push the confirmed commit to the exact integration branch. For a confirmed transient failure, choose a retry count based on the error, capped at three total attempts for the same ref and commit including the first. Do not retry permanent or unsafe-to-repeat errors. Reconcile an uncertain result before retrying. Never amend, force-push, or rewrite history. After retries fail, stop and report the local commit and error.
6. After the internal ticket review and confirmed authorized push, sync the completed ticket's status under the task-start grant; this checkpoint does not wait for human approval. Immediately before writing new or materially revised Issue titles, bodies, or comments, invoke `/conventional-git-messages` to draft the text, supplying the known facts and target repository's root `AGENTS.md` language rule. Metadata-only status updates do not require a drafting call. Apply the shared bounded retry rules to status sync. Do not roll back pushed code.
7. Return to the ready frontier after status sync and follow the slot-reuse procedure in the graph plan. When no non-deferred eligible ticket remains, run final verification and root review, then follow the [final-review remediation reference](references/final-review-remediation.md) for handoff, partial results, permanent records, retry and reconciliation, and the [completion gate](references/final-review-remediation.md#completion-gate). If a decision, preference, permission, security concern, or scope boundary is unclear, stop and load the original `SKILL.md` for `/grill-duo-with-docs`. A purely local, objective blocker may be recorded and skipped while independent ready tickets continue; do not bypass a user decision.

## Final review

When no non-deferred ready ticket remains, resolve the recorded starting `HEAD` and the final `HEAD` to full commit object IDs with `git rev-parse --verify`, then read and follow the original `SKILL.md` for `/parallel-code-review` before invoking it. Call `/parallel-code-review` exactly once for that final-review round with `--range <starting-oid>...<final-oid>`, using those exact object IDs rather than branch or tag names.

Pass `--require-requirements` when freezing the final-review scope. After freezing, require `manifest.input_status.requirements` to be `included`.

Before freezing, require `git merge-base <starting-oid> <final-oid>` to equal `<starting-oid>`. If the command fails or returns another object, block without re-basing or substituting a merge-base. After freezing, require `manifest.scope.base` and `manifest.scope.merge_base` to equal `<starting-oid>` and `manifest.scope.head` to equal `<final-oid>`; any mismatch blocks before dispatch.

Before freezing, materialize only non-file requirement inputs outside the reviewed repository. For each GitHub issue, write the exact issue body and each applicable comment that adds a requirement, decision, correction, or accepted clarification as a separate UTF-8 file; name it with its source identity and content hash, and reuse identical content or use a round-qualified name. Pass those files with repeatable `--requirements`; pass local requirement files by their original paths. For `--standards`, pass the documented source paths directly: applicable root and nested `AGENTS.md`; root `GLOSSARY.md` or `GLOSSARY-MAP.md` and each relevant glossary it names; `docs/agents/domain.md`; applicable ADRs; formatter, lint, type-check, build, and test configuration; and any additional standards source required by `/parallel-code-review`, its routed adapters, or the target repository's documentation. Do not create a second content-addressed standards snapshot layer; `freeze` copies and hashes every supplied requirement and standards input into the bundle, and the manifest remains the hash record. If a source changes, re-freeze from the original standards paths and refreshed requirement materialization; do not reuse stale inputs.

Pass each final verification result as repeatable `--check NAME=RESULT` with `passed`, `failed`, or `not_assessed`, or as `--not-run NAME=REASON` when it was not run; do not omit a required result. Pass every excluded source and its non-empty reason as repeatable `--exclude PATH=REASON`. Verify `manifest.checks` and `manifest.exclusions` contain exactly those recorded entries before dispatch.

The [final-review remediation reference](references/final-review-remediation.md) is the sole normative source for the final-review completion gate, complete-report handoff, preservation of blocked and incomplete reviews, the distinction between a one-track partial result and a per-root exception, permanent append-only records, approval ordering, and retry and reconciliation. After every round, follow its [complete-report handoff](references/final-review-remediation.md#complete-report-handoff) and [completion gate](references/final-review-remediation.md#completion-gate).

## Completion and report

Report `complete` only when all of these hold:

- no uncompleted, non-deferred ticket remains;
- every completed ticket meets its acceptance criteria;
- the full suite required by `/implement` passes after the final implementation batch;
- the [final-review completion gate](references/final-review-remediation.md#completion-gate) passes;
- every approved P0/P1 repair is complete;
- low-priority findings are recorded as deferred tickets;
- root and ticket statuses are synchronised;
- the root checkpoint is approved.

Otherwise report `waiting for approval`, `blocked`, or `failed`, with the exact condition.

The final report includes root and ticket states, test evidence, review-round count, deferred ticket identifiers, blockers or required approvals, and every commit in oldest-to-newest order. For each commit, use `/show-me` or `/archify` to explain its effect with the missing context restored. Use `/show-me` or `/archify` for the final summary, explaining the delivered result with the missing context restored.
