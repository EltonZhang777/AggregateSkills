---
name: requirements-to-spec-tickets
description: Turn one or more codebase ideas into approved, independently scoped specs and tracer-bullet tickets through interactive child sessions.
disable-model-invocation: true
metadata:
  prerequisites: '{"skills":[["grill-with-docs","mattpocock/skills"],["to-spec","mattpocock/skills"],["to-tickets","mattpocock/skills"],["grilling","mattpocock/skills"],["domain-modeling","mattpocock/skills"],["setup-matt-pocock-skills","mattpocock/skills"]],"mcps":[],"tools":[]}'
---

# Requirements to specs and tickets

Use this skill only when the user wants to turn one or more codebase ideas into clarified specs and tickets. This workflow produces requirements documentation; it does not implement code.

## 1. Preflight

Resolve and read the current `SKILL.md` for each required dependency from the active skill roots:

- `grill-with-docs`
- `to-spec`
- `to-tickets`

Read the files at runtime. Treat them as the source of truth, not as text to copy into this skill. If a dependency is missing or unreadable, stop and tell the user that it can be installed from [mattpocock/skills](https://github.com/mattpocock/skills/). Do not install it automatically.

When a dependency points to another skill, resolve and read that skill's current `SKILL.md` at the point of use; apply the same missing-file stop rule. Do not replace a referenced skill with a copied summary.

After the dependency check, verify that `setup-matt-pocock-skills` has supplied the issue tracker and triage-label configuration required by `to-spec` and `to-tickets`. If the setup or tracker configuration is absent, stop and tell the user to run `/setup-mattpocock-skills`. Do not create child sessions.

Preflight is complete only when all three dependency files are readable and the tracker configuration is available.

## 2. Turn the request into groups

Read the user's current conversation as the source of the requirements. For each request, propose a group with:

- a short title and feature slug;
- one independent user outcome;
- scope and non-goals;
- acceptance intent;
- dependencies on other groups, if any.

For several requests, make one group per independently implementable, single-target behavior. Shared implementation details do not justify merging groups. A single request is one group, but still follows the approval gate.

Show the complete proposed grouping and wait for an explicit approval such as "Approve grouping" before creating any child session. A tentative response is not approval. If the user objects but the requested change is unclear, read and follow the current `grill-with-docs/SKILL.md` in this parent session, then present a revised complete grouping and wait again.

The grouping step is complete only when the user has explicitly approved the current complete grouping.

## 3. Create interactive child sessions

Create one child session per approved group. Each child must be visible to and directly interactive with the user: the user can enter it, answer its questions, and let it continue. A background subagent does not satisfy this requirement. Name each child session exactly `spec: <feature-slug>`, using the approved group slug that will also identify its spec. In Codex Desktop, pass this as the `title`; on other platforms, use the equivalent session title.

For independent groups, create child sessions in parallel when the host supports it. For groups with a decision dependency, process the blocker first or make the dependent child wait for the blocker's relevant conclusion. Ticket-level implementation dependencies remain the responsibility of `to-tickets`.

### Codex Desktop

Use the Codex project/thread creation capability. Identify the current project with `list_projects`, require a unique match, and create each child with the same project and a `local` environment. Use a new task window and do not create a worktree. If the project cannot be identified uniquely, pause and ask the user to select or open it; never guess.

### CLI and other coding agents

Use the platform's equivalent visible child conversation or a new terminal session in the same working directory. If the platform cannot create one, provide a complete handoff prompt containing the approved group, repository path, dependency-reading rule, phase order, shared-workspace rules, and completion report format. State that the child session still needs to be started by the user. Do not claim that it was created.

Give each child only its approved group, global workflow rules, dependency information, repository/workspace context, and known group dependencies. Keep unrelated sibling requirements and parent-history noise out of the child prompt.

Child-session creation is complete only when every approved group has either a real interactive child-session identifier or an explicit manual handoff with a reported reason.

## 4. Child-session protocol

In every child session, re-read the current dependency files immediately before proceeding:

1. Read and follow `grill-with-docs/SKILL.md`.
2. After that phase reaches its own shared-understanding gate, read and follow `to-spec/SKILL.md`.
3. After the spec and its required seam confirmation are complete, read and follow `to-tickets/SKILL.md`.

After `to-tickets` finishes, this orchestrator links the published GitHub ticket issues as native sub-issues of their spec issue. Keep this phase outside the `to-tickets` run so its existing parent-issue boundary stays intact:

- Before any GitHub-specific read or write, confirm the configured tracker is GitHub; otherwise stop and report the blocker. If ticket publication is partial, retain created issues and defer all linking. On resume, reconcile the approved ticket list with all GitHub issues across open and closed states using a fully paginated query such as `gh api 'repos/<owner>/<repo>/issues?state=all&per_page=100' --paginate`; ignore results with a `pull_request` field. Reuse a recorded issue number, or a single exact title-and-body match; if the match is ambiguous, pause and ask. If issue creation returns an error, first reconcile the full issue listing: reuse exactly one match and pause if there are multiple matches. If there are zero matches and the outcome is unknown (such as a timeout or lost connection), pause and do not resubmit. If the response confirms no issue was created, retry only a clearly transient failure under the existing publication approval; report and stop on other errors. Pause if the listing cannot be read completely. Create only tickets confirmed missing under the existing publication approval. Carry forward the reported create-attempt count for each ticket from the to-tickets publication report, including its initial attempt, and count it toward a maximum of three total attempts across the workflow. Before each recovery create, increment the count in the parent task progress summary; if a missing ticket may have been attempted but its count cannot be recovered, or the limit is reached, pause instead of retrying automatically. Keep `ready-for-agent` on every ticket. Start linking only when all planned issues exist.
- After all issues exist and the existing seam, ticket-granularity, blocking-edge, and publication gates pass, confirm native sub-issues and required permissions are available; otherwise stop and report the blocker. Add each ticket with `gh issue edit <spec-issue-number> --add-sub-issue <ticket-issue-number>`. Before each write, read both `gh api repos/<owner>/<repo>/issues/<ticket-number>/parent` and `gh api repos/<owner>/<repo>/issues/<spec-number>/sub_issues --paginate`. Treat a ticket as already complete only when both reads show the same spec parent. Treat a 404 from the ticket `/parent` endpoint as no parent only after confirming the ticket exists and the spec `/sub_issues` read succeeds; the list must not contain that ticket. Any other read error leaves the relationship unknown.
- If a ticket has a different parent, or the two relationship reads disagree or cannot establish current state, pause this spec and ask the user; never reparent automatically. If native sub-issues or required permissions are unavailable, report the blocker and keep created issues and successful links. Do not use a textual or task-list fallback.
- After any failed or ambiguous relationship write, re-read both relationships before retrying. If the link now exists under the same spec, treat it as complete. Otherwise preserve successful links and retry only the missing link, only for a clearly transient failure, with at most three total write attempts per link. Record the cumulative write-attempt count for each link in the parent task progress summary before each write, and update it before every retry. Carry the count forward on resume. If the prior summary is missing or incomplete, do not retry automatically. Re-read before every retry; stop on other errors or when the limit is reached, and report which links succeeded or remain pending.
- Preserve ticket and spec issue titles, bodies, labels, states, and blocking edges. Read these fields before linking, then verify them and every native parent relationship afterward. Re-read the spec `/sub_issues` list with `--paginate` and confirm it contains every planned ticket; leave the spec issue state unchanged.

Reading the live files is the dependency mechanism for this workflow. It keeps the child aligned with dependency updates without modifying or duplicating those skills. If a required file becomes unavailable, stop that child and report the missing dependency.

The child must preserve the dependencies' own confirmation gates. In particular, it must let the user clarify the requirement, confirm proposed seams, approve ticket granularity and blocking edges, and approve publication wherever the dependency requires it. The child must not answer user-facing clarification questions on the user's behalf.

The child protocol is complete only when the three dependency processes have finished in order, or the child has reported a specific blocker and stopped.

## 5. Shared workspace and document writes

All child sessions use the current shared working directory. Keep spec-specific documents and ticket files uniquely named by feature slug. Follow existing repository conventions and the live dependency skills for document locations and tracker publication.

For shared ADRs, glossaries, and other public documents, use additive reconciliation:

- preserve existing public content by default;
- retain distinct new content from both sides;
- deduplicate exact repeats;
- adjust placement when edits are compatible;
- reserve deletion or replacement for an explicit user decision;
- report a conflict only when the conclusions cannot both be true.

Before writing a shared file, read its latest contents. If a semantic conflict appears, pause the affected child and report both conclusions, the affected specs and documents, and the decision the user must make. Do not silently choose one conclusion.

## 6. Completion, failure, and resumption

The parent session aggregates each child as it completes or needs attention. For every group, report:

- spec name and status;
- spec path or tracker link;
- ADR, glossary, or other document changes;
- ticket links and blocking edges;
- unresolved questions or conflicts;
- whether the group is complete.

Keep completed groups when another group fails or pauses. Continue unaffected groups, do not roll back published results, and retry only clear transient tool failures. Semantic conflicts and missing user decisions require user input.

On a later run, inspect existing child-session status and spec/ticket artifacts before acting. Skip completed phases, continue incomplete phases, and avoid duplicate publication. Report ambiguous state instead of guessing.

The workflow is complete when every approved group is either complete with its spec and tickets published through the dependency process, or explicitly reported as blocked with the required user action.

Do not install skills, run setup, modify the dependency skills, implement code, create commits, push changes, or open pull requests as part of this workflow.
