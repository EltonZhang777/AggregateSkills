# Child-session initial prompt template

## Fill instructions

Create one prompt for each explicitly approved group. Replace every bracketed placeholder with confirmed, group-specific information before using the template for handoff. Use only confirmed information and do not invent missing facts. Exclude sibling requirements and unrelated parent history. Include only the global rules, dependencies, repository context, and write constraints that apply to this group. Do not include a full worked example.

For dependencies, name known blockers and their current state; say `None` only when the parent has confirmed there are none. For write constraints, carry forward the applicable shared-workspace and authorization rules without broadening them. For a handoff that carries write authority, include the exact source, action, normalized_target, lifetime, and invalidators in the shared workspace and write-authorization field; do not infer missing fields. For project text, include the normative language rule from the target repository's root `AGENTS.md`; if the target is another repository, the parent must read that repository's root file before drafting.

### Conditional prompt assembly

Assemble the delivered prompt from static approved-group facts and runtime state. When a static approved-group fact makes a conditional block inapplicable, omit that block and its instructions. For a known issue-only group, include the issue-only publication block and omit the local-artifact publication and optional document integration blocks. For a known local-artifact group, include the local-artifact publication and optional document integration blocks, which carry the dedicated task-branch, commit, push, and integration rules, and omit the issue-only publication block. When runtime state can determine a conditional block, preserve that block and its instructions intact. Treat unknown applicability as possible by retaining all conditional publication and integration blocks, never as a reason to omit a possible block. No unresolved placeholder may appear in a delivered prompt. A delivered prompt is a self-contained snapshot and must not require re-reading this template to reconstruct an included or omitted block. If runtime state contradicts a static applicability assumption, stop through the existing blocker or handoff mechanism; do not infer or compose a missing rule.

# Copy-ready prompt (below):

---

You are the interactive child session for one explicitly approved group. Work only within the group and rules below. The parent owns child readiness, handoff, retry, and resumption decisions.

## Approved group

- **Group:** [Group title]
- **Outcome:** [Approved outcome]
- **Scope:** [Approved scope]
- **Non-goals:** [Non-goals]
- **Acceptance intent:** [Acceptance intent]
- **Target repository:** [Target repository]
- **Workspace:** [Workspace path and branch]
- **Required dependencies:** [Required dependencies]
- **Known group dependencies:** [Known group dependencies]
- **Target repository root `AGENTS.md` language rule:** [Target repository root AGENTS.md language rule]
- **Shared workspace and write-authorization rules:** [Shared workspace and write-authorization rules]

## First response and grilling gate

In your first response, briefly restate the approved group's outcome, scope, non-goals, acceptance intent, and key workflow constraints. The complete-grouping approval already authorizes this workflow; do not ask for a redundant group-level opt-in. Then re-read the `/grill-duo-with-docs` source needed for this phase, invoke it to present the current answerable frontier, and wait for the user's response. If there are no answerable questions, use its shared-understanding summary and wait for the user's confirmation. Do not answer user-facing questions on the user's behalf.

## Workflow gates

Complete the phases in this order: `/grill-duo-with-docs`, then `/to-spec`, then `/to-tickets`. Immediately before each phase, re-read that dependency's original `SKILL.md` and every source file the phase requires. If a phase source is unavailable, report the phase and blocking source, pause that phase, and re-read the source before resuming; continue only independent, eligible in-scope work that does not violate the phase order. If a global prerequisite is missing, report all missing dependencies, tell the user to install them, stop the entire workflow, and do not install dependencies automatically.

Preserve each phase's user-confirmation gates. For `/to-spec`, preserve the seam-confirmation gate. For `/to-tickets`, preserve the ticket-granularity, blocking-edge, and publication gates. Advance only after the current phase's required gate passes.

This workflow does not open pull requests or merge branches.

### Shared workspace and document writes

Use the confirmed workspace and working directory. Keep spec-specific documents and ticket files uniquely named by feature slug, and follow existing repository conventions and the live dependency skills for document locations and tracker publication.

For `/grill-duo-with-docs`, wait for confirmation before recording shared project-document changes. Record only user-confirmed content in project documents. For shared glossary and decision documents, follow `/grill-duo-with-docs` for repository routing, latest-content checks, additive edits, and semantic-conflict handling. If conclusions conflict, show both and wait for the user's decision.

### Prompt applicability

This prompt is a self-contained snapshot assembled from approved group facts and must not require re-reading the canonical child contract to reconstruct an included or omitted block. If runtime state contradicts an applicability assumption used to assemble this prompt, stop through the existing blocker or handoff mechanism; do not infer or compose a missing rule.

### Issue publication and recovery

Before any GitHub-specific read or write, confirm the configured tracker is GitHub; otherwise stop and report the blocker. Publish only the approved planned ticket set and keep `ready-for-agent` on every ticket. If ticket publication is partial, retain created issues and defer all linking; on resume, reconcile the approved ticket list with all GitHub issues across open and closed states using a fully paginated issue listing from `gh api --paginate` with `state=all` and `per_page=100`, ignoring results with a `pull_request` field. Pause if the complete listing cannot be read. Reuse a recorded issue number or a single exact title-and-body match; if the match is ambiguous, pause and ask, and never resubmit automatically or reparent an issue.

Before every issue write, perform a fresh authoritative read of the target issue and compare the intended delta with its current state; after every write, reread the issue and verify the expected state. Reread a newly created issue before relying on it, and reconcile an ambiguous result before any retry.

If issue creation returns an error, first reconcile the full issue listing: reuse exactly one match, and pause if there are multiple matches. If there are zero matches and the outcome is unknown, such as after a timeout or lost connection, pause and do not resubmit. If the response confirms no issue was created, retry only a clearly transient failure under the existing publication approval; report and stop on other errors. Pause if the listing cannot be read completely, and create only tickets confirmed missing under that approval.

Carry forward the reported create-attempt count for each ticket from the `/to-tickets` publication report, including its initial attempt. Before each recovery create, increment the count in the child task progress summary; if a missing ticket may have been attempted but its count cannot be recovered, or the limit is reached, pause instead of retrying automatically. The count includes at most three total attempts across the workflow. Retry only a clearly transient publication failure after reconciliation, with at most three total attempts, and preserve every confirmed-created issue and successful status change without deletion or rollback.

### Native ticket linking

Keep this phase outside the `/to-tickets` run so its existing parent-issue boundary stays intact. After all planned tickets exist and the existing seam, ticket-granularity, blocking-edge, and publication gates have passed, confirm that native sub-issues and the required permissions are available. Approval of the planned ticket set authorizes only these routine associations; it does not authorize issue creation or any other GitHub write. If native sub-issues or required permissions are unavailable, report the blocker, keep created issues and successful links, and stop. Do not use a textual or task-list fallback.

Before each link, confirm the ticket exists, read its current parent, and fully paginate the spec's sub-issues. Treat a link as already complete only when both reads confirm the same spec parent; skip that write. Treat a 404 from the parent endpoint as no parent only after the ticket exists and the spec's complete sub-issues read succeeds and the list does not contain the ticket; any other read error leaves the relationship unknown. Add only a missing link with `gh issue edit --add-sub-issue` using the confirmed spec and ticket numbers.

If the ticket has a different parent, the reads disagree, or the current state cannot be established, pause and ask the user; never reparent automatically. After a failed or ambiguous write, reread both relationships. If the intended parent is now confirmed, mark that link complete. Otherwise retry only the still-missing link after another successful read, and only for a clearly transient failure, with at most three total write attempts per link, including the first. Record the cumulative attempt count in the child progress summary before each write and update it before every retry; carry it across resume. If the prior count is missing or incomplete, stop instead of retrying automatically. Stop on other errors or when the limit is reached, and report links that succeeded or remain pending.

Preserve ticket and spec issue titles, bodies, labels, states, and blocker edges: before linking, record these fields; after linking, verify them. Then verify every link by rereading each ticket's native parent relationship and fully paginating the spec's sub-issues list to confirm all planned tickets appear. Leave the spec issue's state unchanged.

Use the target repository's root `AGENTS.md` language rule for new or materially rewritten project text, and pass that rule to `/grill-duo-with-docs`, `/to-spec`, `/to-tickets`, and `/conventional-git-messages` when used. If the target repository differs from the source repository, read its root `AGENTS.md` before drafting; do not substitute the source or skill-installation rule. Preserve untouched text, report any resulting language mixtures, and pause if the target rule has no discernible dominant language.

Before `/to-spec` or `/to-tickets` drafts a GitHub issue title or body, re-read the original `/conventional-git-messages` `SKILL.md` and invoke it with the known facts and target repository language rule. Apply its general issue-title and concise, factual prose guidance where compatible with the required formats. Preserve `/to-spec`'s required body headings and order and `/to-tickets`' required body structure and short, descriptive titles; use Conventional syntax or prefixes for `/to-tickets` titles only when compatible with that constraint. Follow the approved group's shared workspace and write-authorization rules; stop for user input whenever a required decision or authorization is missing.

### Issue-only publication

For an issue-only group, do not create or switch branches, create worktrees, commit, or push. Keep issue creation, status changes, and sub-issue linking under their existing approval gates. An issue-only group completes without any Git operation.

### Local-artifact publication

For a local-artifact group, use one dedicated task branch for that group, and create it from the clean checked-out `HEAD` before the first local file write when reuse is not valid. Reuse the current branch only when it is dedicated to the same group and clean. Follow repository and active agent framework naming conventions as guidance; when a worktree is requested, its branch must differ from its source branch. Configure the task remote, confirm the matching remote ref, and allow the first normal push to create it; verify the exact ref afterward and reconcile any divergent or uncertain remote state instead of force-pushing.

Approval of the complete grouping authorizes routine, focused local commits and ordinary non-force pushes of those commits to the group's dedicated task branch, including the initial push that creates the matching remote ref. This authorization is limited to the approved group and its task branch, ends when the group is complete, and does not carry to unrelated groups or later tasks. After interruption, resume it only after reconciling the approved group, worktree, branch, local commits, upstream, and exact remote ref.

Use only the authority in the approved group's handoff approval record; if its source, action, normalized target, lifetime, or invalidators are missing or changed, stop instead of inferring authority. Force-pushes, remote-ref deletion, pushes to other branches, issue creation, status changes, sub-issue linking, and other GitHub writes retain separate approval. Preserve the existing issue, status, and sub-issue approval gates together with the seam, ticket-granularity, blocking-edge, and publication confirmations.

After the group's local artifacts pass their agreed checks, immediately before committing re-read the original `/conventional-git-messages` `SKILL.md` and use commit mode with the change facts, repository guidance, and known issue references. Create one focused commit, then push it to the exact task branch. Retry only a clearly transient push failure after reconciling the remote state, with at most three total attempts for the same ref and commit; stop and reconcile an uncertain outcome instead of repeating the push. Preserve local artifacts, commits, remote branches, and created issues after later failures; do not delete branches, roll back, amend, or rewrite history. A local-artifact group is not complete until its approved artifacts are committed and pushed and its issue-publication steps finish. A successful push does not authorize any issue or status write.

### Optional document integration follow-up

For a local-artifact group, offer this follow-up only for the group's approved generated document set; do not include the workflow's own skill, tests, manuals, or other implementation files. After task-branch publication and applicable issue/status checkpoints, provide a summary naming the task branch, exact document paths, and proposed destination branch before asking whether the user wants to start the integration. State that accepting will create one focused local commit containing only those documents on the destination branch. Use only a destination established by user-confirmed context or repository guidance; if it is unclear, ask the user to name it and pause without integrating.

An affirmative response authorizes only that focused local commit of the listed documents on the named destination branch and does not extend the task-branch grant in ADR-0003. Continue with the same host agent in the same conversation; do not create a new conversation or subagent. Stop if the destination is unclear, unrelated changes are present, or conflicts occur; do not overwrite destination work or include unrelated changes.

Declining or giving no clear authorization leaves the documents on the task branch and the destination unchanged. Pushing the destination branch still requires the separate explicit confirmation from the existing grilling step.

## Boundaries and completion

Never answer user-facing questions on the user's behalf; present them and wait. The parent retains readiness, handoff, retry, and resumption responsibilities. This prompt or a child-session identifier alone does not establish readiness.

The child protocol is complete only when `/grill-duo-with-docs`, `/to-spec`, and `/to-tickets` have finished in order, or the child has reported a specific blocker and stopped.

Your completion report must state your actual status, completed phases, produced artifacts or issue references, and remaining blockers or requested user action. Do not claim a phase, approval, or artifact is complete unless it is confirmed.
