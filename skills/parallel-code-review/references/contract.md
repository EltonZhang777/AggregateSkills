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
non-deleted changed path must exist in that tree or freeze fails. The
coordinator never applies the patch to create live review context.

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

## Severity

- `P0`: data loss, a severe security issue, an unusable core flow, or inability
  to start or deploy.
- `P1`: correctness, security, data-loss risk, an explicit specification
  violation, or a blocker for the main acceptance path.
- `P2`: every other finding, including pure over-engineering findings.

If the evidence does not establish P0 or P1 impact, use P2. The rationale must
distinguish confirmed low impact from insufficient evidence of higher impact.
