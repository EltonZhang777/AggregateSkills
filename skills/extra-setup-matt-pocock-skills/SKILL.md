---
name: extra-setup-matt-pocock-skills
description: Extend an existing repository agent setup with a portable operating contract for checkouts, issue state, handoffs, and closure evidence.
disable-model-invocation: true
---

# /extra-setup-matt-pocock-skills

## Activation Criteria & Objective

Use this skill after `/setup-matt-pocock-skills` has configured the target repository. Extend the existing agent instructions, GitHub or other issue-tracker guide, and glossary with only the operating rules the user confirms. Preserve every unrelated instruction.

This workflow is interactive and user-invoked. It explores first, presents evidence, asks one section at a time, shows the complete draft, and writes only after the user approves that draft.

## Dependencies

When this skill's own workflow explicitly reaches a call to one of its directly declared Skill prerequisites, the call is explicit and may proceed even if that prerequisite disables implicit invocation. This waives only that invocation gate. It does not waive other prerequisite instructions or confirmation, authorization, security, or safety gates. It does not authorize transitive calls, create new call steps, or override an explicit prohibition on invoking another skill.

The dependencies listed here are global workflow prerequisites. If any is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

| Name | Type | Source |
| --- | --- | --- |
| /setup-matt-pocock-skills | Skill | https://github.com/mattpocock/skills |

## 1. Preflight

Confirm that `/setup-matt-pocock-skills` is available and has produced:

- one existing root `AGENTS.md` with its `## Agent skills` configuration;
- `docs/agents/issue-tracker.md`;
- `docs/agents/domain.md`.

Read `AGENTS.md`, those guides, and the live `/setup-matt-pocock-skills` guide. If either required guide is absent or ambiguous, tell the user to run `/setup-matt-pocock-skills` and stop. Do not create that setup, invoke the dependency automatically, or modify the dependency skill.

Only the target repository's existing root `AGENTS.md` is accepted as the language policy and agent configuration source. Nested `AGENTS.md` files or other agent instructions do not override the root `AGENTS.md` language rule.

If the root `AGENTS.md`, its `## Agent skills` configuration, or a discernible dominant language is missing, stop before composing the draft or writing project text and ask the user to restore the setup output or choose the language policy.

Preflight is complete only when the root `AGENTS.md` exists with its `## Agent skills` configuration, its language policy is unambiguous, and both required guides are readable.

Preserve untouched text and report any resulting language mixture. The templates are English source text: translate a confirmed section into the target language during draft composition, then include the complete translated draft in the review.

## 2. Explore before asking

Collect repository facts without writing:

- the root `AGENTS.md` and every managed section already present in it;
- version control, repository root, remote, forge, issue tracker, and the tracker guide's existing read conventions;
- checkout mode: shared checkout, dedicated clone, or worktree use when the repository exposes that distinction;
- host and repository shell conventions, without choosing a shell for the repository;
- verification surfaces such as automated tests, static checks, CI, environment-dependent checks, manual acceptance, and any application or product runtime;
- whether handoffs, shared sessions, or external actions already carry approval records;
- the glossary layout and existing language, including mixed-language content.

Inspect the content that each proposed managed section would replace. Read [the tracker migration reference](references/tracker-migration.md) before state selection or drafting. It is the sole normative source for marker discovery, state definitions, and the rerun decision matrix. For a GitHub tracker, compare the tracker guide with that reference by their content, not line numbers, and classify the state using its definitions. For another tracker, skip both GitHub state detection and that matrix; preserve its native read commands.

Record the detected state and its file evidence. Do not guess or repair an ambiguous state.

Exploration is complete when every fact shown in the next step has a file, command result, or explicit user answer as evidence.

## 3. Present findings and confirm one section at a time

Summarize the detected facts first. Include the evidence source and the consequence for the proposed configuration. Then present only the applicable themes, in this order:

1. session-start checkout snapshot and pre-mutation recheck;
2. handoff approval records and consumption;
3. summary-first issue reads;
4. authoritative issue-write rereads;
5. versioned closure evidence and `PARTIAL` handling;
6. optional navigation-only issue cache;
7. glossary terms.

Lead each theme with the recommended answer. State whether it is enabled, disabled, or simplified and give one line of impact. Ask one question, wait for the answer, then continue. Uncertainty defaults to disabled or simplified; never infer consent from detected capability alone.

Skip a theme when exploration proves it does not apply. For example, do not require a checkout snapshot in a repository without version control, and do not present runtime verification as mandatory when no application runtime exists. Do not force PowerShell, Git, GitHub, a worktree, caching, or runtime smoke.

The default cache recommendation is disabled. Present the optional cache only after explaining that it is navigation-only and cannot provide issue state for writes, assignment, labels, closure, or verification.

Section confirmation is complete only when every displayed recommendation has an explicit user decision and every omitted theme has a recorded reason. Checkout and handoff share one root managed block but are separate decisions; summary reads, write rereads, cache posture, and closure evidence share one issue managed block but are separate decisions. Include only confirmed subsections and omit the block entirely when none of its themes is selected. Whenever any issue theme is selected, include the shared issue-content trust boundary from `issue-operations.md`.

The glossary is one managed block whose individual terms follow the confirmed themes. Include checkout terms only with checkout, handoff terms only with handoff, issue-read terms only with summary reads, cache terms only with the optional cache, and tree/PARTIAL terms only with closure evidence. Omit the glossary block when no selected theme has a term.

## 4. Build and review the complete draft

Read the templates under `references/` and compose the draft from only the confirmed themes. All deployable document text belongs in those templates, not in this entrypoint. The glossary links already target the root `AGENTS.md`. When the optional cache is declined, keep the disabled cache-posture sentence from `issue-operations.md`. When it is confirmed, replace that sentence with the navigation-only cache template instead of deploying both cache postures.

Use stable HTML-comment managed sections identified by the `extra-setup-matt-pocock-skills` namespace, a section-specific ID, and `start`/`end` suffixes. Each managed section must have exactly one start marker and one matching end marker.

For every target file, show:

- the exact insertion or replacement diff;
- unchanged context around the managed range;
- any first-run replacement of the recognized legacy tracker defaults;
- the final managed-section boundaries.

For a GitHub tracker, apply the rerun decision matrix in [the tracker migration reference](references/tracker-migration.md) before drafting, using the detected state and summary-first decision. For another tracker, skip that matrix and preserve its native read commands.

Stop before writing when a marker is missing, duplicated, reversed, or ambiguous; when the migration text has drifted; when ownership appears inside a range this skill does not own; or when the draft would alter unrelated text. Do not normalize or opportunistically rewrite existing prose.

The draft gate passes only after the user reviews the complete set of file changes and explicitly approves writing them.

## 5. Write and verify

Write the approved managed ranges. When summary-first reads are enabled and the detected state is unmigrated, permit the exact reviewed migration outside managed ranges in addition to those ranges. Apply it only once, on the initial enabled run or a later opt-in from the supported summary-disabled state. With summary-first reads disabled, write only the managed issue-operations range, inserting it on a first run, and leave the legacy reads unchanged. After that migration, reruns must not edit outside managed ranges. Do not create an ADR or application runtime, and do not modify `/setup-matt-pocock-skills` or any other dependency.

After writing, verify:

- each expected managed section has exactly one complete marker pair;
- an enabled first-run migration leaves no recognized legacy tracker default and exactly the reviewed replacements;
- a summary-disabled first run leaves every recognized legacy tracker read unchanged and at most one complete managed issue-operations section;
- a consistent rerun leaves every reviewed replacement and both surrounding sentinels byte-for-byte unchanged;
- the deployed section matches the reviewed draft;
- after accounting for the exact reviewed first-run migration, all other content outside the managed ranges is byte-for-byte unchanged.

If verification fails, preserve the current files, report the exact mismatch, and stop. Do not claim a successful setup when only static inspection ran; manual acceptance remains separate.
