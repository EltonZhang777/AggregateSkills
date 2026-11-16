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

- one existing root `AGENTS.md` or `CLAUDE.md` with its `## Agent skills` configuration;
- `docs/agents/issue-tracker.md`;
- `docs/agents/domain.md`.

Read those files and the live `/setup-matt-pocock-skills` guide. If the setup output is absent or ambiguous, tell the user to run `/setup-matt-pocock-skills` and stop. Do not create that setup, invoke the dependency automatically, or modify the dependency skill.

Preflight is complete only when exactly one instruction file can be identified as the existing agent configuration target and both required guides are readable.

Use the target repository's root instruction file as the only language policy for new or materially rewritten project text. If its normative prose has no discernible dominant language, ask the user before writing. Preserve untouched text and report any resulting language mixture. The templates are English source text: translate a confirmed section into the target language during draft composition, then include the complete translated draft in the review.

## 2. Explore before asking

Collect repository facts without writing:

- the instruction file selected by the existing setup, and every managed section already present in it;
- version control, repository root, remote, forge, issue tracker, and the tracker guide's existing read conventions;
- checkout mode: shared checkout, dedicated clone, or worktree use when the repository exposes that distinction;
- host and repository shell conventions, without choosing a shell for the repository;
- verification surfaces such as automated tests, static checks, CI, environment-dependent checks, manual acceptance, and any application or product runtime;
- whether handoffs, shared sessions, or external actions already carry approval records;
- the glossary layout and existing language, including mixed-language content.

Inspect the content that each proposed managed section would replace. When summary-first issue reads are enabled for GitHub, compare the tracker guide with the three legacy defaults in `references/tracker-migration.md` by their content, not line numbers. If any listed legacy default exists, all three must exist exactly once and unchanged; if one is missing, appears more than once, or has changed, record the migration as blocked and do not guess. If none exists, preserve the guide and deploy only the confirmed sections. For another tracker, skip the GitHub migration and preserve its native read commands.

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

Read the templates under `references/` and compose the draft from only the confirmed themes. All deployable document text belongs in those templates, not in this entrypoint. Replace the `<instruction-file>` placeholder with the root instruction file selected in preflight. When the optional cache is declined, keep the disabled cache-posture sentence from `issue-operations.md`. When it is confirmed, replace that sentence with the navigation-only cache template instead of deploying both cache postures.

Use stable HTML-comment managed sections identified by the `extra-setup-matt-pocock-skills` namespace, a section-specific ID, and `start`/`end` suffixes. Each managed section must have exactly one start marker and one matching end marker.

For every target file, show:

- the exact insertion or replacement diff;
- unchanged context around the managed range;
- any first-run removal of the three legacy tracker defaults;
- the final managed-section boundaries.

When summary-first issue reads are enabled on the first run for a GitHub guide that contains any listed legacy default, show the exact tracker migration from `references/tracker-migration.md` as part of the same complete draft. Replace all three legacy defaults with the listed pointers to the single managed issue-operations section. If summary-first issue reads are disabled, preserve the existing read conventions even when another issue theme is enabled. On reruns, replace only the confirmed managed section and show that exact replacement diff.

Stop before writing when a marker is missing, duplicated, reversed, or ambiguous; when the migration text has drifted; when ownership appears inside a range this skill does not own; or when the draft would alter unrelated text. Do not normalize or opportunistically rewrite existing prose.

The draft gate passes only after the user reviews the complete set of file changes and explicitly approves writing them.

## 5. Write and verify

Write only the approved managed ranges. Leave all text outside those ranges unchanged. Do not create an ADR or application runtime, and do not modify `/setup-matt-pocock-skills` or any other dependency.

After writing, verify:

- each expected managed section has exactly one complete marker pair;
- the migrated tracker has no legacy issue-read or issue-list default remaining;
- the deployed section matches the reviewed draft;
- content outside the managed ranges is byte-for-byte unchanged.

If verification fails, preserve the current files, report the exact mismatch, and stop. Do not claim a successful setup when only static inspection ran; manual acceptance remains separate.
