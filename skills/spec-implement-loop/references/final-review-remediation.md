# Final-review remediation

Read this reference after each final `/parallel-code-review` round, before deciding handoff, remediation, or completion. This reference is the sole normative source for complete-report handoff, preservation of blocked and incomplete reviews, the distinction between a one-track partial result and a per-root exception, permanent append-only records, approval ordering, retry and reconciliation, and final-review completion gating. The main skill supplies only review invocation and freeze mechanics.

## Complete-report handoff

Treat the complete track reports from `/parallel-code-review` as immutable review input. Preserve each report's track identity, route order, complete native content, finding order, and each finding's P0/P1/P2 severity and rationale exactly as received. Do not merge, remove, rerank, reclassify, or assign severity.

Hand every current complete track report unchanged, in route order, with its findings, native metadata, severities, and rationales preserved. Handoff does not decide the final-review gate. Preserve any blocked or incomplete state and missing-track evidence with the reports; an incomplete round remains incomplete and cannot become a normal pass through remediation. If every current complete report is clean, skip empty remediation. Handoff is evidence only; it does not make the final review pass.

## Partial results and per-root exceptions

An explicitly approved one-track partial review remains an incomplete final review. A **one-track partial result** has one complete track report and at least one missing track. Its partial-mode approval is not a root exception and does not authorize issue comments, status synchronization, or completion.

After every remediation code change, refresh the requirement and standards inputs, re-freeze the scope, checks, and exclusions, and rerun every routed track; reports from before the change are historical only. Verify the refreshed `manifest.checks` and `manifest.exclusions` contain exactly the recorded entries before dispatch. A rerun that remains partial requires a new partial-mode approval bound to its latest blocked artifact. Show its new blocked result when requesting that approval; the prior partial-mode approval and artifact are historical only.

A **per-root exception** is a separate approval that lets a current one-track partial result proceed through root status synchronization after its complete current report has no unhandled P0/P1 findings and final verification passes. It requires the permanent append-only record, does not make the review complete or passing, and authorizes no other GitHub writes. Only after the latest review is current and final verification is complete may the loop ask for a separate per-root user exception.

## Permanent append-only records

Before showing that request, invoke `/conventional-git-messages` with the target root repository's root `AGENTS.md` and the exact facts. Draft the complete wrapper and the exact report content; split it if needed. Show the proposed exception and report content. The request and final record series must name:

- the frozen scope: starting OID, final OID, manifest digest, and scope digest;
- the latest partial-mode approval source and evidence plus the blocked result path and SHA-256;
- the root-exception approval source and evidence, added after that approval;
- the missing track and the resulting loss of independence;
- the residual risk, including the review perspective that was not executed;
- the permanent partial state and its effect on completion;
- one complete completed-track report exactly as received, including its normalized findings and native metadata, unchanged.

Obtain the separate per-root exception approval. Add only its exact source and evidence to the record metadata, freeze the final comment series, and show it. Then request separate issue-comment write approval for that exact series; do not infer approval from the partial-mode approval, silence, or the task-start grant. After both approvals, write the approved append-only series verbatim; do not edit, delete, or rewrite a comment. If any content or part count changes, stop and obtain renewed approvals.

If the record exceeds one comment, split it into an ordered `part N/M` series. Each part carries its part label and only its slice; the series contains exactly one complete report, with no duplication, truncation, change, or omission. The exception is effective only when every part is confirmed.

## Retry and reconciliation

A stale final-review bundle makes its reports historical only; re-freeze from the original standards paths and refreshed requirement inputs, then rerun every routed track. Do not reuse a prior round's reports.

Re-read the root issue after each record write. If a write is uncertain, reconcile the existing comments before retrying; append only missing parts. Retry only clearly transient failures up to three total attempts, and stop before root status synchronization while any part is unresolved.

## Remediation procedure

For each review round:

Immediately before `/to-spec` or `/to-tickets` drafts each remediation Issue title or body, invoke `/conventional-git-messages` with the review reports, supplied facts, and the target repository's root `AGENTS.md` language rule, and use its draft. Apply its general Issue-title and concise, factual prose guidance where compatible with the required formats. Preserve `/to-spec`'s required body headings and order and `/to-tickets`' required body structure and short, descriptive titles; use Conventional syntax or prefixes for `/to-tickets` titles only when compatible with that constraint. Keep each skill's existing confirmation and Issue-write approval gates.

1. Read and follow the original `SKILL.md` for `/to-spec` using all complete track reports unchanged as input. Preserve its seam-confirmation gate before publication.
2. Read and follow the original `SKILL.md` for `/to-tickets`. Preserve its granularity, blocking-edge, and publication approval gates.
3. Consume each finding's P0/P1/P2 value from its originating track report; never reclassify it or assign a new severity. Use those reported severities for the existing approval, remediation, and deferral gates.
4. Publish P2 findings as low-priority tickets in the original `/to-tickets` format with `ready-for-agent` unchanged and add:

   ```markdown
   **Deferred:** yes — <UTC ISO-8601 timestamp to seconds>; excluded from the current `/spec-implement-loop` run
   ```

5. Show the complete P0/P1 batch, if any, and ask the user for approval. Execute only approved tickets. If approval is partial or absent for a non-empty batch, stop with a waiting-approval status.
6. Implement every approved P0/P1 ticket in the normal issue loop. Do not re-review a partial batch. Re-review only after the current batch is complete.

Count `review -> /to-spec -> /to-tickets -> fix -> commit -> repeat` rounds from 1. Allow at most three rounds. If round three still produces P0/P1 findings, create the final review spec, stop before another `/to-tickets` or fix pass, and report the current state for user approval.

Do not close or modify a parent issue inside `/to-tickets`; the outer loop updates root progress only after the approved work is verified.

## Completion gate

The final-review gate passes only when the frozen bundle is current and every routed track report is complete. A current review whose pinned requirements are missing, empty, whitespace-only, or `not_assessed` cannot pass the final-review gate, partial mode, or the per-root exception. A failed, stale, or incomplete parallel review cannot pass the final-review gate or normal root completion. The preservation rule in [Complete-report handoff](#complete-report-handoff) applies.

When the current complete review has no unhandled P0/P1 findings after P2 tickets are recorded as deferred and final verification passes, mark it passed and proceed to root status synchronization under the task-start grant without a separate approval pause, using the same retry and reconciliation rules as ticket status sync; the separate root completion checkpoint still applies. A complete review skips the per-root exception.

A per-root exception path remains incomplete until the separate per-root exception is approved and the complete append-only record is confirmed. Every record part must be confirmed before root status synchronization under the task-start grant without a separate approval pause, using the same retry and reconciliation rules as ticket status sync. After synchronization, the root completion checkpoint remains mandatory, and status synchronization never counts as approval to declare the root complete. At `root_checkpoint`, present the final evidence and pause for explicit approval. If the synced root status is already complete while approval is pending, leave it in place; if work resumes, reopen the root during the next status sync. Declining the exception or leaving its record incomplete keeps the root in `root_exception`; do not sync completed status.
