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

The objective is one reproducible orchestration pass over one frozen code scope. The routing table decides which tracks run and in what order. The contract is the sole normative source for [Frozen scope and tree](references/contract.md#frozen-scope-and-tree), [Output boundary](references/contract.md#output-boundary), [Upstream resolution and pins](references/contract.md#upstream-resolution-and-pins), the [Common report envelope](references/contract.md#common-report-envelope), [Evidence boundary](references/contract.md#evidence-boundary), [Coordinator run aggregation](references/contract.md#coordinator-run-aggregation), and [One-track partial results](references/contract.md#one-track-partial-results). This entry point owns activation, preflight order, command forms, dispatch sequence, and links to those sections; it does not own any upstream track's review criteria.

## Preflight the routed contract

Read [the route table](references/routing-table.md) and [the contract](references/contract.md). The route table is the only activation registry. Its row order defines dispatch, collection, and aggregation order. Do not infer tracks from adapter files and do not hardcode a track count.

For every routed row, read its fixed-marker JSON metadata, resolve the declared upstream skill through the current host and SkillRoute, and collect its required manifest inputs. Apply [Upstream resolution and pins](references/contract.md#upstream-resolution-and-pins) for identity, contract version, exact-byte pinning, failure aggregation, and diagnostic order. Report every missing shared or routed dependency together, and do not dispatch while a required dependency or input other than standalone `requirements` is unresolved.

Run the package validator with the coordinator-resolved inputs:

```text
python scripts/review_contract.py preflight --skill-root <skill package root> \
  --upstream /code-review=<resolved SKILL.md or URI> \
  --upstream /ponytail-review=<resolved SKILL.md or URI> \
  [--upstream-exact-sha /code-review=<exact-sha256>] \
  [--upstream-size /code-review=<exact-bytes>] \
  [--upstream-sha /code-review=<normalized-text-sha256>]
```

The validator does not run SkillRoute or fetch remote text. Pass each coordinator-resolved source explicitly; [Upstream resolution and pins](references/contract.md#upstream-resolution-and-pins) defines how local and remote resolutions are validated and pinned. Any failure blocks the run before dispatch.

## Freeze one review scope

Before any track starts, freeze one immutable patch/tree snapshot. [Frozen scope and tree](references/contract.md#frozen-scope-and-tree) defines the permitted scope sources, bundle and tree mechanics, exclusions, non-regular entry rejection, pins, freshness, and staleness. Apply [Output boundary](references/contract.md#output-boundary) before selecting the bundle path.

Use the package script:

```text
python scripts/review_contract.py freeze --repo <repo> --output <external bundle> --range <base...head> \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source> \
  --upstream /ponytail-review=<resolved source>
python scripts/review_contract.py freeze --output <external bundle> --patch <patch> --tree-root <frozen tree> \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source> \
  --upstream /ponytail-review=<resolved source>
python scripts/review_contract.py freeze --repo <repo> --output <external bundle> --uncommitted \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source> \
  --upstream /ponytail-review=<resolved source>
```

For each routed remote URI, also pass `--upstream-exact-sha <track>=<exact digest>` and `--upstream-size <track>=<exact bytes>`; `--upstream-sha` is optional normalized attestation. Supply pinned requirements and standards with repeatable `--requirements` and `--standards`. When the routed adapters require `checks`, supply `--check NAME=RESULT` or `--not-run NAME=REASON`; record every exclusion with `--exclude PATH=REASON`. A `/spec-implement-loop` final-review freeze also passes `--require-requirements`. See the [Required input registry](references/contract.md#required-input-registry) for accepted values and required-input semantics.

Before each track starts, run:

```text
python scripts/review_contract.py verify --bundle <bundle> --repo <repo> \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source> \
  --upstream /ponytail-review=<resolved source>
python scripts/review_contract.py verify --bundle <bundle> --patch <patch> \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source> \
  --upstream /ponytail-review=<resolved source>
```

The contract defines which live locator each scope requires and every freshness check. Treat anything other than a current result as blocked; do not present stale findings as current or silently re-freeze mid-run. For a remote upstream, pass the same exact digest and size pin used by freeze.

## Dispatch each review track

For each route-table row, in row order, load the referenced adapter and start its review track in its own independent sub-agent. Give every track the identical bundle, manifest digest, patch attestation, included paths, requirements or their recorded `not_assessed` status, standards, checks, and exclusions. Do not let a track read a live ref or live workspace file in place of the frozen bundle.

The `/code-review` adapter keeps its upstream review track and internal Standards and Spec sub-agents and aggregation. Read the original upstream `/code-review` skill before invoking it. Execute that review contract against the sealed patch and frozen tree. Preserve both review axes and their original order.

Never simulate a missing reviewer or substitute a single agent for an independent track. If the host cannot start the required independent sub-agent, return a blocked pre-dispatch result. If host independence or model discovery cannot be demonstrated, mark that live check `not run`; do not report it as passed.

## Validate the common envelope

Validate every routed track report against the [Common report envelope](references/contract.md#common-report-envelope). The contract defines the required fields, source matching, coverage-check equality, and finding-preservation rules; a report that fails validation blocks the run.

Run:

```text
python scripts/review_contract.py validate-envelope --bundle <bundle> --envelope <track report> \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source> \
  --upstream /ponytail-review=<resolved source>
```

Only validated reports may proceed to presentation. Apply the contract's preservation and blocking rules, and use `Not stated by the source track` when an upstream section did not state a required presentation field. Apply the [Evidence boundary](references/contract.md#evidence-boundary) when interpreting static or synthetic test data.

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

## Block required-track failures

Aggregate the validated track results with one coordinator run record and run:

```text
python scripts/review_contract.py validate-run --bundle <bundle> --run <run record> --repo <repo> \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source> \
  --upstream /ponytail-review=<resolved source>
python scripts/review_contract.py validate-run --bundle <bundle> --run <run record> --patch <patch> \
  --contract-root <skill package root> \
  --upstream /code-review=<resolved source> \
  --upstream /ponytail-review=<resolved source>
```

Use [Coordinator run aggregation](references/contract.md#coordinator-run-aggregation) for run status, freshness and stale-scope precedence, recovery, capability checks, and completed-report preservation. Use [One-track partial results](references/contract.md#one-track-partial-results) for any degraded result after the blocked result is shown.

If `validate-run` produces a blocked result, show it before requesting one-track partial approval. The contract owns the partial artifact and follow-up-run requirements; do not restate or relax them here.

## Read-only boundary

Do not write to the reviewed repository, apply the patch, create review branches, stage files, commit, push, open pull requests, update issues, or run write-producing checks. Write only the explicit external bundle and, when requesting partial mode, its blocked-result artifact. Report checks that were not run with their reason instead of implying they passed.
