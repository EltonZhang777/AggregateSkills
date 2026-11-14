# Parallel Review Contract

## Version

The routing adapter metadata and the common report envelope use
`contract_version: 1`. The coordinator supports exactly that integer version.
Unknown fields, unknown required-input categories, invalid field types, and
any other version fail preflight.

Adding a field or required-input category increments the version. Adding a
track that reuses the existing schema does not.

## Routing authority

[`routing-table.md`](routing-table.md) is the only activation registry. Each
row has a stable track ID and one adapter document under
`references/tracks/`. Row order is execution and aggregation order.

Every adapter starts with exactly one fixed-marker metadata object:

````markdown
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
````

Track ID, adapter path, and order come only from the routing table. Adapter
metadata does not contain a track count, native sections, review criteria, or
an optional-track flag.

## Upstream resolution

The coordinator resolves every declared upstream through the host and
SkillRoute. The validator does not perform network resolution. Preflight and
freeze require a resolved local skill file/directory, or a resolved URI plus
the host-supplied exact-byte SHA-256 and exact byte size. Verify and envelope
validation require that same resolution explicitly; the manifest alone is not
an upstream fallback.

The pinned upstream record contains the exact dependency name, resolved URI,
exact-byte SHA-256, exact byte size, and, when available, a normalized-text
SHA-256. A local file is read by the validator, which computes and
cross-checks all three values. A remote URI is accepted only with the host's
exact digest and size. Its normalized digest is optional normalized attestation
and cannot substitute for exact-byte identity. Missing, duplicate, unreadable,
empty, malformed, size-mismatched, or hash-mismatched resolutions fail before
dispatch.

Pin objects use `sha256` for the exact-byte digest, `size_bytes` for the exact
byte count, and optional `normalized_sha256` for normalized text attestation.
An upstream pin also records `name`, the declared `source`, `kind`
(`local_file`, `local_directory`, or `remote_uri`), and its resolved
`uri`/path.

An upstream's full identity is `(name, source)`. Multiple adapters may share
the same full identity and therefore one resolution and one pin. A declared
`name` must be unique across routed upstreams: if two adapters use the same
name with different sources, preflight fails with
`upstream_identity_conflict` before resolution or dispatch. This invariant
keeps the name-keyed resolution arguments unambiguous while pin validation and
storage use the full `(name, source)` identity.

## Required input registry

The fixed input categories are:

| Input | Required content |
| --- | --- |
| `patch` | Exact frozen patch bytes and SHA-256. |
| `tree` | Frozen code tree snapshot at the reviewed revision. |
| `requirements` | Pinned issue/spec/acceptance sources. |
| `standards` | Pinned repository rules and applicable decisions. |
| `checks` | Observed check results, or `not_run` with a reason. |
| `exclusions` | Every excluded path with a reason. |

An adapter may require a subset of this registry. A new category needs an
explicit contract change and version increment.

When `checks` is required, at least one check or `not_run` record is required.
Observed results are `passed`, `failed`, or `not_assessed`. A `not_run` record
must carry a non-empty reason and is supplied as `--not-run NAME=REASON`; the
`--check` form does not accept `not_run`.

## Frozen bundle

`scripts/review_contract.py freeze` creates:

```text
<bundle>/
  manifest.json
  attestation.json
  scope/patch.diff
  tree/<included source paths>
  inputs/<role>/<pinned input snapshots>
```

The manifest is canonical UTF-8 JSON with sorted keys and is itself outside
the digest it describes. The separate attestation records the exact manifest
SHA-256, patch SHA-256 and byte size, and included paths.

The manifest records:

- `contract_version`;
- the scope kind and resolved Git identities;
- the patch identity;
- included source paths and tree-source hashes;
- `input_status`, which resolves every registry category as `included`,
  `recorded`, or `not_assessed`;
- pinned requirements and standards;
- checks and `not_run` reasons;
- exclusions and reasons;
- routing-table, adapter, and resolved-upstream pins.

Any byte change to the patch, tree source, pinned input, manifest, routing
table, adapter, or resolved upstream makes the bundle stale. Routing-table,
adapter, resolved-upstream, and pinned-input records contain both the exact-byte
SHA-256 and exact byte size; the exact values are authoritative for staleness.
Text records may also carry `normalized_sha256` for normalized attestation, but
it never replaces the exact comparison. A line-ending-only byte change is
stale. The patch remains exact-byte hashed. Verify requires the contract root
and upstream resolution explicitly.

`input_status` is derived from the frozen manifest, not accepted as an
independent claim:

- `patch` is `included` because the validated scope always contains the frozen
  patch.
- `tree` is `included` only when frozen tree sources exist; otherwise it is
  `not_assessed`.
- `requirements` and `standards` are `included` only when matching input
  snapshots exist; otherwise they are `not_assessed`.
- `checks` is `recorded` only when at least one check or `not_run` record
  exists; otherwise it is `not_assessed`.
- `exclusions` is always `recorded`, including an explicit empty exclusion
  list.

Every routed adapter's `required_inputs` must resolve consistently with this
mapping. An included category must have its frozen input, a tracked adapter
cannot require `not_assessed` content, and a required `checks` category needs
at least one record. Any mismatch makes the bundle invalid.

An explicit patch also requires a separately supplied frozen tree. Every
non-deleted changed path must exist in that tree, and the tree must match the
patch's exact post-image, or freeze fails. The coordinator validates
applicability against a temporary copy and never applies the patch to create
live review context.

Excluded paths are omitted from the frozen tree and recorded with their
reasons. A patch that changes an excluded path fails the freeze instead of
claiming the path was both reviewed and excluded.

## Common report envelope

Each track returns one JSON object with exactly these top-level fields:

```json
{
  "contract_version": 1,
  "track_id": "code-review",
  "invocation_id": "track invocation identifier",
  "launch_status": "launched",
  "attestation": {
    "manifest_sha256": "...",
    "patch_sha256": "...",
    "patch_size_bytes": 0,
    "included_paths": []
  },
  "coverage": {
    "status": "complete",
    "checked": [{"path": "...", "sha256": "..."}],
    "unchecked": [{"path": "...", "reason": "..."}],
    "checks": [{"name": "...", "result": "not_run", "reason": "..."}]
  },
  "native": {},
  "findings": []
}
```

`native` is opaque track-specific content. The coordinator may render it but
must not reinterpret or change it. `coverage.status` is separate from launch
status and from whether findings exist.

`coverage.status: complete` requires at least one checked source. Each checked
hash must match the frozen tree. Finding locations must resolve to a valid line
in the frozen tree, and each citation must match a frozen tree or pinned input
path, line, and exact quoted text. Repository-relative citation paths resolve
against the frozen bundle; callers do not need absolute host paths. A check
whose result is `not_run` must carry a non-empty reason.

Each finding has:

| Field | Requirement |
| --- | --- |
| `severity` | Exactly `P0`, `P1`, or `P2`. |
| `severity_rationale` | One evidence-based sentence. |
| `title` | Short finding title. |
| `location` | Object with `path` and positive `line`. |
| `what_this_is` | Upstream meaning without invented impact. |
| `problem` | Evidence-based problem statement. |
| `fix` | Source-based recommendation. |
| `if_we_skip_it` | Source-based impact. |
| `citations` | Non-empty exact source citations with `path`, `line`, and `quote`. |

Optional native fields are `native_axis`, `native_id`, `native_severity`, and
`native_group`. They remain visible beside the normalized severity. The
coordinator validates and presents findings in their received order; it does
not reclassify, merge, remove, or rerank them.

Native semantic ordering belongs to the upstream track and remains opaque to
the coordinator. A schema-valid synthetic envelope is contract-test data, not
evidence of live model discovery or independent execution.

## Coordinator run result

One review run record aggregates every required routed track without changing
the track envelope. The run record has exactly these fields:

```json
{
  "contract_version": 1,
  "tracks": [
    {
      "track_id": "code-review",
      "attempts": [
        {
          "invocation_id": "code-review-001",
          "status": "completed",
          "launch_status": "launched",
          "request_sha256": "...",
          "envelope": "code-review.json"
        }
      ]
    }
  ],
  "checks": [
    {
      "name": "independence_capability",
      "result": "not_run",
      "reason": "The host did not expose live launch evidence."
    }
  ],
  "partial": null
}
```

`validate-run` derives the overall `status`; a run record cannot claim it.
`complete` requires every routed track's final attempt to be `completed` with
a current valid envelope. Any missing, unstarted, invalid, blank, truncated,
scope-mismatched, or otherwise unverifiable required track makes the overall
status `blocked`. A valid completed envelope remains in `completed_reports`
in routing-table order when another required track fails. A malformed or
unverifiable track attempt degrades only that track; valid reports from other
tracks remain in the aggregation. Duplicate, unknown, unidentified, or
non-object track entries and malformed `checks` containers or records are
run-level errors, not reasons to discard already valid completed reports. A
valid completed candidate for a routed track remains attributable even when a
duplicate entry is malformed, while the duplicate still makes the run blocked.
Validation fails closed before aggregation only when the run cannot be
interpreted: the run is not an object, required top-level fields are missing
or unknown, `contract_version` is unsupported, `tracks` is not a list, or the
frozen manifest has no usable routing table.
Envelope paths in the run record are relative to the run record's directory.
The command exits zero only for `complete`; `blocked` and `partial` still
print their full result but exit nonzero so neither can pass as a complete
review by command status alone.

Each attempt is `completed` or `failed`. A completed attempt names its
envelope and must use `launch_status: launched`; its envelope track and
invocation IDs must match the attempt. A failed attempt records evidence
appropriate to its class and one of these classes:

- `launch_failure`: the required track could not start.
- `transient_runtime`: an evidenced transient runtime failure.
- `transient_transport`: an evidenced transient transport failure.
- `invalid_result`: the returned result was blank, truncated, or unverifiable.
- `scope_mismatch`: the report did not attest the frozen scope.

A track with no attempts is missing. The coordinator never substitutes a
reviewer, invents an envelope, or lets a single completed track become a
complete review through omission.

One run may perform at most one recovery invocation. Recovery is allowed only
when the immediately preceding attempt failed with `transient_runtime` or
`transient_transport` and supplied structured host evidence. The recovery
attempt has a new `invocation_id`, the same derived `request_sha256` as the
failed attempt, and a `recovery` object:

```json
{
  "recovery": {
    "of_invocation_id": "code-review-001",
    "analysis_reused": false
  }
}
```

`analysis_reused` must be `false`; the recovery receives the original frozen
request and must not reuse the failed attempt's analysis. An implicit retry,
a second recovery, a changed request, or recovery after a non-transient
failure is invalid. Every attempt must use `launch_status: launched` except
`launch_failure`, which must use `not_launched`.

Transient failure evidence has exactly `source`, `phase`, and `detail`.
`source` must be `host`, and `phase` must be `runtime` for
`transient_runtime` or `transport` for `transient_transport`. This validates
the recorded evidence shape, not whether the host actually failed.

`request_sha256` must equal the SHA-256 of canonical JSON containing the
routed `track_id`, frozen `manifest`, and frozen `attestation`. The validator
recomputes that digest for every attempt and requires recovery attempts to
match the failed attempt. This proves the recorded request identity matches
the frozen bundle; it does not prove the host sent those bytes or that hidden
analysis was not reused.

After a blocked result has been shown, an explicit user approval may retain
exactly one completed report as `partial`. First save the blocked
`validate-run` JSON result as an external artifact. Then use a separate
follow-up run record:

```json
{
  "partial": {
    "approval": {
      "source": "user",
      "evidence": "User approved the one-track partial review."
    },
    "blocked_result": {
      "path": "blocked-result.json",
      "sha256": "..."
    },
    "missing_track_ids": ["ponytail-review"],
    "reduced_independence": "Only one of two required independent tracks completed."
  }
}
```

The artifact path is relative to the follow-up run record and cannot be the
current run record or a hard link to it. Its resolved path must remain inside
the run directory. Its exact bytes must match `sha256`; it must contain the
complete `validate-run` result schema with overall status `blocked`, no partial
approval, and rendered output. Its tracks, coverage, checks, missing tracks, and
full completed envelopes and run errors must exactly match the follow-up run.
Its rendered output must exactly equal the canonical render of those blocked
result values; substituted summary or display text is invalid. The approval
source must be `user` and include non-empty evidence. The missing-track list
must match the tracks that did not complete, and exactly one track must have
completed. The derived result labels the run `partial`, records the artifact
digest, missing tracks, reduced independence, coverage, and completed-report
identities, and includes each original completed envelope without truncation.
Partial mode is never a complete parallel review. The digest binds the artifact
content but cannot prove wall-clock order or the human identity behind
`source: "user"`.

Track `coverage.status` remains a report fact separate from launch status. A
valid report may record `partial` or `not_assessed` coverage without being
misreported as a launch failure. Unavailable host independence or recovery
capability is recorded in run `checks` as `independence_capability` or
`recovery_capability` with result `not_run` and a non-empty reason, not
inferred as passed. Every run needs at least one such capability check. A
recovery needs `recovery_capability`; a complete run needs
`independence_capability`. A capability check with result `failed` or
`not_assessed` makes the overall result blocked. A completed report with
`coverage.status: blocked` also makes the overall result blocked with a
distinct `coverage_blocked` run error; the track remains completed and its
original report remains present. `partial` and `not_assessed` coverage remain
visible limitations and do not trigger that failure.

## Severity

- `P0`: data loss, a severe security issue, an unusable core flow, or inability
  to start or deploy.
- `P1`: correctness, security, data-loss risk, an explicit specification
  violation, or a blocker for the main acceptance path.
- `P2`: every other finding, including pure over-engineering findings.

If the evidence does not establish P0 or P1 impact, use P2. The rationale must
distinguish confirmed low impact from insufficient evidence of higher impact.
