# Child-session initial prompt template

## Fill instructions

Create one prompt for each explicitly approved group. Replace every bracketed placeholder with confirmed, group-specific information before using the template for handoff; do not leave unresolved placeholders. Use only confirmed information and do not invent missing facts. Exclude sibling requirements and unrelated parent history. Include only the global rules, dependencies, repository context, and write constraints that apply to this group. Do not include a full worked example.

For dependencies, name known blockers and their current state; say `None` only when the parent has confirmed there are none. For write constraints, carry forward the applicable shared-workspace and authorization rules without broadening them. For project text, include the normative language rule from the target repository's root `AGENTS.md`; if the target is another repository, the parent must read that repository's root file before drafting.

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

Preserve each phase's user-confirmation gates. For `/grill-duo-with-docs`, wait for confirmation before recording shared project-document changes. For `/to-spec`, preserve the seam-confirmation gate. For `/to-tickets`, preserve the ticket-granularity, blocking-edge, and publication gates. Advance only after the current phase's required gate passes.

### Native ticket linking

After all planned tickets exist and the existing seam, ticket-granularity, blocking-edge, and publication gates have passed, confirm the configured tracker is GitHub and that native sub-issues and the required permissions are available. Approval of the planned ticket set authorizes only these routine associations; it does not authorize issue creation or any other GitHub write. If GitHub, native sub-issues, or required permissions are unavailable, report the blocker and stop.

Before each link, confirm the ticket exists, read its current parent, and fully paginate the spec's sub-issues. Treat a link as already complete only when both reads confirm the same spec parent; skip that write. Treat a 404 from the parent endpoint as no parent only after the ticket exists and the spec's complete sub-issues read succeeds and the list does not contain the ticket; any other read error leaves the relationship unknown. Add only a missing link with `gh issue edit <spec-number> --add-sub-issue <ticket-number>`.

If the ticket has a different parent, the reads disagree, or the current state cannot be established, pause and ask the user; never reparent automatically. After a failed or ambiguous write, reread both relationships. If the intended parent is now confirmed, mark that link complete. Otherwise retry only the still-missing link after another successful read, and only for a clearly transient failure, with at most three total write attempts per link, including the first. Record the cumulative attempt count in the child progress summary before each write and update it before every retry; carry it across resume. If the prior count is missing or incomplete, stop instead of retrying automatically. Stop on other errors or when the limit is reached, and report links that succeeded or remain pending.

Preserve ticket and spec issue titles, bodies, labels, states, and blocker edges: before linking, record these fields; after linking, verify them. Then verify every link by rereading each ticket's native parent relationship and fully paginating the spec's sub-issues list to confirm all planned tickets appear. Leave the spec issue's state unchanged.

Use the target repository's root `AGENTS.md` language rule for new or materially rewritten project text, and pass that rule to `/grill-duo-with-docs`, `/to-spec`, `/to-tickets`, and `/conventional-git-messages` when used. If the target repository differs from the source repository, read its root `AGENTS.md` before drafting; do not substitute the source or skill-installation rule. Preserve untouched text and pause if the target rule has no discernible dominant language.

Before `/to-spec` or `/to-tickets` drafts a GitHub issue title or body, re-read the original `/conventional-git-messages` `SKILL.md` and invoke it with the known facts and target repository language rule. Follow the approved group's shared workspace and write-authorization rules; stop for user input whenever a required decision or authorization is missing.

## Boundaries and completion

Never answer user-facing questions on the user's behalf; present them and wait. The parent retains readiness, handoff, retry, and resumption responsibilities. This prompt or a child-session identifier alone does not establish readiness.

Your completion report must state your actual status, completed phases, produced artifacts or issue references, and remaining blockers or requested user action. Do not claim a phase, approval, or artifact is complete unless it is confirmed.
