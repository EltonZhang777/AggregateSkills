---
name: spec-implement-loop
description: Run an explicitly approved root spec or ticket tree through implementation, verification, commit, push, status sync, and bounded review remediation.
disable-model-invocation: true
metadata:
  prerequisites: '{"skills":[["implement","mattpocock/skills"],["tdd","mattpocock/skills"],["code-review","mattpocock/skills"],["grill-with-docs","mattpocock/skills"],["grilling","mattpocock/skills"],["domain-modeling","mattpocock/skills"],["to-spec","mattpocock/skills"],["to-tickets","mattpocock/skills"],["setup-matt-pocock-skills","mattpocock/skills"],["ponytail-review","DietrichGebert/ponytail"],["caveman-commit","JuliusBrussee/caveman"]],"mcps":[],"tools":[]}'
---

# `/spec-implement-loop`

Run the user's root spec(s) to verified delivery in the current branch or worktree. Keep the scope to the supplied roots and stop at approval, ambiguity, security, permission, or external-state gates.

## Preflight

Complete every check before doing any work; report all failures together and stop on any failure.

Required skills:

- `mattpocock/skills`: `/implement`, `/tdd`, `/code-review`, `/grill-with-docs`, `/grilling`, `/domain-modeling`, `/to-spec`, `/to-tickets`, `/setup-matt-pocock-skills`
- `DietrichGebert/ponytail`: `/ponytail-review`
- `JuliusBrussee/caveman`: `/caveman-commit`

`/wait-what` is optional and is not an automatic step. `/skill-creator`, `/writing-for-agents`, and `/grill-me` are authoring-time skills, not runtime dependencies.

For every required skill, verify that the current skill catalog exposes it, its original `SKILL.md` is readable, and its invocation metadata is compatible. Load the original file when its step is reached. Never edit, copy, or paraphrase a dependency skill as a substitute. User-only dependencies retain their own user-confirmation gates.

If a dependency is missing, show the relevant installation hint and stop:

```text
npx skills@latest add mattpocock/skills --skill=<skill-name>
npx skills@latest add DietrichGebert/ponytail --skill=ponytail-review
npx skills@latest add JuliusBrussee/caveman --skill=caveman-commit
```

Read the original `SKILL.md` for `/setup-matt-pocock-skills`, then verify the configured issue-tracker files and vocabulary it requires. Do not run setup automatically. If setup or tracker configuration is missing or invalid, stop.

Also require:

- a clean worktree;
- a non-detached current branch;
- one resolvable upstream remote for that branch.

Record the starting `HEAD` for review and commit accounting. Do not re-check dependency origins over the network during normal execution.

## Intake and frontier

Accept one or more inline specs, local spec/ticket paths, or GitHub issue URLs/identifiers. Preserve each root's source and keep multiple roots as independent queues unless an explicit dependency joins them.

Discover descendants only from explicit parent/child links, checklists, issue links, or blocking/dependency edges. Do not infer tickets from titles or invent relationships.

- Treat a root itself as an implementation item when it has clear acceptance criteria and is a manageable size.
- If a root is clearly too large for one implementation round, pause and ask for approval to load and run `/to-tickets`.
- If a root is only planning material and has no clear acceptance criteria, pause and report; do not create tickets automatically.

A ticket is ready when its blockers are complete, its acceptance criteria are clear, and required permissions and environment are available. Process one ready ticket at a time, preferring dependency order and then the root's order or issue number. Exclude tickets generated and marked `deferred` during the current run.

## Issue loop

For each ready ticket:

1. Read and follow the original `SKILL.md` for `/implement`; use its `/tdd` and `/code-review` discipline. Implement only the ticket's scope and use the ticket's agreed seams.
2. Run the smallest relevant tests and verification for the ticket. Do not call an issue complete until its acceptance criteria, tests, and issue-level review pass.
3. Read and follow the original `SKILL.md` for `/caveman-commit` to produce the commit message.
4. Create exactly one focused commit for the completed ticket. The outer loop owns this commit boundary; treat `/implement`'s commit instruction as satisfied by this commit and never create a duplicate commit.
5. Push the commit to the current branch. If push fails, choose a small, finite retry count based on the error and retry. After retries fail, stop and report the local commit and error; do not amend or rewrite history.
6. Update the completed ticket and root progress only after the push succeeds. Retry a failed tracker/status update a small, finite number of times; if it still fails, stop and report that code is pushed but status is unsynchronised. Do not roll back the code.

If a decision, user preference, permission, security concern, or scope boundary is unclear, stop and load the original `SKILL.md` for `/grill-with-docs`. A purely local, objective blocker may be recorded and skipped while independent ready tickets continue; do not bypass a user decision.

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

- no uncompleted, non-deferred ready ticket remains;
- every completed ticket meets its acceptance criteria;
- the full test suite passes after the final implementation batch;
- final review is complete;
- every approved P0/P1 repair is complete;
- low-priority findings are recorded as deferred tickets;
- root and ticket statuses are synchronised.

Otherwise report `waiting for approval`, `blocked`, or `failed`, with the exact condition.

The final report includes root and ticket states, test evidence, review-round count, deferred ticket identifiers, blockers or required approvals, and every commit in oldest-to-newest order. For each commit, state its summary and explain its effect in plain language with the missing context restored; do not auto-invoke `/wait-what`.
