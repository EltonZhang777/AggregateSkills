# /review-duo manual acceptance scenario

Operator instructions only. Do not send this file to reviewers because it contains expected findings.

## Fixed package inputs

Paths are relative to the directory containing `SKILL.md`.

- Synthetic code: `references/acceptance-fixture.patch`
- Requirement source: `references/acceptance-requirements.md`
- Standard source: `references/acceptance-standard.md`
- Package resource inventory: `references/acceptance-manifest.json`

The patch has two deliberate defects: it silently accepts an unknown coupon and uses binary floating point in an informational tax preview. Do not apply it to the repository.

## Runtime context

The coordinating agent reads applicable instructions, domain context, and decisions from the repository receiving the review. It supplies those documents separately from the fixed package inputs and pins their paths and hashes in the run-specific coverage manifest. Never substitute copies from the repository that contains this skill package.

## Procedure

1. Resolve package resources against the skill package root and verify their hashes. Resolve `/code-review` in the current runtime and record its URI and normalized-text SHA-256. Read applicable context from the target repository, then build and freeze one run-specific coverage manifest containing those runtime sources, the package inputs, and relevant checks. Compute the exact manifest digest once before dispatch.
2. Start one strict review with independent Standards and Spec agents. Give both the exact patch, requirements, standard, separately supplied target context, resolved skill URI and hash, and identical run-specific manifest bytes and digest. Do not send this operator procedure to either reviewer. Permit read-only verification tools; prohibit writes.
3. Collect both reports before comparing them. Confirm each echoes the manifest digest, patch SHA-256 and exact byte size, included paths, and its checked and unchecked sources and checks. Compare each report with the frozen manifest and the other report before marking the review current; a mismatch in the shared scope makes the overall status blocked. Confirm the expected findings below appear with their stated IDs and severities, and were not merged or reordered.
4. Confirm repository tests are shown as not run with a reason. Confirm the fixture patch was not applied and no review agent wrote files. The required read-only dry-run ends here: do not create a temporary repository or write files.

Steps 5–7 are separate robustness checks. They may use disposable patch copies, but must not create a temporary repository.

5. On a temporary copy only, change one byte of the patch after freezing the manifest. The report must be stale and must not be presented as current. Discard the temporary copy afterward.
6. In a separate run on a temporary copy only, make a declared source unavailable after freezing. The affected coverage must be partial and name the missing source. Discard the temporary copy afterward.
7. In a separate run on a disposable copy, exercise an input-sharing failure with two real agents. Start the first axis against the valid frozen patch and record its completed result. Then move only the disposable copy of the patch away from its declared path and start the second axis with the same manifest and digest. The second agent must stop before reviewing because it cannot verify the fixed scope. Mark the overall run blocked, preserve the completed first-axis result, and do not start a single-agent fallback without explicit approval. Verify the repository working tree is unchanged by this run, then restore or discard the disposable copy. Do not simulate a second reviewer in one context. If the host cannot launch the second agent with the pinned path unavailable, record this check as not run, not passed.

## Expected baseline findings

- Standards and Quality: STD-01 high for binary floating point in the monetary preview at `src/pricing.py:9`.
- Spec Conformance: SPEC-01 medium for accepting an unknown coupon at `src/pricing.py:6`; SPEC-02 medium for float arithmetic in the non-persisted preview at `src/pricing.py:9`.
- Both axes report checked and unchecked coverage. The repository test check remains not run because the patch is review-only.
- The operator confirms that review produced no writes.

Both reports must show the digest computed from the exact manifest bytes.
