---
name: spec-review
description: For an initial review, assess a staged specification against required business and technical evidence lenses; for a re-review after approved edits, reassess the edited specification against prior review coverage and observations.
---

# /spec-review

## Dependencies

When this skill's own workflow explicitly reaches a call to one of its directly declared Skill prerequisites, the call is explicit and may proceed even if that prerequisite disables implicit invocation. This waives only that invocation gate. It does not waive other prerequisite instructions or confirmation, authorization, security, or safety gates. It does not authorize transitive calls, create new call steps, or override an explicit prohibition on invoking another skill.

This workflow has no direct skill prerequisites. Its two isolated reviewer invocations are part of this skill's own workflow; do not route them through another skill or request cross-model opinions.

## Activation Criteria & Objective

Use `/spec-review` to review a named staged specification against business intent, engineering and test decisions, affected-codebase evidence, and independent challenge. Identify its target repository before inspecting code. The workflow is read-only: it returns a review report and does not edit or publish the specification.

## Review triggers

Choose exactly one trigger branch from the request:

- **Initial review:** use this branch when a staged specification is presented for its first review and there is no approved-edit re-review context. Establish the scope and run every required lens below.
- **Re-review after approved edits:** use this branch when approved edits have been made and the edited staged specification is presented with the prior review context. Recheck the edited content against the prior review observations and run every required lens again; do not assume that an earlier covered lens remains covered.

If the request does not identify an initial review or a re-review after approved edits, ask which branch applies before reporting a result. If the staged specification is not identified by a path or other stable name, ask which draft to review. A staged specification, target repository, or approved-edit context that cannot be read is incomplete review input.

## Lens selection and coverage

Every review, including a re-review, always covers business scope, engineering and test decisions, affected-codebase evidence, one fresh isolated primary invocation, and one independent adversary-A invocation.

### Required lenses

- **Business scope:** check the intended outcome, users or operators, in-scope and out-of-scope behavior, constraints, and acceptance conditions.
- **Engineering and test decisions:** check the proposed design, interfaces, failure handling, operational assumptions, and the test decisions that demonstrate the behavior.
- **Affected-codebase evidence:** inspect the relevant code, callers, interfaces, configuration, and tests; record the paths or symbols that support or contradict each material specification claim.

### Isolated reviewer invocations

Start one fresh isolated **primary invocation** with the staged specification, its target context, and the review instructions. Fresh means it has no reused conversation state or prior reviewer output. Start one separate independent **adversary-A invocation** with the same staged specification and target context; do not provide the primary invocation's analysis to adversary-A. Ask adversary-A to challenge missing scope, unsupported codebase claims, engineering assumptions, and test decisions. These are separate perspectives from the same available model/runtime; do not request cross-model opinions.

## Technical-stack checklist triggers

Use affected-codebase evidence to identify every affected technical stack. Check the target repository's root instructions, domain documents, and stack-specific checklist sources. For every affected technical stack, determine and record whether its domain checklist triggers, naming the checklist considered and the evidence for the decision.

If no domain checklist triggers for a stack, record `not applicable` and why. If a checklist trigger is ambiguous, record the decision as `incomplete` rather than guessing. If a triggered checklist cannot be covered, record that required coverage is `incomplete`; do not silently omit the checklist.

## Developer-experience condition

Run developer-experience review only when a CLI/API/config/comparable developer-facing interface changes. When that condition is absent, record developer-experience review as `not applicable` and explain why. When the condition is present, developer-experience review is required coverage and must be `covered` before the review can pass.

## Coverage states and decision

Record one of these states for every required or conditional lens:

- `covered`: the required evidence or invocation was completed and its result is recorded.
- `not applicable`: a conditional lens does not trigger, with the reason recorded. Use this state for a non-triggered domain checklist or the developer-experience condition only.
- `incomplete`: required evidence is missing, a trigger is ambiguous, an invocation did not complete, or a triggered checklist could not be covered.

Missing required coverage must never count as passed. Report the review as passed only when all mandatory lenses are `covered`, every affected stack has a recorded checklist decision, and each conditional lens is either `covered` or explicitly `not applicable`.

## Report

Return a report that identifies the selected trigger branch, the reviewed specification scope, affected stacks and checklist decisions, every lens with its coverage state and evidence, the primary and adversary-A results, and the final coverage decision. For a re-review, also identify which prior review observations the approved edits address and which still need attention. Keep the report evidence-based and do not claim a pass when any required coverage is incomplete.
