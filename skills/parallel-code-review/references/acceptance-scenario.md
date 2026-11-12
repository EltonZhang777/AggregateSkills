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

1. Resolve the upstream `/code-review` skill through the host and SkillRoute.
   Run preflight with `--upstream /code-review=<resolved local file or URI>` and,
   for a remote URI, `--upstream-exact-sha /code-review=<exact digest>` plus
   `--upstream-size /code-review=<exact bytes>`; normalized text SHA-256 is
   optional separate attestation. Confirm the routing table resolves one
   `code-review` row, its exact contract version, upstream dependency, and all
   six required manifest inputs. Capture the exact route-table, adapter, and
   upstream pins. The validator does not perform live SkillRoute resolution.
2. Freeze the explicit patch with the supplied tree, requirements, standards,
   `--not-run repository tests=<reason>`, explicit `--contract-root`, and the
   same upstream pin. Write the bundle outside the reviewed repository. Confirm
   the manifest digest and patch attestation.
3. Record explicit invocation by calling `/parallel-code-review`, and record
   that the model-facing description also selects it for a parallel independent
   review request. Confirm a generic single-path review request does not select
   it.
4. Start the single `/code-review` track in its own independent sub-agent. Give
   it the identical frozen bundle and require its Standards and Spec sections
   in original order. Do not simulate the reviewer.
5. Collect the common envelope. Validate it with `validate-envelope`, passing
   the explicit contract root and upstream pin (including exact digest and size
   for a remote source). Confirm its contract version, track ID, manifest
   digest, patch size and hash, included paths, coverage, checked hashes,
   normalized presentation fields, exact citations, and received finding
   order.
6. Confirm the normalized result preserves the native axes and severities. The
   coordinator must not reclassify, reorder, merge, or choose a winner.
7. Snapshot the repository before and after the run. Confirm no repository writes,
   no applied patch, no branch or commit changes, and no task or pull request
   actions.

## Expected findings

- `STD-01` at `src/discounts.py:9`, native Standards severity `high`, normalized
  `P1`: binary float conversion can make the monetary preview incorrect.
- `SPEC-01` at `src/discounts.py:6`, native Spec severity `medium`, normalized
  `P1`: the explicit requirement to reject an unknown coupon is not met.

The repository-test check remains `not_run` because the patch is review-only.

The automated test helper's static envelope is only contract-shape test data.
It must not be reported as a live `/code-review` result, model-discovery pass,
or independent-reviewer pass.

## Unavailable host checks

If the host cannot demonstrate live model discovery, independent sub-agent
execution, or GitHub behavior, record the affected check as `not run`. Static
package evidence does not turn those live checks into passes.
