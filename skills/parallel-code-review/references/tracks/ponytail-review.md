<!-- parallel-code-review-track-metadata -->

```json
{
  "contract_version": 1,
  "upstream": {
    "name": "/ponytail-review",
    "source": "https://github.com/DietrichGebert/ponytail"
  },
  "required_inputs": [
    "patch",
    "tree",
    "requirements",
    "standards",
    "checks",
    "exclusions"
  ]
}
```

# `/ponytail-review` Track Adapter

This adapter is a thin integration boundary. It supplies no replacement review
criteria.

Before dispatch, read the original upstream `/ponytail-review` skill. Run its
review against the same frozen bundle supplied to every routed track. Replace
its moving patch or worktree target with the sealed patch and frozen tree; do
not read a live ref or live workspace file as review input.

Use the same frozen bundle without modifying it. Echo its manifest digest,
patch attestation, included paths, requirements, standards, checks, exclusions,
and checked source hashes in the common envelope. Do not freeze a second scope.

Return the upstream narrative, finding groups, grouping, verdict, Lean, and
Not checked content in `native`. Preserve the native Must fix, Should fix, and
Nice to have group names and order when the upstream supplies them. Do not
turn narrative, verdict, Lean, or Not checked content into findings.

Map each actual upstream finding to the common finding layout. Preserve its
native ID, group, severity, and original order. Assign an evidence-based
P0/P1/P2 severity and write one rationale sentence; use P2 when the evidence
does not establish P0 or P1 impact. Keep the native group and severity visible,
and cite the exact frozen source path, line, and quoted text.

Do not merge, remove, rerank, or reorder findings. Do not merge findings across
tracks or create a cross-track winner. The synthetic static acceptance envelope
is only coordinator contract test data; it is not evidence that the upstream
skill was resolved, that a model selected this track, or that an independent
sub-agent ran.
