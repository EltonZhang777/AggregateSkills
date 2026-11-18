---
name: requirements-to-spec-tickets
description: Turn one or more codebase ideas into approved, independently scoped specs and tracer-bullet tickets through interactive child sessions.
disable-model-invocation: true
---

# /requirements-to-spec-tickets

## Activation Criteria & Objective

Use this skill when the user wants to turn one or more codebase ideas into clarified specs and tickets. It can publish approved local repository artifacts on a task branch; it does not implement application code.

## Dependencies

When this skill's own workflow explicitly reaches a call to one of its directly declared Skill prerequisites, the call is explicit and may proceed even if that prerequisite disables implicit invocation. This waives only that invocation gate. It does not waive other prerequisite instructions or confirmation, authorization, security, or safety gates. It does not authorize transitive calls, create new call steps, or override an explicit prohibition on invoking another skill.

The dependencies listed here are global workflow prerequisites. If any is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

Before starting the workflow, confirm that the `skillroute` command is callable in the current environment.

| Name | Type | Source |
| --- | --- | --- |
| /grill-duo-with-docs | Skill | https://github.com/EltonZhang777/AggregateSkills |
| /to-spec | Skill | https://github.com/mattpocock/skills |
| /to-tickets | Skill | https://github.com/mattpocock/skills |
| /conventional-git-messages | Skill | https://github.com/EltonZhang777/AggregateSkills |
| /setup-matt-pocock-skills | Skill | https://github.com/mattpocock/skills |
| SkillRoute CLI executable (`skillroute`) | Tool | https://github.com/erichare/skillroute |

## 1. Preflight

Confirm that every dependency in the table is available before starting the workflow. Read each direct skill's current `SKILL.md` before using it; treat the live file as the source of truth, and do not copy its body or expand transitive dependencies. Verify that `/setup-matt-pocock-skills` has supplied the issue tracker and triage-label configuration required by `/to-spec` and `/to-tickets`. If the setup or tracker configuration is absent, stop and tell the user to run `/setup-matt-pocock-skills`; do not run setup automatically or create child sessions.

Preflight is complete when all listed dependencies and the tracker configuration are available.

## 2. Turn the request into groups

Read the user's current conversation as the source of the requirements. For each request, propose a group with:

- a short title and feature slug;
- one independent user outcome;
- scope and non-goals;
- acceptance intent;
- confirmation that approval starts the canonical child contract without a per-group opt-in;
- local repository artifacts included in the approved output, if any;
- dependencies on other groups, if any.

For several requests, make one group per independently implementable, single-target behavior. Shared implementation details do not justify merging groups. A single request is one group, but still follows the approval gate.

Show the complete proposed grouping and wait for explicit approval of that complete grouping. Approval starts every approved group under the canonical child contract; no per-group opt-in is required. If the user objects but the requested change is unclear, ask a direct clarification question, then present the revised grouping and wait again.

The grouping step is complete only when the user has explicitly approved the current complete grouping.

## 3. Create interactive child sessions

Create one child session per approved group. Each child must be visible to and directly interactive with the user: the user can enter it, answer its questions, and let it continue. A background subagent does not satisfy this requirement. Name each child session exactly `spec: <feature-slug>`, using the approved group slug that will also identify its spec. In Codex Desktop, pass this as the `title`; on other platforms, use the equivalent session title.

Use the [child-session initial prompt template](references/child-session-initial-prompt.md) as each child's initial prompt or manual handoff. Its copy-ready prompt is the sole normative source for child-executed workflow behavior. Apply its conditional assembly instructions and fill every applicable placeholder with confirmed information before creating or delivering it; do not append a second child protocol.

For independent groups, create child sessions in parallel when the host supports it. For groups with a decision dependency, process the blocker first or make the dependent child wait for the blocker's relevant conclusion. Ticket-level implementation dependencies remain the responsibility of `/to-tickets`.

When multiple approved groups will change local repository files in the shared checkout, serialize their file-writing work. Do not switch branches while another group may write to that checkout. Issue-only groups can still run in parallel.

### Codex Desktop

Use the Codex project/thread creation capability. Identify the current project with `list_projects`, require a unique match, and create each child with the same project and a `local` environment. Use a new task window. Create a worktree only when the user explicitly requests one; otherwise use the shared checkout and follow the filled canonical child contract for write handling. If the project cannot be identified uniquely, pause and ask the user to select or open it; never guess.

### CLI and other coding agents

Use the platform's equivalent visible child conversation or a new terminal session in the same working directory. If the platform cannot create one, provide the filled canonical child contract with its approved group, repository path, dependency information, and known group dependencies. State that the child session still needs to be started by the user. Do not claim that it was created.

Give each child only its filled canonical child contract and confirmed group facts. Do not paraphrase its workflow rules or add another first-response or completion protocol. Keep unrelated sibling requirements and parent-history noise out of the child prompt.

For new or materially rewritten project text, the parent must use the normative prose in the root `AGENTS.md` of the repository receiving that text. When source and target differ, read the target repository's root `AGENTS.md` instead of substituting the source or installation rule. Capture the exact target rule in the template's language-rule field; the canonical child contract governs how the child applies it. Pause child creation and ask if the target rule has no discernible dominant language. Do not modify the external dependency skills.

Child-session creation is complete only when every approved group has a real interactive child-session identifier. If the platform cannot create one, provide the complete manual handoff described above and report the group as blocked; a manual handoff is not a ready child and cannot count toward successful handoff.

## 4. Canonical child contract

The copy-ready prompt in the [child-session initial prompt template](references/child-session-initial-prompt.md) is the sole normative source for child-executed workflow behavior. It defines the child's first response and grilling, phase order and gates, source rereading, issue publication and recovery, Conventional Messages drafting, native sub-issue linking, target-repository language handling, local-artifact publication, optional document integration, authorization, verification, and completion reporting.

Do not restate, duplicate, or redefine those child-executed workflow rules in this guide or in a handoff. The parent keeps only these lifecycle responsibilities: dependency preflight, grouping approval, interactive child creation, shared-checkout write serialization, child-readiness evidence, handoff, retry, and resumption. When validating a child, use the canonical child contract's observable evidence and the readiness checks in Section 5; do not execute the child's phases or answer its user-facing questions.

## 5. Child readiness, handoff, and resumption

The parent's only validation interface is readiness evidence: the first response and first actual grilling turn must meet the filled canonical child contract before handoff. For each group, it verifies:

- the first response and first actual grilling turn meet the filled canonical child contract, cover the group's essentials without substantive contradiction, and demonstrate its required wait, including its no-decisions confirmation path;
- the child is a real interactive session the user can enter and continue.

A group is ready only when both checks pass. A prompt, returned session identifier, child status, or elapsed time alone is not readiness evidence. Keep each group's state distinct. Continue unaffected groups where possible and preserve already-created sessions.

Handle creation and startup outcomes as follows:

- A pending child with no first response remains pending. Ask the user whether to wait or authorize a retry; a timeout never changes it to ready.
- Report explicit creation or child errors and wait for the user's decision before retrying.
- Reconcile an ambiguous creation result against the known operation or child-session state before considering any retry. If the result remains uncertain, report the evidence and ask the user how to proceed. Never retry automatically or create a duplicate.

If not every group is ready, report each group's child link or missing-session state, readiness evidence, and concrete blocker. Do not claim successful handoff. Ask only for the action needed to resolve pending, failed, or uncertain states.

When every approved group is ready, give one handoff summary containing, for each group, the interactive child link, evidence for both readiness checks, known blockers, and artifacts available at that point (such as spec, document, or ticket links, or that none exist yet). Send it once. Then stop tracking or aggregating the children's later grilling, specs, tickets, shared documents, conflicts, or issue links. Each child reports its later results directly to the user.

On resumption, inspect existing child-session status and first-turn evidence, reuse known identifiers, and reconcile uncertain creation outcomes before acting. For local-artifact groups, also reconcile the approved group, checkout, branch, local commits, upstream, and exact remote ref before resuming the child handoff; do not rerun or paraphrase the canonical publication rules.

Do not install skills, run setup, modify the dependency skills, implement application code, or open pull requests as part of this workflow. The canonical child contract owns task-scoped Git publication; this guide does not add a separate branch or issue-publication protocol.
