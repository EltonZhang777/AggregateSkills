---
name: parallel-code-review
description: Run parallel review and combined review tracks with independent reviewers over one frozen scope, including /spec-implement-loop final review; explicit /parallel-code-review invocation always works, but do not use this skill for a generic single-path review.
---

# /parallel-code-review

## Dependencies

When this skill's own workflow explicitly reaches a call to one of its directly declared Skill prerequisites, the call is explicit and may proceed even if that prerequisite disables implicit invocation. This waives only that invocation gate. It does not waive other prerequisite instructions or confirmation, authorization, security, or safety gates. It does not authorize transitive calls, create new call steps, or override an explicit prohibition on invoking another skill.

If a shared dependency is missing, report all missing shared dependencies, tell the user to install them, and stop. Routed upstream skills are declared by adapter metadata; resolve all of them during preflight and report every missing upstream together. Do not install dependencies automatically.

Before dispatch, confirm that the `skillroute` command and the host's independent sub-agent capability are callable.

| Name | Type | Source |
| --- | --- | --- |
| SkillRoute CLI executable (`skillroute`) | Tool | https://github.com/erichare/skillroute |
| Host independent sub-agent runtime | Tool | Not declared |

## Activation Criteria & Objective

Use this skill for an explicit `/parallel-code-review` request, a request for parallel review, combined review tracks, multiple independent reviewers over one frozen scope, or `/spec-implement-loop` final review. Do not select it for a generic single-path review request; those requests continue to use their named single review path.

The objective is one reproducible orchestration pass over one frozen code scope. The routing table decides which tracks run and in what order. This entrypoint owns preflight, freezing, dispatch, envelope validation, and presentation. It does not own any upstream track's review criteria.

## Preflight the routed contract

Read [the route table](references/routing-table.md) and [the contract](references/contract.md). The route table is the only activation registry. Its row order defines dispatch, collection, and aggregation order. Do not infer tracks from adapter files and do not hardcode a track count.

Resolve every routed upstream through the host first, then run the package
validator with those resolution inputs:

```text
python scripts/review_contract.py preflight --skill-root <skill package root> \
  --upstream /code-review=<resolved SKILL.md or URI> \
  [--upstream-exact-sha /code-review=<exact-sha256>] \
  [--upstream-size /code-review=<exact-bytes>] \
  [--upstream-sha /code-review=<normalized-text-sha256>]
```

The validator pins the route table, every routed adapter, and every resolved
upstream by exact-byte SHA-256 and exact byte size. It retains a normalized-text
SHA-256 as separate attestation when text normalization is needed. It rejects
an empty route table and any missing, duplicate, unreadable, malformed, version-mismatched, or orphan adapter metadata. It also rejects duplicate
metadata blocks, unknown metadata fields, unsafe adapter paths, unknown
required-input categories, and unresolved upstreams. Any of these failures
blocks the run before dispatch.

An upstream identity is `(name, source)`. Adapters may share the same identity,
but a declared name must not map to multiple sources; that conflict fails with
`upstream_identity_conflict` before resolution or pin creation.

For every routed row, read its fixed-marker JSON metadata, resolve the declared upstream skill through the current host and SkillRoute, and collect its required manifest inputs. Report all missing upstream dependencies and inputs together, then stop. Do not dispatch a track while any required dependency or input is unresolved. Verify that every metadata block uses the exact shared contract version before starting work.

The validator does not run SkillRoute or fetch remote text. Pass the
coordinator-resolved upstream source explicitly. A local skill file or skill
directory is read and hashed by the validator. A remote URI must be paired with
the exact-byte SHA-256 and exact byte size returned by the host resolution; a
normalized-text SHA-256 is optional separate attestation and cannot substitute
for exact identity. Missing, unreadable, empty, size-mismatched, or
hash-mismatched resolutions block the run.

## Freeze one review scope

Freeze one immutable patch/tree snapshot before starting any track. The snapshot must originate from exactly one of:

- a Git range;
- an explicit patch plus its frozen code tree;
- the current uncommitted worktree state.

Use the package script with an output directory outside the reviewed repository:

```text
python scripts/review_contract.py freeze --repo <repo> --output <external bundle> --range <base...head> --contract-root <skill package root> --upstream /code-review=<resolved source>
python scripts/review_contract.py freeze --output <external bundle> --patch <patch> --tree-root <frozen tree> --contract-root <skill package root> --upstream /code-review=<resolved source>
python scripts/review_contract.py freeze --repo <repo> --output <external bundle> --uncommitted --contract-root <skill package root> --upstream /code-review=<resolved source>
```

For a remote URI, also pass `--upstream-exact-sha /code-review=<exact digest>`
and `--upstream-size /code-review=<exact bytes>`; `--upstream-sha` is optional
normalized attestation. Supply pinned requirements and standards with
repeatable `--requirements` and `--standards`. When the routed adapters require
`checks`, supply at least one `--check NAME=RESULT` or `--not-run NAME=REASON`;
`--check` accepts `passed`, `failed`, or `not_assessed`, while `not_run` must
use `--not-run` with a non-empty reason. Record every exclusion with `--exclude
PATH=REASON`.

The bundle contains the exact patch, the frozen code tree, pinned input snapshots, a canonical manifest, and a separate patch/manifest attestation. The manifest records the manifest digest source, included sources, checks, exclusions, routing/adapter/upstream pins, and the scope identity. For an explicit patch, every non-deleted changed path must exist in the supplied tree or the freeze fails. Do not reconstruct inputs from live workspace reads after the freeze.

Every supplied `--repo` path is resolved immediately to its Git top level.
The output directory must stay outside that reviewed repository and outside any
Git repository containing the frozen tree.

Before each track starts, run:

```text
python scripts/review_contract.py verify --bundle <bundle> \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source>
```

A changed patch, tree source, pinned input bytes, manifest, route table, adapter document, or upstream pin makes the run stale. Stop and report stale; do not present stale findings as current and do not silently re-freeze mid-run.

Verify and `validate-envelope` always require `--upstream`; do not fall back to
the manifest copy. For a remote upstream, pass the same exact digest and size
pin used by freeze.

## Dispatch each review track

For each route-table row, in row order, load the referenced adapter and start its review track in its own independent sub-agent. Give every track the identical bundle, manifest digest, patch attestation, included paths, requirements, standards, checks, and exclusions. Do not let a track read a live ref or live workspace file in place of the frozen bundle.

The `/code-review` adapter keeps its upstream review track and internal Standards and Spec sub-agents and aggregation. Read the original upstream `/code-review` skill before invoking it. Execute that review contract against the sealed patch and frozen tree. Preserve both review axes and their original order.

Never simulate a missing reviewer or substitute a single agent for an independent track. If the host cannot start the required independent sub-agent, return a blocked pre-dispatch result. If host independence or model discovery cannot be demonstrated, mark that live check `not run`; do not report it as passed.

## Validate the common envelope

Every track returns the versioned common report envelope defined in the contract. It includes its track ID, launch status, coverage, native report extras, manifest and patch attestation, and findings in original order.

Every finding includes its native axis, ID, severity, and group when the upstream track supplies them; an evidence-based P0/P1/P2 severity; a one-sentence severity rationale; a title and exact location; `What this is`; `Problem`; `Fix`; `If we skip it`; and exact source citations. Use `Not stated by the source track` when an upstream section did not state a required presentation field.

Run:

```text
python scripts/review_contract.py validate-envelope --bundle <bundle> --envelope <track report> \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source>
```

The coordinator validates the schema, routed track ID, contract version, and attestation. It must validate but do not reclassify or reorder findings, change native severity or grouping, merge findings, or choose a cross-track winner. A malformed, truncated, blank, stale, or attestation-mismatched report blocks the run.

Checked source hashes must match the frozen manifest. Every finding location
must exist in the frozen tree at a valid line, and every citation must match
the exact frozen or pinned source text. A synthetic envelope used by package
tests only validates coordinator behavior; it is not evidence that a live
model, model discovery, or an independent reviewer ran.

Present native track sections separately, preserve route order and finding order, and render each finding as:

```text
<title>
<exact location>
Severity: P0/P1/P2 — <evidence-based rationale>
What this is: ...
Problem: ...
Fix: ...
If we skip it: ...
```

Show native axis, ID, severity, or group separately when present. Report launch status, coverage, findings, and any unavailable check as separate facts.

## Read-only boundary

Do not write to the reviewed repository, apply the patch, create review branches, stage files, commit, push, open pull requests, update issues, or run write-producing checks. Write only the explicit external bundle. Report checks that were not run with their reason instead of implying they passed.
