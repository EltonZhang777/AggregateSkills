---
name: requirements-to-spec-tickets
description: Turn one or more codebase ideas into approved, independently scoped specs and tracer-bullet tickets through interactive child sessions.
disable-model-invocation: true
---

# /requirements-to-spec-tickets

## Activation Criteria & Objective

Use this skill when the user wants to turn one or more codebase ideas into clarified specs and tickets. It can publish approved local repository artifacts on a task branch; it does not implement application code.

## Dependencies

If any dependency is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

| Name | Type | Source |
| --- | --- | --- |
| /grill-duo-with-docs | Skill | https://github.com/EltonZhang777/AggregateSkills |
| /to-spec | Skill | https://github.com/mattpocock/skills |
| /to-tickets | Skill | https://github.com/mattpocock/skills |
| /setup-matt-pocock-skills | Skill | https://github.com/mattpocock/skills |
| SkillRoute CLI | Tool | https://github.com/erichare/skillroute |

## 1. Preflight

Confirm that every dependency in the table is available before starting the workflow. Read each direct skill's current `SKILL.md` before using it; treat the live file as the source of truth, and do not copy its body or expand transitive dependencies. Verify that `/setup-matt-pocock-skills` has supplied the issue tracker and triage-label configuration required by `/to-spec` and `/to-tickets`. If the setup or tracker configuration is absent, stop and tell the user to run `/setup-matt-pocock-skills`; do not run setup automatically or create child sessions.

Preflight is complete when all listed dependencies and the tracker configuration are available.

## 2. Turn the request into groups

Read the user's current conversation as the source of the requirements. For each request, propose a group with:

- a short title and feature slug;
- one independent user outcome;
- scope and non-goals;
- acceptance intent;
- explicit opt-in to the canonical `/grill-duo-with-docs` two-agent grilling and confirmed project-document updates;
- local repository artifacts included in the approved output, if any;
- dependencies on other groups, if any.

For several requests, make one group per independently implementable, single-target behavior. Shared implementation details do not justify merging groups. A single request is one group, but still follows the approval gate.

Show the complete proposed grouping with each group's opt-in clearly identified. Wait for explicit approval that names or clearly includes the `/grill-duo-with-docs` two-agent grilling and document-maintenance phase; a generic grouping approval does not authorize it. Do not create a child session for a group whose opt-in is declined or unresolved. If the user objects but the requested change is unclear, seek opt-in before using `/grill-duo-with-docs` for clarification; without opt-in, ask a direct clarification question and do not invoke it. Then present the revised grouping and wait again.

The grouping step is complete only when the user has explicitly approved the current complete grouping.

## 3. Create interactive child sessions

Create one child session per approved group. Each child must be visible to and directly interactive with the user: the user can enter it, answer its questions, and let it continue. A background subagent does not satisfy this requirement. Name each child session exactly `spec: <feature-slug>`, using the approved group slug that will also identify its spec. In Codex Desktop, pass this as the `title`; on other platforms, use the equivalent session title.

For independent groups, create child sessions in parallel when the host supports it. For groups with a decision dependency, process the blocker first or make the dependent child wait for the blocker's relevant conclusion. Ticket-level implementation dependencies remain the responsibility of `/to-tickets`.

When multiple approved groups will change local repository files in the shared checkout, serialize their file-writing work. Do not switch branches while another group may write to that checkout. Issue-only groups can still run in parallel.

### Codex Desktop

Use the Codex project/thread creation capability. Identify the current project with `list_projects`, require a unique match, and create each child with the same project and a `local` environment. Use a new task window. Create a worktree only when the user explicitly requests one; otherwise use the shared checkout and follow the task-branch rules below. If the project cannot be identified uniquely, pause and ask the user to select or open it; never guess.

### CLI and other coding agents

Use the platform's equivalent visible child conversation or a new terminal session in the same working directory. If the platform cannot create one, provide a complete handoff prompt containing the approved group, repository path, dependency-reading rule, phase order, shared-workspace rules, and completion report format. State that the child session still needs to be started by the user. Do not claim that it was created.

Give each child only its approved group, global workflow rules, dependency information, repository/workspace context, and known group dependencies. Include the first-response requirement from Section 4. Keep unrelated sibling requirements and parent-history noise out of the child prompt.

For new or materially rewritten project text, use only the normative prose in the root `AGENTS.md` of the repository receiving that text. When source and target differ, do not use the source or installation `AGENTS.md` as a substitute; when they are the same repository, the shared root is the target rule. Include the target repository's rule in each child prompt and require the child to pass it to `/grill-duo-with-docs`, `/to-spec`, and `/to-tickets`. If the child will write to a different repository, it must read that repository's root rule before drafting. Pause if the target rule has no discernible dominant language, preserve untouched text, and report resulting language mixtures. Do not modify the external dependency skills.

Child-session creation is complete only when every approved group has a real interactive child-session identifier. If the platform cannot create one, provide the complete manual handoff described above and report the group as blocked; a manual handoff is not a ready child and cannot count toward successful handoff.

## 4. Child-session protocol

In every child session, re-read each current dependency file immediately before its phase. If a source is unavailable, follow the Dependencies recovery rule and pause only the phase that needs that source. The first response must briefly restate the group's outcome, scope, non-goals, and key workflow constraints. Only a group whose approved grouping explicitly includes the opt-in may invoke `/grill-duo-with-docs` to present the current answerable frontier and wait for the user's response. If the frontier is empty, use its shared-understanding summary and wait for confirmation. The child prompt alone does not establish readiness.

For a group with explicit opt-in, run `/grill-duo-with-docs` first, then `/to-spec` and `/to-tickets` in that order. Advance only after the current skill's confirmation gate passes, including `/to-spec`'s seam confirmation and `/to-tickets`' ticket-granularity, blocking-edge, and publication gates.

After `/to-tickets` publishes every planned ticket, the child session for that spec links those issues as native sub-issues of its spec; the parent does not create or retry these links. Approval of the planned ticket set authorizes these routine associations without a separate prompt and does not authorize issue creation or any other GitHub write. Keep this phase outside the `/to-tickets` run so its existing parent-issue boundary stays intact:

- Before any GitHub-specific read or write, confirm the configured tracker is GitHub; otherwise stop and report the blocker. If ticket publication is partial, retain created issues and defer all linking. On resume, reconcile the approved ticket list with all GitHub issues across open and closed states using a fully paginated query such as `gh api 'repos/<owner>/<repo>/issues?state=all&per_page=100' --paginate`; ignore results with a `pull_request` field. Reuse a recorded issue number, or a single exact title-and-body match; if the match is ambiguous, pause and ask. If issue creation returns an error, first reconcile the full issue listing: reuse exactly one match and pause if there are multiple matches. If there are zero matches and the outcome is unknown (such as a timeout or lost connection), pause and do not resubmit. If the response confirms no issue was created, retry only a clearly transient failure under the existing publication approval; report and stop on other errors. Pause if the listing cannot be read completely. Create only tickets confirmed missing under the existing publication approval. Carry forward the reported create-attempt count for each ticket from the `/to-tickets` publication report, including its initial attempt, and count it toward a maximum of three total attempts across the workflow. Before each recovery create, increment the count in the child task progress summary; if a missing ticket may have been attempted but its count cannot be recovered, or the limit is reached, pause instead of retrying automatically. Keep `ready-for-agent` on every ticket. Start linking only when all planned issues exist.
- After all issues exist and the existing seam, ticket-granularity, blocking-edge, and publication gates pass, confirm native sub-issues and required permissions are available; otherwise stop and report the blocker. Add each ticket with `gh issue edit <spec-issue-number> --add-sub-issue <ticket-issue-number>`. Before each write, read both `gh api repos/<owner>/<repo>/issues/<ticket-number>/parent` and `gh api repos/<owner>/<repo>/issues/<spec-number>/sub_issues --paginate`. Treat a ticket as already complete only when both reads show the same spec parent. Treat a 404 from the ticket `/parent` endpoint as no parent only after confirming the ticket exists and the spec `/sub_issues` read succeeds; the list must not contain that ticket. Any other read error leaves the relationship unknown.
- If a ticket has a different parent, or the two relationship reads disagree or cannot establish current state, pause this spec and ask the user; never reparent automatically. If native sub-issues or required permissions are unavailable, report the blocker and keep created issues and successful links. Do not use a textual or task-list fallback.
- After any failed or ambiguous relationship write, re-read both relationships before retrying. If the link now exists under the same spec, treat it as complete. Otherwise preserve successful links and retry only the missing link, only for a clearly transient failure, with at most three total write attempts per link. Record the cumulative write-attempt count for each link in the child task progress summary before each write, and update it before every retry. Carry the count forward on resume. If the prior summary is missing or incomplete, do not retry automatically. Re-read before every retry; stop on other errors or when the limit is reached, and report which links succeeded or remain pending.
- Preserve ticket and spec issue titles, bodies, labels, states, and blocking edges. Read these fields before linking, then verify them and every native parent relationship afterward. Re-read the spec `/sub_issues` list with `--paginate` and confirm it contains every planned ticket; leave the spec issue state unchanged.

Preserve each dependency's user-confirmation, seam, ticket-granularity, blocking-edge, and publication gates. The child must not answer user-facing questions on the user's behalf.

The child protocol is complete only when the three dependency processes have finished in order, or the child has reported a specific blocker and stopped.

## 5. Task branches and Git publication

Decide from the approved group whether it changes files inside this repository:

- For an issue-only group, do not create or switch branches, create worktrees, commit, or push. Keep issue creation, status changes, and sub-issue linking under their existing approval gates.
- For a group with local repository artifacts, use one dedicated task branch for that group. Reuse the current branch only when it is dedicated to the same group and clean; otherwise create a branch from the current clean `HEAD` before the first local file write. Follow repository and active agent framework naming conventions as guidance; do not require a fixed prefix.
- If the user explicitly requests a worktree, its branch must differ from its source branch. Configure the task remote (normally `origin`) and confirm the matching remote ref. The first normal push may create that ref; verify the exact ref after the push. Reconcile a divergent or uncertain remote state before continuing, and never force-push.
- Approval of the complete grouping grants the main agent standing authorization for routine, focused commits and normal pushes of that group's local artifacts, including its task branch, any explicitly requested worktree, and the initial push. This authorization ends when the assigned group is complete, does not carry to unrelated groups or later tasks, and resumes after interruption only after reconciling the approved group, worktree, branch, local commits, upstream, and exact remote state.
- This Git authorization does not cover issue creation, status changes, or sub-issue relationships. Preserve their existing approval gates, along with the seam, ticket-granularity, blocking-edge, and publication confirmations. This workflow does not open pull requests or merge branches.
- After the group's local artifacts pass their agreed checks, create one focused commit for them and push the confirmed commit to the exact task branch. Retry only a clearly transient push failure after reconciliation, with at most three total attempts for the same ref and commit. Block uncertain outcomes; never repeat a confirmed commit or push. Preserve local artifacts, commits, remote branches, and created issues after later failures; do not delete branches, roll back, amend, or rewrite history.

An issue-only group completes without any Git operation. A local-artifact group is not complete until its approved artifacts are committed and pushed and the group's existing issue-publication steps finish. Do not use a successful push as approval for any issue or status write.

## 6. Shared workspace and document writes

All child sessions use the current shared working directory. Keep spec-specific documents and ticket files uniquely named by feature slug. Follow existing repository conventions and the live dependency skills for document locations and tracker publication.

For shared glossary and decision documents, follow `/grill-duo-with-docs` for repository routing, latest-content checks, additive edits, and semantic-conflict handling. Serialize writes across child sessions. If conclusions conflict, show both and wait for the user's decision.

## 7. Child readiness, handoff, and resumption

Before a successful handoff, the parent tracks only child creation and readiness. For each group, it verifies:

- the first response and first actual grilling turn meet Section 4's contract, cover the group's essentials without substantive contradiction, and follow Section 4's required wait, including its no-decisions confirmation path;
- the child is a real interactive session the user can enter and continue.

A group is ready only when both checks pass. A prompt, returned session identifier, child status, or elapsed time alone is not readiness evidence. Keep each group's state distinct. Continue unaffected groups where possible and preserve already-created sessions.

Handle creation and startup outcomes as follows:

- A pending child with no first response remains pending. Ask the user whether to wait or authorize a retry; a timeout never changes it to ready.
- Report explicit creation or child errors and wait for the user's decision before retrying.
- Reconcile an ambiguous creation result against the known operation or child-session state before considering any retry. If the result remains uncertain, report the evidence and ask the user how to proceed. Never retry automatically or create a duplicate.

If not every group is ready, report each group's child link or missing-session state, readiness evidence, and concrete blocker. Do not claim successful handoff. Ask only for the action needed to resolve pending, failed, or uncertain states.

When every approved group is ready, give one handoff summary containing, for each group, the interactive child link, evidence for both readiness checks, known blockers, and artifacts available at that point (such as spec, document, or ticket links, or that none exist yet). Send it once. Then stop tracking or aggregating the children's later grilling, specs, tickets, shared documents, conflicts, or issue links. Each child reports its later results directly to the user.

On resumption, inspect existing child-session status and first-turn evidence, reuse known identifiers, and reconcile uncertain creation outcomes before acting. For local-artifact groups, also reconcile the checkout, task branch, local commits, upstream, and exact remote ref before resuming Git authorization.

Do not install skills, run setup, modify the dependency skills, implement application code, or open pull requests as part of this workflow. Apply task-scoped Git publication only to approved local repository artifacts; issue-only groups use no branch or push.
