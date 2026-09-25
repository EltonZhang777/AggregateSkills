---
name: review-duo
description: Run code-review in opt-in strict mode with one fixed scope, independent review axes, and evidence-based findings.
metadata:
  prerequisites: '{"skills":[["code-review","mattpocock/skills"]],"mcps":[],"tools":[]}'
---

# Review Duo

Use this skill only when the user explicitly requests `review-duo` or strict `code-review`. It adds a strict contract to the existing `code-review` workflow; it is not a second review implementation.

## Resolve and run the upstream skill

Resolve the current `code-review` skill through the host's native skill resolver at runtime, then follow that skill once. If it is unavailable, stop and tell the user to install it with `npx skills@latest add mattpocock/skills --skill=code-review`. Never copy a fallback body or continue with a locally vendored version.

Keep the upstream workflow and its two-agent topology. Pass the strict scope and axis instructions below to those two agents in that one run. Do not start another review pair or nest a second `code-review` run. If this invocation cannot start two independent agents, set the overall status to `blocked` before reviewing; do not simulate two reviewers in one context. Ask the user to retry in a host with parallel-agent support or explicitly approve single-agent degradation. If the host cannot pass the same fixed inputs to both agents, stop with status `blocked`.

## Freeze the review inputs

Use upstream `code-review`'s fixed-point flow for Git reviews. For a supplied patch or uncommitted work, replace the moving-ref input with one immutable patch snapshot and pass that exact diff to the same two agents. Give both agents the same pinned inputs:

- For Git reviews, resolve and record the full base, merge-base, and head commit SHAs once. Use that immutable range for both agents.
- For a supplied patch or uncommitted work, capture one content-addressed patch snapshot, including the intended staged, unstaged, and new files. Record its SHA-256, byte size, and included paths. Pass its exact bytes or immutable shared path and hash instead of manufacturing a Git diff command or commit list. Both agents must read that exact snapshot; never substitute separate live-workspace reads.
- Pin requirement sources from the user's request, issue/PR body and acceptance criteria, design docs, and applicable contracts or ADRs. Record their revision or content hash. Commit messages, branch names, tests, and existing implementation are not requirements. If no requirement source exists, the Spec axis is `not_assessed`; do not infer requirements from code.
- Pin applicable repository standards, including root and relevant-path `AGENTS.md`, domain docs, ADRs, and formatter, lint, type-check, build, and test configuration. Give both agents the same source contents or immutable revisions and record their hashes.

Before starting the agents, freeze one coverage manifest containing the code scope, pinned requirement and standards sources, relevant implementation and test sources, explicit exclusions, and relevant checks. For each source, record its path or stable URI, role, pinned revision or SHA-256, and included or excluded status; give exclusions a reason. For each relevant check, record its name, command, observed result, or `not run` with a reason. A source an axis did not inspect remains unchecked.

Serialize the manifest as canonical UTF-8 JSON with sorted keys and source entries ordered by path. Hash its exact bytes with SHA-256 and keep the digest outside the manifest. Give both agents the identical manifest bytes and digest, or the same immutable path and digest. Do not reconstruct it from separate live-workspace reads or change it during the review.

At finalization, report the manifest digest and, for each axis, the checked and unchecked sources and checks. A missing or unreadable declared source makes coverage partial. If a pinned source, manifest, or recorded check result changes after the freeze, mark the report stale.

If either agent cannot read or verify the same fixed code scope, set the overall status to `blocked`, preserve any completed axis results, and pause. If a relevant evidence source is unavailable to an axis, mark that axis `partial` and state the gap. Before finalizing, verify that the patch/range and source hashes still match. If any pinned input changed, mark the report `stale`; do not present it as current or silently rerun it.

## Independent review axes

Start the upstream workflow's two agents in parallel, with no cross-agent discussion:

- **Standards and Quality** checks repository rules, correctness, error handling, security, concurrency, retries, consistency, APIs, databases, migrations, lifecycle, important test gaps, and material maintenance cost. It does not decide whether the change satisfies product requirements.
- **Spec Conformance** checks only missing, partial, or incorrect requirements, unmet acceptance criteria, unrequested behavior, and conflicts or gaps in requirement sources. It does not report style or preference opinions.

A finding must have a concrete location and evidence, an actual impact, and a recommendation. Exclude preference-only observations. Use only these severities:

- `blocker`: severe data or security risk, unusable core flow, or unsafe acceptance failure.
- `high`: major correctness failure, inconsistent persisted state, or a key requirement missed.
- `medium`: meaningful boundary, reliability, or test-coverage issue.
- `low`: localized quality issue with limited impact.

Assign stable per-axis IDs in the form `STD-01` and `SPEC-01`, in each agent's original finding order. Each finding includes location, problem, evidence, impact, recommendation, and severity. Preserve every axis's findings, severity, and order. The same issue may appear on both axes; never merge, remove, rerank, or change severity across axes. Do not give one overall score.

Mark an axis `partial` when its evidence or coverage is incomplete and state the limitation. The Spec axis may be `not_assessed` only when no requirement source exists. If the second agent cannot start or read the fixed scope, mark the review `blocked` and pause. Do not degrade to one agent unless the user explicitly approves; after approval, label the mode `single-agent degradation`, keep the two axes separate, and state that the results lack dual-agent independence.

## Final report

Return a read-only report in the user's language. Include:

- Fixed scope: immutable commit range or patch SHA-256, byte size, and included paths.
- Mode: `dual-agent` or explicitly approved `single-agent degradation`; overall status: `current`, `stale`, or `blocked`.
- Requirement and standards sources with their pinned revisions or hashes.
- Separate `Standards and Quality` and `Spec Conformance` sections. For each, include status (`complete`, `partial`, `blocked`, or `not_assessed`), finding count, all findings in original order, and checked/unchecked coverage.
- Checks not run, with the reason, and any generated, vendor, binary, or other excluded files.

Do not modify code, create tasks, run write-producing checks, commit, push, or update a PR. Report checks that were not run instead of implying they passed.