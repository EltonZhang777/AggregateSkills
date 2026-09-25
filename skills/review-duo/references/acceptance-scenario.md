# Review Duo manual acceptance scenario

Operator instructions only. Do not send this file to reviewers because it contains expected findings.

## Fixed inputs

- Synthetic code: acceptance-fixture.patch
- Requirement source: acceptance-requirements.md
- Standard source: acceptance-standard.md
- Shared inventory: acceptance-manifest.json

The patch has two deliberate defects: it silently accepts an unknown coupon and uses binary floating point in an informational tax preview. Do not apply it to the repository.

## Procedure

1. Verify the resolved upstream code-review skill URI and normalized-text SHA-256, every other source SHA-256, and the code-scope patch SHA-256 and exact byte size. Normalize text sources by converting CRLF or CR line endings to LF and encoding as UTF-8. Hash and measure the frozen patch using its exact bytes. Compute the SHA-256 of the exact manifest file bytes once before dispatch.
2. Start one strict review with independent Standards and Spec agents. Give both the exact patch, requirements, standard, applicable repository sources, resolved skill URI and hash, manifest bytes, and manifest digest. The orchestrator verifies the pinned hashes before dispatch. Permit read-only verification tools; prohibit writes.
3. Collect both reports before comparing them. Confirm each echoes the manifest digest, patch SHA-256 and exact byte size, included paths, and its checked and unchecked sources and checks. Compare each report with the frozen manifest and the other report before marking the review current; a mismatch in the shared scope makes the overall status blocked. Confirm the expected findings below appear with their stated IDs and severities, and were not merged or reordered.
4. Confirm repository tests are shown as not run with a reason. Confirm the fixture patch was not applied and no review agent wrote files.
5. On a temporary copy only, change one byte of the patch after freezing the manifest. The report must be stale and must not be presented as current. Discard the temporary copy afterward.
6. In a separate run on a temporary copy only, make a declared source unavailable after freezing. The affected coverage must be partial and name the missing source. Discard the temporary copy afterward.
7. In a separate run on a disposable copy, exercise an input-sharing failure with two real agents. Start the first axis against the valid frozen patch and record its completed result. Then move only the disposable copy of the patch away from its declared path and start the second axis with the same manifest and digest. The second agent must stop before reviewing because it cannot verify the fixed scope. Mark the overall run blocked, preserve the completed first-axis result, and do not start a single-agent fallback without explicit approval. Verify the repository working tree is unchanged by this run, then restore or discard the disposable copy. Do not simulate a second reviewer in one context. If the host cannot launch the second agent with the pinned path unavailable, record this check as not run, not passed.

## Expected baseline findings

- Standards and Quality: STD-01 high for binary floating point in the monetary preview at `src/pricing.py:9`.
- Spec Conformance: SPEC-01 medium for accepting an unknown coupon at `src/pricing.py:6`; SPEC-02 medium for float arithmetic in the non-persisted preview at `src/pricing.py:9`.
- Both axes report checked and unchecked coverage. The repository test check remains not run because the patch is review-only.
- The operator confirms that review produced no writes.

Both reports must show the digest computed from the exact manifest bytes.
