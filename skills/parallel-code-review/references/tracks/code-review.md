<!-- parallel-code-review-track-metadata -->

```json
{
  "contract_version": 1,
  "upstream": {
    "name": "/code-review",
    "source": "https://github.com/mattpocock/skills"
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

# `/code-review` Track Adapter

This adapter is a thin integration boundary. It supplies no replacement review
criteria.

Before dispatch, read the original upstream `/code-review` skill. Run its
Standards and Spec review contract against the frozen bundle. Replace its
moving Git fixed point with the sealed patch and frozen tree; do not read a
live ref or live workspace file as review input. Keep `/code-review`'s internal
parallel sub-agents and aggregation.

When a standalone bundle records `requirements` as `not_assessed`, report that
limited coverage and do not invent requirements or claim requirement
compliance. A final-loop bundle never dispatches with missing requirements.

Return the Standards and Spec sections in their original order. Preserve every
finding's native axis, ID, severity, and order in the common report envelope.
Normalize each finding to P0/P1/P2 using the shared evidence rules without
changing its native meaning.

The static acceptance envelope is only a coordinator contract fixture. It does
not demonstrate that the upstream skill was resolved live, that model discovery
selected this track, or that an independent sub-agent ran.
