---
name: spec-implement-loop
description: Run an explicitly approved root spec or ticket tree through implementation, verification, commit, push, status sync, and bounded review remediation.
disable-model-invocation: true
metadata:
  prerequisites: '{"skills":[["implement","mattpocock/skills"],["tdd","mattpocock/skills"],["code-review","mattpocock/skills"],["grill-duo-with-docs","mattpocock/skills"],["grilling","mattpocock/skills"],["domain-modeling","mattpocock/skills"],["to-spec","mattpocock/skills"],["to-tickets","mattpocock/skills"],["setup-matt-pocock-skills","mattpocock/skills"],["ponytail-review","DietrichGebert/ponytail"],["conventional-git-messages","EltonZhang777/AggregateSkills"]],"mcps":[],"tools":[]}'
---

# /spec-implement-loop

Run the user's root spec(s) to verified delivery in the current branch or worktree. Keep the scope to the supplied roots and stop at approval, ambiguity, security, permission, or external-state gates.

## Preflight

Complete every check before doing any work; report all failures together and stop on any failure.

Required skills:

- `mattpocock/skills`: `/implement`, `/tdd`, `/code-review`, `/grill-duo-with-docs`, `/grilling`, `/domain-modeling`, `/to-spec`, `/to-tickets`, `/setup-matt-pocock-skills`
- `DietrichGebert/ponytail`: `/ponytail-review`
- `EltonZhang777/AggregateSkills`: `/conventional-git-messages`

`/skill-creator`, `/writing-for-agents`, and `/grill-me` are authoring-time skills, not runtime dependencies.

For every required skill, resolve and read its original `SKILL.md` from the active skill roots regardless of whether a skill catalog exposes it or its invocation metadata permits automatic invocation. This exception permits source reading only. Before invoking a dependency, follow its invocation metadata and preserve all user-confirmation, authorization, and clarification gates in its instructions; if direct user invocation is required, pause at that gate. Load the original file again at its workflow step when needed. Never edit, copy, or paraphrase a dependency skill as a substitute.

If a declared source is missing or unreadable, stop and direct the user to the corresponding entry in the [prerequisite guide](../../docs/prerequisites.md). Do not install dependencies automatically.

Read the original `SKILL.md` for `/setup-matt-pocock-skills`, then verify the configured issue-tracker files and vocabulary it requires. Do not run setup automatically. If setup or tracker configuration is missing or invalid, stop.

Also require:

- a clean worktree;
- a non-detached current branch;
- a resolvable task remote and branch-to-remote mapping; a new remote ref may be created by the task's first push.

Record the starting `HEAD` for review and commit accounting. Do not re-check dependency origins over the network during normal execution.

## Task branch and Git authorization

Before editing a ticket, establish the task branch for its approved root or group:

- Reuse the current branch when it is dedicated to that same active task. Otherwise, create a dedicated branch from the clean checked-out `HEAD`; do not put task changes on a shared development branch such as `main`, `dev`, or `experimental`.
- Follow repository and active agent framework naming conventions as guidance. Do not require a fixed prefix or reject a suitable task branch solely because its name lacks one.
- When creating a worktree, use a branch distinct from its source branch. Configure its upstream to the repository's task remote (normally `origin`) and confirm the matching remote ref. If the remote ref does not exist, the task's first normal push creates it under the authorization below. Reconcile a divergent or uncertain remote state before continuing; never force-push.

Starting an explicitly approved root grants the main agent standing authorization for routine, focused commits and normal pushes of that task's branch. It includes branches and worktrees created for the same task and the initial push that creates their remote refs. Keep one focused commit per ticket, and publish only confirmed task commits to the exact task branch. This authorization ends when the assigned task is complete; it does not carry to unrelated roots or later tasks. It does not authorize issue, status, label, comment, pull request, or merge writes, branch deletion, rollbacks, force-pushes, or history rewrites. A narrower instruction from the user takes precedence.

After an interruption, resume this authorization only after reconciling the task source, worktree, branch, local commits, upstream mapping, and exact remote ref. A confirmed side effect is not repeated; an uncertain result blocks for reconciliation.

## Root-run lifecycle

The coordinator tracks the active root, ticket, lifecycle state, and resume point only for the current session. Reconstruct them from the authoritative source after interruption; do not create a local authoritative state database.

| State | Meaning and permitted transition |
| --- | --- |
| intake | Validate the approved input, complete preflight, and read its explicit issue graph. Move to ready only when at least one ticket meets the ready guard; unclear or oversized scope enters blocked. |
| ready | Select one ticket whose explicit blockers are satisfied, acceptance criteria are clear, and required permissions and environment are available. For GitHub, every blocking Issue must be closed. Move to implement. |
| implement | Change only the selected ticket's scope. Move to verify when the implementation is ready; a technical failure or scope decision enters blocked. |
| verify | Run the ticket's acceptance checks. Pass moves to review; failure enters blocked with the failing evidence and a safe resume point. |
| review | For a ticket, a passing review moves to commit; findings move to remediate only through the review approval gates. For the final root review, no findings moves to `root_checkpoint`. |
| remediate | Work only on approved review repairs through the normal ticket loop. Move to verify, then review the repaired batch; do not re-review a partial batch. |
| commit | After ticket checks and review pass, create exactly one focused commit under the task-scoped authorization. Reconcile Git first if the commit result is uncertain. Move to push only after the commit is confirmed. |
| push | Push the confirmed commit to the exact task branch under the task-scoped authorization. Follow the bounded retry rules in Issue loop; reconcile an uncertain result before retrying. Confirmed success moves to `ticket_checkpoint`; exhausted retries or an unreconciled result enters blocked. Never amend or rewrite history. |
| ticket_checkpoint | Present the ticket's acceptance, review, commit, and push evidence; pause for user review before declaring the ticket complete. After explicit confirmation, move to status_sync. Each issue/status write still needs its own explicit approval. |
| status_sync | After the ticket checkpoint, perform approved issue/status writes. Follow the bounded retries in Issue loop and reconcile uncertain results using the recovery rules above. Confirmed sync moves to ready for the next queue-ordered ticket that passes the ready guard, including a newly unblocked ticket, or to final review when the queue is drained. Exhausted retries or an unreconciled result enters blocked; never roll back pushed code. |
| root_checkpoint | After final verification and root review pass, present the evidence and pause for explicit user approval before declaring the root complete. Root issue/status writes still need their own explicit approval. Move to completed only after the checkpoint and required status sync are approved and confirmed. |
| blocked | Stop the affected dependency chain and record the reason class, evidence, recovery condition, and safe resume state. Resume only when the condition is met and relevant source and Git state have been reconciled. |
| completed | Every non-deferred ticket and approved review repair is complete; acceptance checks and the full suite pass; final review passes; required pushes and status syncs are confirmed; the root checkpoint is approved. |

Classify dependency when a required blocker remains unsatisfied; technical for an implementation or verification failure; external-service for a known service or network failure; operator-decision for missing approval or an unresolved user choice; decomposition when scope needs further ticketing; and needs-reconcile when a side-effect result is uncertain. A review repair uses remediate, not a generic blocked state. A blocker pauses only its dependent work; continue another independent root queue when it has a ready ticket.

A missing approval for an issue/status or pull request action is operator-decision: pause at that operation and do not perform the write until approval is given. Routine task commits and pushes use the standing authorization above, subject to any narrower user instruction. This lifecycle adds no PR or merge gate.

For GitHub inputs, the Issue task contract and native dependency edges are authoritative; use the ready guard above when checking dependency completion. Read comments and labels as relevant evidence. Keep durable decisions, blocker evidence, and handoffs in the repository-approved Issue record; never overwrite an Issue body as a progress log or add status labels. Issue/status writes still require explicit approval. For inline and local-file inputs, the supplied source remains authoritative. Session lifecycle state is temporary execution state, not a second source of truth.

After a restart or interruption, re-read the authoritative input (Issue, local file, or supplied inline spec). For GitHub inputs, also re-read the relevant Issue comments, labels, explicit child links, and dependency edges. Inspect the current branch, worktree, local commits, upstream mapping, and exact remote branch state before resuming. Before retrying an operation whose result is uncertain, reconcile the relevant Issue and local/remote Git evidence. If the operation is confirmed successful, continue from its next state without repeating it. If confirmed not applied, retry only a clearly transient operation within its bound. If its result cannot be established, enter blocked with needs-reconcile and stop for user input. Never repeat a commit, push, or Issue/status write until reconciliation proves it did not succeed.

## Intake and frontier

Accept one or more inline specs, local spec/ticket paths, or GitHub issue URLs/identifiers. Preserve each root's source and keep multiple roots as independent queues unless an explicit dependency joins them.

Discover descendants only from explicit parent/child links, checklists, issue links, or blocking/dependency edges. Do not infer tickets from titles or invent relationships.

- Treat a root itself as an implementation item when it has clear acceptance criteria and is a manageable size.
- If a root is clearly too large for one implementation round, pause and ask for approval to load and run `/to-tickets`.
- If a root is only planning material and has no clear acceptance criteria, pause and report; do not create tickets automatically.

Use the source-specific ready guard above. Process one ready ticket at a time, preferring dependency order and then the root's order or issue number. Exclude tickets generated and marked `deferred` during the current run.

## Issue loop

For new or materially rewritten project text, use only the normative prose in the root `AGENTS.md` of the target repository receiving that text. When source and target differ, do not use the source or installation `AGENTS.md` as target policy; when they are the same repository, the shared root is the target rule. If the target differs from the current checkout, read the target's root file before drafting. Pause if the target rule has no discernible dominant language, preserve untouched text, and report resulting language mixtures. Pass the target rule to `/grill-with-docs`, `/domain-modeling`, `/to-spec`, and `/to-tickets` whenever invoked.

For each ready ticket:

1. Read and follow the original `SKILL.md` for `/implement`; use its `/tdd` and `/code-review` discipline. Implement only the ticket scope and use its agreed seams.
2. Run every acceptance check, including the smallest relevant tests and any other specified verification. If a check fails, enter `blocked` with the reason class selected by its cause (for example, an implementation or verification defect is `technical`, while a known service or network failure is `external-service`), and preserve the failure evidence and safe resume point. Resume only when the recorded recovery condition is met; resume implementation for a `technical` failure only when its correction stays within the approved scope, otherwise stop for the required user decision. Do not call the issue complete until its acceptance criteria, tests, and issue-level review pass.
3. Read the original `SKILL.md` for `/conventional-git-messages` and use its commit mode to produce the commit message. Resolve `/show-me` or `/archify` dynamically at this step and use its smallest useful view to explain the commit's effect with the missing context restored.
4. After acceptance checks and ticket-level review pass, create exactly one focused commit under the task-scoped authorization. The outer loop owns this commit boundary; treat `/implement`'s commit instruction as satisfied by this commit and never create a duplicate commit.
5. Push the confirmed commit to the task branch under the task-scoped authorization. For a confirmed transient failure, choose a retry count based on the error, capped at three total attempts for the same ref and commit including the first; do not retry permanent or unsafe-to-repeat errors. Before retrying an uncertain result, reconcile the local commit and exact remote branch state. Never repeat a confirmed successful push, amend, or rewrite history. After retries fail, stop and report the local commit and error.
6. After the ticket checkpoint and a confirmed push, update the completed ticket and root progress, with explicit approval for each tracker/status write. Any new or materially rewritten issue text must follow the target repository's root language rule; preserve untouched text and report resulting language mixtures. Retry only transient update failures, up to three total attempts including the first; reconcile uncertain results before retrying. If retries fail, stop and report that code is pushed but status is unsynchronised; do not roll back the code.
7. After status sync succeeds, continue with the next ticket that passes the ready guard, including newly unblocked tickets; enter final verification and root review when no non-deferred ready ticket remains. After the final root review passes, present the root checkpoint and wait before declaring completion. If a decision, user preference, permission, security concern, or scope boundary is unclear, stop and load the original `SKILL.md` for `/grill-duo-with-docs`. A purely local, objective blocker may be recorded and skipped while independent ready tickets continue; do not bypass a user decision.

## Final review and remediation

When no non-deferred ready ticket remains, review the complete target diff from the recorded starting `HEAD` with the original `SKILL.md` for `/code-review` and `/ponytail-review`.

If the reports contain no findings, finish the review phase without creating empty remediation artifacts. Otherwise, for each review round:

1. Read and follow the original `SKILL.md` for `/to-spec` using all review reports as input. Preserve its seam-confirmation gate before publication.
2. Read and follow the original `SKILL.md` for `/to-tickets`. Preserve its granularity, blocking-edge, and publication approval gates.
3. Classify findings while preserving the original report and rationale:
   - P0: data loss, severe security issue, unusable core flow, or inability to start/deploy.
   - P1: correctness, security, data-loss risk, explicit spec violation, or a blocker for the main acceptance path.
   - P2 or lower: all other findings, including pure over-engineering findings from `/ponytail-review`.
4. Publish low-priority tickets in the original `/to-tickets` format with `ready-for-agent` unchanged and add:

   ```markdown
   **Deferred:** yes — <UTC ISO-8601 timestamp to seconds>; excluded from the current `/spec-implement-loop` run
   ```

5. Show the complete P0/P1 batch and ask the user for approval. Execute only approved tickets. If approval is partial or absent, stop with a waiting-approval status.
6. Implement every approved P0/P1 ticket in the normal issue loop. Do not re-review a partial batch. Re-review only after the current batch is complete.

Count `review -> /to-spec -> /to-tickets -> fix -> commit -> repeat` rounds from 1. Allow at most three rounds. If round three still produces P0/P1 findings, create the final review spec, stop before another `/to-tickets` or fix pass, and report the current state for user approval.

Do not close or modify a parent issue inside `/to-tickets`; the outer loop updates root progress only after the approved work is verified.

## Completion and report

Report `complete` only when all of these hold:

- no uncompleted, non-deferred ticket remains;
- every completed ticket meets its acceptance criteria;
- the full test suite passes after the final implementation batch;
- final review is complete;
- every approved P0/P1 repair is complete;
- low-priority findings are recorded as deferred tickets;
- root and ticket statuses are synchronised;
- the root checkpoint is approved.

Otherwise report `waiting for approval`, `blocked`, or `failed`, with the exact condition.

The final report includes root and ticket states, test evidence, review-round count, deferred ticket identifiers, blockers or required approvals, and every commit in oldest-to-newest order. For each commit, use `/show-me` or `/archify` to explain its effect with the missing context restored. Use `/show-me` or `/archify` for the final summary, explaining the delivered result with the missing context restored.
