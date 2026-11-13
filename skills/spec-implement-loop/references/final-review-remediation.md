# Final-review remediation

For each review round:

Immediately before `/to-spec` or `/to-tickets` drafts each remediation Issue title or body, invoke `/conventional-git-messages` with the review reports, supplied facts, and the target repository's root `AGENTS.md` language rule, and use its draft. Apply its general Issue-title and concise, factual prose guidance where compatible with the required formats. Preserve `/to-spec`'s required body headings and order and `/to-tickets`' required body structure and short, descriptive titles; use Conventional syntax or prefixes for `/to-tickets` titles only when compatible with that constraint. Keep each skill's existing confirmation and Issue-write approval gates.

Treat the complete track reports from `/parallel-code-review` as immutable review input. Preserve each report's track identity, route order, complete native content, finding order, and each finding's P0/P1/P2 severity and rationale exactly as received. Do not merge, remove, rerank, reclassify, or assign severity.

Handoff does not decide the final-review gate. Preserve any blocked or incomplete state and missing-track evidence with the reports; an incomplete round remains incomplete and cannot become a normal pass through remediation. If every current complete report is clean, skip empty remediation. After remediation changes code, refresh the requirement materialization and documented standards source paths, re-freeze the checks and exclusions, and rerun every routed track; do not reuse prior reports. Handoff is evidence only; it does not make the final review pass.

1. Read and follow the original `SKILL.md` for `/to-spec` using all complete track reports unchanged as input. Preserve its seam-confirmation gate before publication.
2. Read and follow the original `SKILL.md` for `/to-tickets`. Preserve its granularity, blocking-edge, and publication approval gates.
3. Consume each finding's P0/P1/P2 value from its originating track report; never reclassify it or assign a new severity. Use those reported severities for the existing approval, remediation, and deferral gates.
4. Publish P2 findings as low-priority tickets in the original `/to-tickets` format with `ready-for-agent` unchanged and add:

   ```markdown
   **Deferred:** yes — <UTC ISO-8601 timestamp to seconds>; excluded from the current `/spec-implement-loop` run
   ```

5. Show the complete P0/P1 batch, if any, and ask the user for approval. Execute only approved tickets. If approval is partial or absent for a non-empty batch, stop with a waiting-approval status.
6. Implement every approved P0/P1 ticket in the normal issue loop. Do not re-review a partial batch. Re-review only after the current batch is complete.

When the current complete review has no unhandled P0/P1 findings after P2 tickets are recorded as deferred, mark it passed and proceed to root status synchronization; the separate root completion checkpoint still applies. A blocked or incomplete review cannot proceed to normal root completion through remediation.

Each review round resolves both endpoints to full commit object IDs, requires `git merge-base <starting-oid> <final-oid>` to equal `<starting-oid>`, verifies `manifest.scope.base` and `manifest.scope.merge_base` equal `<starting-oid>` and `manifest.scope.head` equals `<final-oid>`, invokes `/parallel-code-review` once with `--range <starting-oid>...<final-oid>`, re-freezes the requirement, standards, checks, and exclusions inputs, and must pass the current-and-complete gate. Do not reuse a prior round's reports.

Count `review -> /to-spec -> /to-tickets -> fix -> commit -> repeat` rounds from 1. Allow at most three rounds. If round three still produces P0/P1 findings, create the final review spec, stop before another `/to-tickets` or fix pass, and report the current state for user approval.

Do not close or modify a parent issue inside `/to-tickets`; the outer loop updates root progress only after the approved work is verified.
