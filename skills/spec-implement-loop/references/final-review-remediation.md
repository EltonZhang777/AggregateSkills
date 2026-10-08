# Final-review remediation

For each review round:

Immediately before `/to-spec` or `/to-tickets` drafts each remediation Issue title or body, invoke `/conventional-git-messages` with the review reports, supplied facts, and the target repository's root `AGENTS.md` language rule, and use its draft. Apply its general Issue-title and concise, factual prose guidance where compatible with the required formats. Preserve `/to-spec`'s required body headings and order and `/to-tickets`' required body structure and short, descriptive titles; use Conventional syntax or prefixes for `/to-tickets` titles only when compatible with that constraint. Keep each skill's existing confirmation and Issue-write approval gates.

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
