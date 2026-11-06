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
| /spec-review | Skill | https://github.com/EltonZhang777/AggregateSkills |
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
- the default post-approval workflow: `/grill-duo-with-docs` and confirmed project-document updates, followed by `/to-spec`, `/spec-review`, and `/to-tickets`;
- local repository artifacts included in the approved output, if any;
- dependencies on other groups, if any.

For several requests, make one group per independently implementable, single-target behavior. Shared implementation details do not justify merging groups. A single request is one group, but still follows the approval gate.

Show the complete proposed grouping and wait for explicit approval of that complete grouping. Approval starts every approved group in the `/grill-duo-with-docs` and confirmed-content document-maintenance workflow; no per-group opt-in is required. If the user objects but the requested change is unclear, ask a direct clarification question, then present the revised grouping and wait again.

The grouping step is complete only when the user has explicitly approved the current complete grouping.

## 3. Create interactive child sessions

Create one child session per approved group. Each child must be visible to and directly interactive with the user: the user can enter it, answer its questions, and let it continue. A background subagent does not satisfy this requirement. Name each child session exactly `spec: <feature-slug>`, using the approved group slug that will also identify its spec. In Codex Desktop, pass this as the `title`; on other platforms, use the equivalent session title.

Use the [child-session initial prompt template](references/child-session-initial-prompt.md) as each child's initial prompt or manual handoff. Fill every placeholder with confirmed information before creating or delivering it.

For independent groups, create child sessions in parallel when the host supports it. For groups with a decision dependency, process the blocker first or make the dependent child wait for the blocker's relevant conclusion. Ticket-level implementation dependencies remain the responsibility of `/to-tickets`.

When multiple approved groups will change local repository files in the shared checkout, serialize their file-writing work. Do not switch branches while another group may write to that checkout. Issue-only groups can still run in parallel.

### Codex Desktop

Use the Codex project/thread creation capability. Identify the current project with `list_projects`, require a unique match, and create each child with the same project and a `local` environment. Use a new task window. Create a worktree only when the user explicitly requests one; otherwise use the shared checkout and follow the task-branch rules below. If the project cannot be identified uniquely, pause and ask the user to select or open it; never guess.

### CLI and other coding agents

Use the platform's equivalent visible child conversation or a new terminal session in the same working directory. If the platform cannot create one, provide a complete handoff prompt containing the approved group, repository path, dependency-reading rule, phase order, shared-workspace rules, and completion report format. State that the child session still needs to be started by the user. Do not claim that it was created.

Give each child only its approved group, global workflow rules, dependency information, repository/workspace context, and known group dependencies. Include the first-response requirement from Section 4. Keep unrelated sibling requirements and parent-history noise out of the child prompt.

For new or materially rewritten project text, use only the normative prose in the root `AGENTS.md` of the repository receiving that text. When source and target differ, do not use the source or installation `AGENTS.md` as a substitute; when they are the same repository, the shared root is the target rule. Include the target repository's rule in each child prompt and require the child to pass it to `/grill-duo-with-docs`, `/to-spec`, `/spec-review`, `/to-tickets`, and `/conventional-git-messages`. If the child will write to a different repository, it must read that repository's root rule before drafting. Pause if the target rule has no discernible dominant language, preserve untouched text, and report resulting language mixtures. Do not modify the external dependency skills.

Child-session creation is complete only when every approved group has a real interactive child-session identifier. If the platform cannot create one, provide the complete manual handoff described above and report the group as blocked; a manual handoff is not a ready child and cannot count toward successful handoff.

## 4. Child-session protocol

In every child session, re-read the source file needed by each phase immediately before it. If a source file needed by one phase is unavailable, report the phase and blocking source, pause only that phase, and allow independent eligible phases to continue. Re-read the source file before resuming that phase. Missing global prerequisites in the Dependencies section still stop the entire workflow; do not install dependencies automatically. The first response must briefly restate the group's outcome, scope, non-goals, and key workflow constraints. For every approved group, invoke `/grill-duo-with-docs` to present the current answerable frontier and wait for the user's response. If the frontier is empty, use its shared-understanding summary and wait for confirmation. The complete-grouping approval includes this workflow; no further opt-in is required. The child prompt alone does not establish readiness.

For every approved group, run `/grill-duo-with-docs` first, then complete `/to-spec` seam confirmation and draft staging, `/spec-review`, successful spec Issue publication, and only then the `/to-tickets` workflow. Advance only after the current phase's confirmation gate passes. Preserve `/to-tickets` ticket-granularity, blocking-edge, and publication gates.

Read each live dependency immediately before using it. If `/to-spec` can reliably stop before creating or publishing an Issue, use it for seam confirmation and drafting, then stop before its publication step. If it cannot reliably stop, use its seam-confirmation criteria and draft template without invoking its publishing step. After seam confirmation, show the exact draft text and a unique temporary path; obtain explicit approval of that text and authorization for that path. Stage it with create-new semantics, read back the staged bytes, and freeze their exact UTF-8 representation and SHA-256. This staging approval authorizes only that staging operation.

Run `/spec-review` on the staged bytes before any Issue publication. Follow its frozen-input, evidence, finding, candidate, and invocation rules. A candidate is applied only after approval of the exact batch, source version, and unique destination plus explicit write authorization; after approved edits, run fresh review in the same named cycle. A cycle has at most three numbered rounds, including its initial round. At the limit, unresolved issues require a handoff asking whether the user authorizes another named cycle or wants another action. Review pass, candidate approval, and staging approval do not approve the final spec or authorize publication.

Before publication, present the exact Issue title and body, canonical target owner/repository, required label set, and SHA-256 of the exact UTF-8 body bytes. The Issue body must be byte-identical to the frozen draft that passed `/spec-review`. Obtain final specification approval and publication authorization as separate user decisions; bind both to the exact tuple of title, draft SHA-256, canonical owner/repository, and required labels. Publish only after both approval records are present and still match that tuple. Any body-byte change requires a fresh review round and new approvals. Any title, target, or required-label change invalidates both approvals and requires a new exact preview and both approvals. Do not treat a review pass as final approval.

Immediately before `/to-spec` or `/to-tickets` drafts an Issue title or body, invoke `/conventional-git-messages` with the known facts and target repository's root `AGENTS.md` language rule. Apply its title and concise, factual prose guidance where compatible with each required format. Preserve `/to-spec`'s required body headings and order and `/to-tickets`' required body structure and short, descriptive titles; use Conventional syntax or prefixes for `/to-tickets` titles only when compatible with that constraint.

### Exclusive GitHub writer claim and publication recovery

Before every GitHub Issue create/edit, repository-label create, Issue-label change, or ticket-link write, obtain and verify an atomic exclusive writer claim. Key the claim by the canonical owner/repository and the exact approved spec-publication tuple, exact ticket payload, or exact ticket relationship graph and link delta, as applicable. Record the claim owner's host/session ID, unique operation ID, key, and operation/attempt state in the task progress summary before the external write. The summary is a record, not a substitute for an atomic claim. If the host cannot verify the exclusive claim, stop before writing.

No second session may write while a claim or any operation for that key is active or unresolved. Release a claim only after terminal read-back reconciliation. Permit takeover only after the prior owner has stopped and every operation it owns has been reconciled. Do not start a second create while an earlier create may have succeeded.

Keep at most one unresolved Issue-create operation per canonical target and approved tuple. For each spec or ticket Issue create, register a unique operation ID and cumulative attempt state before the request, and verify the canonical target immediately before writing. Read the created Issue back and verify its type, canonical target, exact title, and exact body bytes against the approved payload. On an ambiguous outcome, fully paginate Issues across all states, exclude pull requests, and read back the exact candidate; accept only one unique Issue whose target, title, and body bytes match. Incomplete enumeration, multiple matches, mismatches, or an unknown outcome stop the operation without retry. Retry only a confirmed transient failure after a complete listing proves no Issue was created, with at most three total attempts across resumes. Record the increment before each attempt.

After Issue read-back, create and verify required repository labels as needed, then apply the required labels to the Issue with `ready-for-agent` last. Before each label write, verify the Issue still belongs to the canonical target. Track a unique operation ID and cumulative attempt state for each label operation before writing. Reconcile ambiguous label results by reading the label and Issue back; retry only a confirmed transient failure when the label is still missing, up to three total attempts for that label across resumes. Spec publication is successful only after the exact Issue and all required labels are verified by read-back. Keep the writer claim until terminal read-back reconciliation.

### Ticket reconciliation and native links

After the spec Issue and all required labels are verified, obtain the user's explicit authorization for ticket reconciliation. Do not invoke `/to-tickets` until review coverage passed, both exact final approvals were recorded, and spec publication succeeded. Re-read the live `/to-tickets` instructions and prove that the workflow can return its ticket plan and reliably stop before any Issue create, edit, label, or link write. If it can, invoke it only to prepare the exact plan and stop before its first Issue write. If it cannot, do not invoke its publishing step; use its existing ticket-granularity, blocking-edge criteria, and template to prepare and freeze the same proposal in task progress without publishing. Present each proposed title, body, canonical target, required labels, and exact blocking edges before seeking approval.

Reconcile existing spec-review tickets by exact known Issue IDs. Read each title, body, state, labels, parent, and blocking edges. Present the set as unchanged, revised, superseded, or new, with exact proposed field and edge changes. Do not duplicate an existing ticket, infer a closure, or change a field or relationship from a title match. Obtain exact ticket-set approval, then separately obtain explicit Issue-creation authorization; bind both records to the parent spec Issue ID, its exact approved body SHA-256, canonical owner/repository target, and exact ticket payload plus graph. On the safe `/to-tickets` path, its publication confirmation serves as the separate Issue-creation authorization and must bind to that same tuple; in the template fallback, obtain this explicit authorization directly. Before any native link write, present the exact proposed edges and canonical target, then obtain separate explicit link authorization, distinct from both ticket-set approval and Issue-creation authorization. Bind it to the parent spec Issue ID, exact approved body SHA-256, canonical target, and exact graph. Issue-creation authorization never permits links; if only it exists, do not link. Obtain separate approval for each later ticket-payload or graph/link delta, bound to the same parent Issue ID, body hash, and canonical target plus its exact delta. Ticket-set approval alone authorizes no write: create only after the separate Issue-creation authorization, update only after exact payload-delta approval, and link only after exact graph/link approval and link authorization. Each write also requires its own writer claim and applicable publication or relationship gate, then read-back reconciliation.

Create only tickets confirmed missing by exact-ID reconciliation and covered by the exact ticket-set approval and separate Issue-creation authorization described above. Before each create, verify the target, register the operation and attempt state, and follow the create recovery rules above. Preserve successful writes after later failures. Keep `ready-for-agent` on every ticket, applying it last after the other required labels have been created and verified.

Before every ticket create, edit, label change, or link write, re-read the parent spec Issue using its exact approved Issue ID. Verify the returned ID, approved title, canonical owner/repository, exact approved body bytes and their SHA-256, that every approved required label is present, and that the current required-label tuple matches the approved tuple. If any differs, stop and invalidate both final spec approvals, publication authorization, the ticket-set approval, the separate Issue-creation authorization, every affected ticket-payload or graph/link-delta approval, and any independent link-write authorization before any ticket write continues. If the exact body bytes are not byte-identical or the SHA-256 differs, freeze the newly read body and run a fresh `/spec-review` round. Require that round to pass before re-previewing or requesting, binding, or recording any replacement approval or write authorization; no replacement approval or write authorization may exist before that pass. Only after the new review passes, re-preview the exact publication tuple, affected ticket proposal, and exact edges plus canonical target; obtain fresh applicable final spec approvals, publication authorization, ticket-set approval, separate Issue-creation authorization, affected ticket-payload or graph/link-delta approvals, and explicit link authorization bound to the parent Issue ID, body hash, canonical target, and exact graph as applicable. If body bytes and SHA-256 remain identical but only the parent Issue ID, title, canonical owner/repository, or required-label presence/tuple differs, re-preview the exact affected publication tuple and ticket proposals/edges. Re-obtain every invalidated applicable approval and authorization: final specification approval, publication authorization, ticket-set approval, separate Issue-creation authorization, affected ticket-payload or graph/link-delta approval, and any applicable independent write authorization, including explicit link-write authorization for affected graph changes; bind each to the updated parent tuple and exact payload/graph delta. Restore or reconfirm successful publication against that tuple, with all required labels verified by read-back, before resuming ticket writes. Metadata-only drift does not require or imply a new `/spec-review` round solely because of that drift. No ticket write may proceed until applicable approvals are fresh and successful publication is reconfirmed. Immediately before each write, verify the repository of every involved Issue. For each existing-ticket field or edge change, issue one field or edge write at a time. Record a unique operation ID and cumulative attempt state for that individual write before calling the API. Read the ticket immediately before writing and compare its exact current state with the approved baseline or last verified state and the exact expected pre-write state. Drift stops the write until the new exact delta is approved. Read every involved Issue back immediately after each write, verify its repository and exact expected change, and reconcile it before advancing. For an ambiguous response, read back and reconcile before any retry; retry only when a clearly transient failure is confirmed and read-back proves that exact operation is missing, with at most three attempts per write across resumes. Missing or conflicting operation history stops the workflow without retry.

Start native sub-issue linking only after every planned ticket exists, the exact graph/link delta and separate link authorization are approved, and the seam, ticket-granularity, blocking-edge, and publication gates pass. Confirm GitHub, native sub-issues, and required permissions are available; otherwise stop and report the blocker. Before each link, read both `gh api repos/<owner>/<repo>/issues/<ticket-number>/parent` and `gh api repos/<owner>/<repo>/issues/<spec-number>/sub_issues --paginate`. Treat a ticket as complete only when both reads confirm the same spec parent. A 404 from the parent endpoint means no parent only after confirming the ticket exists, the complete spec sub-issues read succeeds, and the list omits the ticket. Any other read error leaves the relationship unknown.

If a ticket has a different parent or the reads disagree or cannot establish state, pause and ask; never reparent automatically. Before each missing-link write, record its unique operation ID and attempt state and obtain the writer claim for the approved graph. After a failed or ambiguous write, re-read both relationships before retrying. Retry only a still-missing link after another successful read and a confirmed transient failure, with at most three total attempts per link. Record cumulative counts before every write and carry them across resumes. If a prior count is missing or incomplete, stop. Preserve successful links and report links that succeeded or remain pending. Verify ticket and spec titles, bodies, labels, states, blocking edges, every parent relation, and the fully paginated spec sub-issues list afterward; leave the spec Issue state unchanged.

Preserve every dependency's user-confirmation, seam, ticket-granularity, blocking-edge, publication, and exact-write gates. The child must not answer user-facing questions on the user's behalf.

The child protocol is complete only when all required dependency processes have finished in order, or the child has reported a specific blocker and stopped.

## 5. Task branches and Git publication

Decide from the approved group whether it changes files inside this repository:

- For an issue-only group, do not create or switch branches, create worktrees, commit, or push. Keep issue creation, status changes, and sub-issue linking under their existing approval gates.
- For a group with local repository artifacts, use one dedicated task branch for that group. Reuse the current branch only when it is dedicated to the same group and clean; otherwise create a branch from the current clean `HEAD` before the first local file write. Follow repository and active agent framework naming conventions as guidance; do not require a fixed prefix.
- If the user explicitly requests a worktree, its branch must differ from its source branch. Configure the task remote (normally `origin`) and confirm the matching remote ref. The first normal push may create that ref; verify the exact ref after the push. Reconcile a divergent or uncertain remote state before continuing, and never force-push.
- Approval of the complete grouping grants the main agent standing authorization for routine, focused local commits and ordinary non-force pushes of those commits to that group's dedicated task branch, including the initial push that creates the matching remote ref. This authorization is limited to the approved group and its task branch, ends when the assigned group is complete, does not carry to unrelated groups or later tasks, and resumes after interruption only after reconciling the approved group, worktree, branch, and local commits.
- Force-pushes, remote-ref deletion, pushes to other branches, pull request actions, issue creation, status changes, sub-issue linking, and other GitHub writes retain separate approval. Preserve the existing issue, status, and sub-issue approval gates, along with the seam, ticket-granularity, blocking-edge, and publication confirmations. This workflow does not open pull requests or merge branches.
- After the group's local artifacts pass their agreed checks, immediately before committing invoke `/conventional-git-messages` in commit mode with the change facts, applicable repository commit guidance, and known issue references; use its result for one focused commit, then push the confirmed commit to the exact task branch. Retry only a clearly transient push failure after reconciliation, with at most three total attempts for the same ref and commit. Block uncertain outcomes; never repeat a confirmed commit or push. Preserve local artifacts, commits, remote branches, and created issues after later failures; do not delete branches, roll back, amend, or rewrite history.

An issue-only group completes without any Git operation. A local-artifact group is not complete until its approved artifacts are committed and pushed and the group's existing issue-publication steps finish. Do not use a successful push as approval for any issue or status write.

### Optional document integration follow-up

After a local-artifact group has completed its task-branch publication and its issue/status checkpoints, offer a separate integration only for the group's approved generated document set; do not include the workflow's own skill, tests, manuals, or other implementation files. Before asking, provide a summary that names the task branch, exact document paths, and proposed destination branch, and state that accepting will create one focused local commit containing only those documents on the destination branch. Use a destination only when user-confirmed context or repository guidance identifies it unambiguously; otherwise ask the user to name the branch and pause without integrating.

Ask whether to start the integration. An affirmative response authorizes only that focused local commit of the listed documents on the named destination branch; it does not extend the task-branch grant in ADR-0003. Continue with the same host agent in the same conversation; do not create a new conversation or subagent.

Before changing the destination, confirm it has no unrelated changes and check for conflicts. Stop if the destination is unclear, unrelated changes are present, or conflicts occur; do not overwrite destination work or include unrelated changes. Declining or giving no clear authorization leaves the documents on the task branch and the destination unchanged.

The integration authorization does not authorize pushing the destination branch; pushing it still requires the separate explicit confirmation from the existing grilling step. Issue-only behavior and application-code branch policy remain unchanged.

## 6. Shared workspace and document writes

All child sessions use the current shared working directory. Keep spec-specific documents and ticket files uniquely named by feature slug. Follow existing repository conventions and the live dependency skills for document locations and tracker publication.

Record only user-confirmed content in project documents. For shared glossary and decision documents, follow `/grill-duo-with-docs` for repository routing, latest-content checks, additive edits, and semantic-conflict handling. Serialize writes across child sessions. If conclusions conflict, show both and wait for the user's decision.

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
