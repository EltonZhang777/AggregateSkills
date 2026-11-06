# `/spec-review` manual scenario

Run these through the user-visible skill invocation in a disposable repository with named staged drafts and a documented technical stack. Do not use production specifications or publish an Issue.

## Initial review and approved-edit re-review

Stage a named specification in a repository with a documented API surface and an applicable stack-specific checklist. Request its initial review. Confirm `/spec-review` selects the initial-review branch, identifies the target repository, and reports business scope, engineering and test decisions, affected-codebase evidence, the checklist decision, developer-experience coverage for the API change, one fresh isolated primary result, and one separate adversary-A result. Confirm every lens has a coverage state and a missing required result cannot produce a passed review.

Present an edited staged specification with prior review context and state that the edits were approved. Request a re-review. Confirm it selects the approved-edit re-review branch, starts fresh primary and adversary-A invocations, rechecks every required lens against the edited draft, and reports which prior observations are addressed or still need attention. Confirm the workflow reports findings and coverage without editing or publishing the draft.

## Domain checklist coverage states

Review a named draft affecting a stack for which no applicable checklist triggers. Confirm the report names the stack, records `not applicable`, and explains why no checklist triggers. In separate runs, make the trigger ambiguous or make an applicable checklist unavailable. Confirm the affected required coverage is `incomplete`, the review is not passed, and the workflow does not substitute cross-model opinions or omit the gap.
