# `/parallel-code-review` acceptance scenario

Operator procedure only. Do not send this file to a review track because it
contains the expected findings.

## Inputs

Paths are relative to the skill package root.

- Patch: `references/acceptance-fixture.patch`
- Frozen tree: `references/acceptance-tree/`
- Requirements: `references/acceptance-requirements.md`
- Standards: `references/acceptance-standard.md`

Do not apply the patch to this repository. The tree is already the immutable
post-patch context.

## Procedure

1. Resolve the upstream `/code-review` and `/ponytail-review` skills through
   the host and SkillRoute. Run preflight with one `--upstream` per routed row
   and, for each remote URI, its exact-byte SHA-256 and exact byte size;
   normalized text SHA-256 is optional separate attestation. Confirm the
   routing-table order is `code-review`, then `ponytail-review`, and that both
   rows use contract version 1 with all six required manifest inputs. Capture
   the exact route-table, adapter, and upstream pins. The validator does not
   perform live SkillRoute resolution.
2. Freeze the explicit patch once with the supplied tree, requirements,
   standards, `--not-run repository tests=<reason>`, explicit
   `--contract-root`, and both resolved upstream pins. Write the bundle outside
   the reviewed repository. Confirm the manifest digest and patch attestation.
3. Record explicit invocation by calling `/parallel-code-review`, and record
   that the model-facing description also selects it for a parallel independent
   review request. Confirm a generic single-path review request does not select
   it.
4. Start the `/code-review` track and the `/ponytail-review` track in different
   independent sub-agents. Give both the same frozen bundle. The `/code-review`
   track keeps its internal Standards and Spec sub-agents and preserves both
   axes in original order. Do not simulate either reviewer.
5. Collect and validate both common envelopes with `validate-envelope`, passing
   the explicit contract root and both upstream pins. Confirm the envelopes
   have matching manifest digests, patch hashes and sizes, included paths, and
   checked source hashes. Confirm every finding has normalized severity,
   evidence rationale, exact citations, and native metadata.
6. Render the final report in routing-table order as separate track sections.
   Preserve each track's received finding order. Do not merge, remove, rerank,
   or choose a winner across tracks; duplicate or related findings stay in
   their owning track.
7. Confirm `/ponytail-review` keeps its narrative, Must fix, Should fix, and
   Nice to have grouping, verdict, Lean, and Not checked content in `native`.
   Do not turn that non-finding content into findings.
8. Snapshot the repository before and after the run. Confirm no repository writes,
   no applied patch, no branch or commit changes, and no task or pull request
   actions.

## Failure and partial-mode scenarios

Use the same frozen bundle and static envelopes to exercise coordinator
behavior only. These records do not demonstrate live model discovery,
independent execution, or recovery capability.

1. **Successful two-track review.** Record one completed attempt for each
   routed track with distinct invocation IDs, the identical frozen
   bundle/attestation, and a distinct request hash derived from each track
   identity. Record the `independence_capability` check. Run `validate-run`.
   Confirm overall `complete`, routing order, both original reports, and no
   merged or reranked findings. The per-track request hashes are expected to
   differ.
2. **Required-track launch failure.** Record the first track as completed,
   then record the second track's attempt as `launch_failure` with evidence and
   `launch_status: not_launched`. Run `validate-run`. Confirm overall `blocked`,
   the second track is missing, and the first completed report remains visible
   and attributable with its original findings.
   Repeat with the valid completed track accompanied by duplicate, unknown,
   non-object, missing-ID, and malformed-attempt entries, and separately with
   `checks: null`. Confirm each run is `blocked`, records the relevant run
   errors, and still returns the actual completed report rather than only an
   error-code envelope.
3. **One bounded recovery.** Fail one track with an evidenced
   `transient_transport` attempt using `source: host`, `phase: transport`, and
   a non-empty detail. Add exactly one recovery attempt with a new invocation
   ID, the same derived `request_sha256`, `analysis_reused: false`, and the
   `recovery_capability` check. Confirm the recovered run is `complete`.
   Repeat with a non-launched transient, permanent failure, arbitrary request
   hash, malformed evidence, reused invocation ID, or reused analysis and
   confirm each is rejected.
4. **Explicit partial approval.** Show and save the blocked launch-failure
   complete JSON result first. In a separate run record, reference that
   artifact by relative path and exact SHA-256, and record
   `approval.source: "user"` with evidence,
   `missing_track_ids: ["ponytail-review"]`, and the reduced independence.
   Confirm the result is `partial`, includes the missing track, derived
   coverage, artifact digest, and the untouched completed envelope, and never
   says it is a complete parallel review. Confirm a self-referenced same-pass
   record is rejected, as are a hard link to the current run, a minimal forged
   artifact, and an artifact with changed findings, rendered summary, or track
   summary under the same identities.
5. **Coverage is not launch failure.** Validate launched reports whose
   `coverage.status` is `partial` or `not_assessed`. Confirm the run reports
   that coverage separately and does not relabel it as a launch failure. Repeat
   with one completed report set to `coverage.status: blocked` and confirm the
   overall run is blocked with `coverage_blocked`, while the track remains
   completed and its full report remains visible.
6. **Unavailable host capability.** If live independent launches,
   independence evidence, or recovery capability cannot be demonstrated,
   record the exact `independence_capability` or `recovery_capability` check as
   `not_run` with a reason. Static records and subprocess contract tests are
   not live evidence.

## Expected findings

Routing order and normalized order are fixed for this synthetic bundle:

1. `code-review` findings: `STD-01`, then `SPEC-01`.
2. `ponytail-review` findings: `1`, `2`, then `3`.

Code review:

- `STD-01` at `src/discounts.py:9`, native Standards severity `high`, normalized
  `P1`: binary float conversion can make the monetary preview incorrect.
- `SPEC-01` at `src/discounts.py:6`, native Spec severity `medium`, normalized
  `P1`: the explicit requirement to reject an unknown coupon is not met.

Ponytail review:

- `1` at `src/discounts.py:9`, native group and severity `Must fix`, normalized
  `P1`: binary float conversion can make the monetary preview incorrect.
- `2` at `src/discounts.py:6`, native group and severity `Should fix`, normalized
  `P1`: unknown coupons return the amount unchanged instead of an explicit error.
- `3` at `src/discounts.py:3`, native group and severity `Should fix`, normalized
  `P2`: the risky money paths have no regression test.

The ponytail fixture has no Nice to have finding, so it emits no empty group.
Its synthetic `native` object includes `Lean: -0 lines possible` to verify that
Lean content is preserved when supplied. The repository-test check remains
`not_run` because the patch is review-only.

The automated test helper's static envelopes are only contract-shape test data.
They must not be reported as a live track result, a model-discovery pass, or
evidence that two independent reviewers ran.

## Unavailable host checks

If the host cannot demonstrate live model discovery, two independent sub-agent
launches, or GitHub behavior, record the affected check as `not run`. Static
package evidence does not turn those live checks into passes.
