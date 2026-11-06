---
name: spec-review
description: For an initial review, assess a staged specification against required business and technical evidence lenses; for a re-review after approved edits, reassess the edited specification against prior review coverage and observations.
---

# /spec-review

## Dependencies

When this skill's own workflow explicitly reaches a call to one of its directly declared Skill prerequisites, the call is explicit and may proceed even if that prerequisite disables implicit invocation. This waives only that invocation gate. It does not waive other prerequisite instructions or confirmation, authorization, security, or safety gates. It does not authorize transitive calls, create new call steps, or override an explicit prohibition on invoking another skill.

This workflow has no direct skill prerequisites. Its two isolated reviewer invocations are part of this skill's own workflow; do not route them through another skill or request cross-model opinions.

## Activation Criteria & Objective

Use `/spec-review` to review a named staged specification against business intent, engineering and test decisions, affected-codebase evidence, and independent challenge. Identify its target repository before inspecting code. Return candidate edits without changing the source draft; create a uniquely named candidate draft only after the user approves the exact batch and authorizes that destination. Review completion remains separate from final specification approval and publication.

## Review triggers

Choose exactly one trigger branch from the request:

- **Initial review:** use this branch when a staged specification is presented for its first review and there is no approved-edit re-review context. Establish the scope and run every required lens below.
- **Re-review after approved edits:** use this branch when approved edits have been made and the edited staged specification is presented with the prior review context. Focus the re-review on the approved edits and directly affected criteria; expand scope only when new evidence implicates another approved requirement. Recheck the edited content against the prior review observations and run every required lens again; do not assume that an earlier covered lens remains covered. Evidence that changes scope or crosses a seam remains separate and routes through the requirements workflow's seam-confirmation gate.

If the request does not identify an initial review or a re-review after approved edits, ask which branch applies before reporting a result. If the staged specification is not identified by a path or other stable name, ask which draft to review. A staged specification, target repository, or approved-edit context that cannot be read is incomplete review input.

## Freeze the round inputs

At round start, freeze draft bytes, the target-repository snapshot and its root `AGENTS.md`, scope/exclusions, requirements, applicable domain/decision docs, relevant implementation/tests/config, and checks before starting any reviewer invocation. The frozen input set is the review's source boundary for that round.

Treat each distinct frozen source as one record with a stable source identifier and a sorted set of roles. Use the canonical target-repository-relative POSIX path for repository sources and a normalized URI for external sources as `stable_source_id`. Each `stable_source_id` must appear exactly once in the `sources` array; when one source serves multiple roles, merge them into one record and list each role once in lexicographic order. For each source whose bytes are read, record the exact byte size and SHA-256 of those exact source bytes. Record an immutable repository or file revision identifier separately as source revision metadata without copying an entire repository snapshot; do not use a hash of the revision-ID string as a substitute for a source-content hash. If bytes are read for a revision-based source, record those exact bytes' size and SHA-256 as well. Include the staged draft, the target repository identity and snapshot revision or bytes, the target repository root `AGENTS.md`, the approved scope and explicit exclusions, every requirement source, applicable domain and decision documents, relevant implementation, tests, configuration, and each relevant check with its command and observed result or not-run reason. If a declared source is unavailable or changes after the freeze, mark the affected review stale or incomplete and do not silently substitute a reread or another source.

## Canonical manifest

Build one manifest from the frozen round input set. Serialize it as canonical UTF-8 JSON with recursively sorted object keys, `ensure_ascii: false`, compact separators `(',', ':')`, no insignificant whitespace, and no trailing newline. Include every frozen source in the `sources` array and order it lexicographically by its canonical path or normalized URI; because each `stable_source_id` is unique, this is a total order. Order every other repeated collection by its specified stable identifier.

Before serializing and hashing the manifest, decide the complete required assignment set for the round. It always contains one primary lens assignment and adversary-A; it also contains adversary-B when a high-risk trigger is met or cannot be ruled out. The single primary assignment's lens set must contain every triggered non-adversarial lens; do not create one primary assignment or invocation per lens. Reserve one unique initial invocation ID for every required assignment before hashing or freezing the manifest. The manifest must explicitly contain the frozen draft hash, repository snapshot identity, `source_hashes`, `checks`, a `high_risk_decision` record, and a `required_assignments` array whose entries contain the exact lens set or adversarial slot and its reserved `initial_invocation_id`. The `high_risk_decision` record must list every trigger considered, the evidence and status (`met`, `absent`, or `uncertain`) for each trigger, and the resulting required adversarial slots. Validate that `required_assignments` exactly matches that recorded decision before launching any invocation. Order `required_assignments` by canonical assignment key and include no unplanned assignment.

Hash the exact manifest bytes with SHA-256 after serialization and keep the resulting manifest hash outside the manifest so it cannot hash itself. Give every required invocation identical byte-based frozen inputs or the same immutable revision identifiers, plus identical canonical manifest bytes and manifest SHA-256. Do not rebuild, reorder, or silently update the manifest during the round.

## Invocation envelope and host identity

For each required invocation, create a canonical UTF-8 JSON invocation envelope using the manifest's sorted-key, compact, no-trailing-newline serialization rules. It binds all of the following: the manifest SHA-256, the exact request identifier and request SHA-256, the cycle identifier, the round identifier, either the exact assigned lens set or one adversarial slot, the manifest's reserved initial invocation ID, the current active invocation ID, and a unique invocation ID. Use an assignment object with either `lenses` or `adversarial_slot`; sort the lens set by stable name before serialization, require the current invocation ID to equal the host's recorded active ID for that assignment, and do not let an invocation claim a broader lens set or a different slot than the manifest. Initially the active ID is the reserved `initial_invocation_id`. For an authorized retry of an assignment, register a unique active replacement ID for that assignment and mark the prior ID superseded without rewriting the frozen manifest; the replacement envelope binds the same manifest and assignment plus both the reserved initial ID and the active replacement ID. Hash the exact envelope bytes with SHA-256 and pass the envelope bytes and hash with the frozen inputs.

The host records the host-returned session ID immediately after launching an invocation and binds that session ID to the envelope's invocation ID and assignment. Accept only the matching host invocation and session binding; a self-reported invocation ID, assignment, or session ID from a reviewer does not establish identity. All required invocations receive identical frozen inputs and manifest, while their envelope assignment and unique invocation ID remain distinct.

## Lens selection and coverage

Every review, including a re-review, always covers business scope, engineering and test decisions, affected-codebase evidence, one fresh isolated primary invocation, and one independent adversary-A invocation.

### Required lenses

- **Business scope:** check the intended outcome, users or operators, in-scope and out-of-scope behavior, constraints, and acceptance conditions.
- **Engineering and test decisions:** check the proposed design, interfaces, failure handling, operational assumptions, and the test decisions that demonstrate the behavior.
- **Affected-codebase evidence:** inspect the relevant code, callers, interfaces, configuration, and tests; record the paths or symbols that support or contradict each material specification claim.

### Isolated reviewer invocations

Start exactly one fresh isolated **primary invocation** for the single primary assignment containing every triggered non-adversarial lens, with the staged specification, its target context, and the review instructions. Fresh means it has no reused conversation state or prior reviewer output. Do not start one primary invocation per lens. Start one separate independent **adversary-A invocation** with the same staged specification and target context; do not provide the primary invocation's analysis to adversary-A. Ask adversary-A to challenge missing scope, unsupported codebase claims, engineering assumptions, and test decisions. These are separate perspectives from the same available model/runtime; do not request cross-model opinions.

## Risk and adversarial slots

Launch adversary-A in every round, including a low-risk round. Classify the round as high risk when security/privacy, data loss/destructive behavior, financial/charged data, irreversible publication/ticket change, review/approval gate, or core acceptance path could be affected. If any high-risk trigger is met or cannot be ruled out, require adversary-B and record the trigger and its evidence before launching that slot. If no trigger is present, record the evidence for that decision and do not launch adversary-B.

Adversary-A and adversary-B are separate fresh isolated invocations. Neither adversary sees primary findings or the other adversary's findings; the host does not use one adversarial output to construct another adversarial prompt. Use the same available model/runtime when needed, but do not request cross-model opinions.

## Result attestation

The primary invocation returns one distinct result for each lens in its assigned lens set. All those per-lens results share that invocation's ID, envelope hash, and host session binding. Each adversarial invocation returns its own result for its assigned slot. Every result attests the exact request, cycle, round, result lens or adversarial slot, reserved initial invocation ID, active invocation ID, and unique invocation ID; the manifest, draft, and envelope SHA-256 values; every checked source's stable identifier and SHA-256; and every unchecked source's stable identifier with a reason. The checked and unchecked source lists must partition the manifest's frozen `sources`: each source ID appears exactly once, in one list only, with none omitted. The host attaches the host-returned session binding to each result and checks its attestation against the frozen source records and canonical invocation envelope before accepting it.

Reject a result with a missing or mismatched attestation as stale or incomplete. Reject a result whose host session, invocation ID, assignment, cycle, round, manifest hash, draft hash, envelope hash, or checked source ID/hash does not match the host binding or frozen inputs; whose unchecked source ID is absent from the frozen sources or lacks a non-empty reason; or whose checked/unchecked source lists omit, duplicate, or overlap a frozen source. Such a result cannot make a lens `covered` or make the review pass.

## Cross-result acceptance

Derive result slots from the manifest's `required_assignments`: expand the primary assignment into one result slot per assigned lens, and keep one result slot for each adversarial assignment. Key a result slot by its exact assignment and result lens or adversarial slot; never count one result for two slots. All per-lens results from the same primary invocation intentionally share one invocation ID, envelope hash, and host session binding. An invocation ID must remain unique to its manifest assignment. Initialize each assignment's active invocation ID to its reserved initial ID. For an authorized retry, register one unique active replacement ID for that assignment, mark the prior ID superseded, supersede all of that invocation's lens results, and never rewrite the frozen manifest. Accept only the recorded active ID and accept a result only when its result slot, assignment, active invocation ID, reserved initial ID, envelope hash, manifest hash, host session binding, and attested source hashes match the manifest and active host record.

Reject duplicate result slots, swapped lenses or assignments, assignments or result slots absent from the manifest, extra results, and results from superseded invocation IDs as stale or incomplete. Repeated invocation IDs are valid only across distinct per-lens results from the same primary assignment; reject reuse across assignments. A late result from a superseded invocation ID is rejected or excluded from the active result set and cannot satisfy coverage, even when its other hashes are valid. Retaining that rejected result with superseded status in history does not invalidate a later complete active result set. A duplicate active result slot or a superseded result presented or used as active leaves coverage incomplete. Coverage passes only when every derived result slot has exactly one active, host-matched result and every required primary and adversarial invocation completed without an unavailable, partial, or abstaining result. This acceptance rule does not define retry counts, retry limits, or review-cycle policy.

## Finding and scope gates

Treat a finding as an evidence-based failure, not a preference. Every finding must name the affected draft section, cite supporting evidence at at least one frozen source path and line or exact symbol, state the practical impact, and propose the smallest exact change that would resolve that failure. Generic evidence without a source location is insufficient. A preference without a concrete failure, evidence, and impact is not a finding. Preserve the finding's severity and rationale; map another severity scale explicitly before applying these gates.

Use the repository's P0/P1/P2-or-lower definitions and preserve each reported severity and rationale; map another scale explicitly before applying these gates. A P0/P1 finding blocks early exit, pass, and publication only when it cites an approved acceptance clause and shows a reproducible failure. If either condition is missing, retain the original rating and rationale as an unverified observation, state that it is not an established blocker, and do not downgrade it solely to satisfy the exit gate; an unverified observation does not block those gates. Lack of safety proof alone does not establish a blocker. A P2-or-lower finding must be fixed or explicitly declined, deferred, or otherwise resolved by the user with a recorded reason before early exit or a pass. Merge duplicate findings that describe the same failure. Reopen a resolved or rejected finding only when new evidence or a changed approved requirement justifies reopening it; do not reopen it for preference alone.

Keep findings within the approved scope and acceptance criteria. When evidence changes the requested scope or crosses a seam, do not silently expand this review: report the evidence separately and route it back to the requirements workflow's seam-confirmation gate. Such evidence is not an approved finding change until that workflow confirms the scope or seam.

## Execution validity and retries

The preceding manifest, envelope, source, and result rules define admissible evidence; this section adds bounded recovery without changing those rules. Treat source, hash, manifest, file-access, and host-attribution failures as invalid executions, not product findings. A truncated invocation is also an invalid execution, never a valid partial review or abstention, and its retry counts against the same-round attempt limit. An invalid execution does not satisfy its assignment and leaves the affected coverage incomplete until a valid replacement result is accepted.

Retry a failed or invalid assignment in the same round with a fresh invocation and a new invocation ID. For a primary assignment, retry the complete assigned lens set as one assignment; apply the existing active-ID replacement and superseded-ID rules to all of its per-lens results. Count the initial invocation and each retry as attempts for that assignment, and allow at most three attempts per assignment per round. Before retrying an unresolved timeout, reconcile or cancel it; if its status remains unresolved, do not launch a replacement and leave the assignment and review coverage incomplete. After three failed or invalid attempts, stop automatic retries and ask the user what to do next. Do not turn an invalid execution into a product finding or silently advance the cycle.

## Named cycles and resumable state

A named review cycle has at most three numbered rounds, including the initial round. Use the existing freeze, manifest, envelope, and result rules for each round. End a cycle early only when no established P0/P1 blocker remains, every P2-or-lower finding is fixed or explicitly disposed of by the user with a reason, all required coverage is complete, and no decision or execution reconciliation is pending. An established P0/P1 blocker, an undisposed lower-severity finding, a pending user decision, an unresolved timeout, or incomplete coverage blocks early exit, pass, and publication.

Starting another named cycle requires the user's explicit authorization and a fresh three-round budget. Do not infer that authorization from the current cycle reaching its limit, and do not reset a round or attempt counter when resuming.

A valid partial review or abstention consumes its numbered round and is not an invalid-execution retry. Supplying missing evidence does not reopen that round. If the named cycle has a round remaining, incorporate the evidence into a new frozen manifest and start the next numbered round on the unchanged draft with a fresh primary and every required adversarial invocation. If no round remains, use the cycle-limit handoff.

When the three-round limit is reached and the review has not passed, present the current frozen draft and every unresolved finding, incomplete lens or slot, pending user decision, and unresolved execution reconciliation. State that the review has not passed, and ask whether the user authorizes another named cycle or wants another action. This cycle-limit handoff is not final approval or publication.

A new named cycle preserves prior reports and findings as history while receiving its fresh three-round budget. Append the new cycle to the resumable record; do not reset or mutate prior cycle history.

Preserve a resumable cycle record in the task progress summary: the named cycle and current round, round/attempt counts including per-assignment attempt counts, active and superseded invocation and host IDs, frozen draft and manifest hashes, user decisions, finding dispositions, candidate-write operation records and statuses, and prior cycle reports and findings. On resume, reconcile that record with authoritative host or invocation evidence before continuing; keep prior IDs and dispositions, and never reuse an invocation ID. Missing or conflicting state leaves the review `incomplete` or `needs-reconcile` and blocks pass. Do not create a separate local authoritative database.

## Candidate batch and approval

After reporting findings, return proposed edits as one exact candidate batch. Assign the batch a stable identifier. Group the proposed edit hunks for each named source into one complete candidate draft. For every candidate, show the exact source path and frozen SHA-256, an unambiguous source span or insertion anchor, the exact replacement or insertion text, the affected draft section, and a unique proposed destination path that does not reuse the source or another candidate destination. Preserve all source text outside the proposed edit hunks, and never write to or replace the source path. Treat multiple candidate destinations as one resulting draft input set for the next review round. Keep scope- or seam-changing proposals out of the approvable batch and report them separately under the requirements-workflow seam-confirmation gate.

Keep the workflow read-only until the user approves the exact candidate batch and separately authorizes creation at its exact destination. Bind both decisions to the batch identifier, every exact edit, each source path and frozen SHA-256, and each unique destination, and preserve those decisions in the task progress summary. If any edit text, source version, destination, or batch membership changes, present the changed batch and obtain approval and write authorization for the new exact tuple. A finding's disposition or review pass does not itself authorize a candidate write.

Before applying an approved batch, verify that the named cycle has a review round remaining for the resulting draft. If none remains, apply nothing, record `not_applied`, present the cycle-limit handoff, and ask whether the user explicitly authorizes a new named cycle or wants another action. After explicit new-cycle authorization, apply only if the prior exact batch approval and destination authorization still match, the source version is unchanged, and the destination remains unused; otherwise return for fresh approval and authorization. Review a candidate applied under the new cycle as round 1, and preserve the previous cycle history.

## Candidate creation and reconciliation

Use the named source's frozen bytes as an immutable byte snapshot; if those bytes are not retained, read the source once into the snapshot and verify its SHA-256 matches the candidate's frozen hash before deriving any output. Derive candidate bytes only from that snapshot plus the approved edits, preserve untouched bytes, and compute the expected SHA-256 from the exact resulting bytes. If the edits cannot be applied unambiguously to those bytes, stop before writing and report the candidate as not applied.

For each candidate destination, before its creation persist in the task progress summary one unique candidate-write operation ID, the batch and destination identity, source path and frozen hash, exact expected candidate bytes, expected SHA-256, and `prepared` status. Serialize candidate-write operations for the same source path; use a stable source-scoped lock where supported and hold it through final source checks and destination creation. Do not run overlapping writes for a source when a lock is unavailable.

Immediately before exclusive destination creation, hash the current source path and require the frozen hash. If it differs, mark the operation `stale`, preserve the source, and stop before creation and review. Create the destination with create-new semantics only; never overwrite. For a fresh operation, an existing destination or failed create-new means `not_applied`; do not silently choose another path because authorization names the exact destination. Immediately after successful creation, hash the source path again. If it changed, mark the operation `stale`, preserve both source and destination, and stop before review.

After creation, reread the destination and verify byte-for-byte equality with the expected candidate snapshot and equality of its SHA-256 with the expected hash before marking the operation `applied`. A mismatch or failed verification is `needs-reconcile`: preserve both files and stop before review. If a batch has multiple candidate writes, the batch remains incomplete and no post-edit review starts until every approved destination is verified; preserve any destination already created if a later write fails.

On resume, treat an existing destination as `applied` only when the resumable record has the matching operation ID and the destination bytes and hash exactly match the persisted expected candidate. Otherwise mark `needs-reconcile`; never overwrite or infer success from path existence alone. Reconcile a `prepared` operation before continuing and do not create a second operation for the same authorized candidate.

## Post-edit review and completion

After every approved candidate destination is verified, freeze all verified resulting bytes and hashes together as the next round's draft input set. Start the next numbered round in the same named cycle, with a fresh primary invocation for all triggered non-adversarial lenses and fresh invocations for every required adversarial slot. Count that review against the cycle's existing three-round budget. A stale, `not_applied`, or `needs-reconcile` candidate does not start the post-edit review.

For a candidate that changes scope or seams, report the proposed change separately and return it to requirements-workflow seam confirmation. Seam confirmation alone grants no write permission. After confirmation, show the exact revised draft text and a unique proposed temporary path, then obtain explicit approval of that text and authorization for that path. Recheck the named-cycle round budget before writing; if no round remains, apply nothing and use the cycle-limit handoff. Apply the same candidate creation safeguards, freeze and review the revised draft, and keep the existing round budget unless the user explicitly authorizes a new named cycle.

Completing a review loop or verifying a candidate write does not constitute final specification approval or publication. Keep those decisions separate and do not publish an Issue in this workflow.

## Technical-stack checklist triggers

Use affected-codebase evidence to identify every affected technical stack. Check the target repository's root instructions, domain documents, and stack-specific checklist sources. For every affected technical stack, determine and record whether its domain checklist triggers, naming the checklist considered and the evidence for the decision.

If no domain checklist triggers for a stack, record `not applicable` and why. If a checklist trigger is ambiguous, record the decision as `incomplete` rather than guessing. If a triggered checklist cannot be covered, record that required coverage is `incomplete`; do not silently omit the checklist.

## Developer-experience condition

Run developer-experience review only when a CLI/API/config/comparable developer-facing interface changes. When that condition is absent, record developer-experience review as `not applicable` and explain why. When the condition is present, developer-experience review is required coverage and must be `covered` before the review can pass.

## Coverage states and decision

Record one of these states for every required or conditional lens:

- `covered`: the required evidence or invocation was completed and its result is valid, complete, and recorded.
- `not applicable`: a conditional lens does not trigger, with the reason recorded. Use this state for a non-triggered domain checklist or the developer-experience condition only.
- `incomplete`: required evidence is missing, a trigger is ambiguous, an invocation or result is unavailable, partial, or abstains, host identity or isolation cannot be verified, or a triggered checklist could not be covered.

Missing required coverage must never count as passed. Report the review as passed only when all mandatory lenses are `covered`, every affected stack has a recorded checklist decision, each conditional lens is either `covered` or explicitly `not applicable`, every derived per-lens and adversarial result slot has exactly one active, host-matched result, and all required invocations completed without a partial or abstaining result.

## Report

Return a report that identifies the selected trigger branch, the reviewed specification scope, affected stacks and checklist decisions, every lens with its coverage state and evidence, each primary per-lens result, all required adversary-slot results, and the final coverage decision. For a re-review, also identify which prior review observations the approved edits address and which still need attention. Present proposed edits as one exact candidate batch with the required source, change, section, and destination details. Keep the report evidence-based and do not claim a pass when any required coverage is incomplete.
