## Durable project text language

- For new or materially rewritten natural-language project text, follow only the normative prose in the root
  `AGENTS.md` of the target repository: the repository receiving the text, including the repository that owns a
  GitHub issue or pull request. When source and target repositories differ, do not use source-repository or
  skill-installation instructions as the target policy. When they are the same repository, its root file is the
  target policy. Nested `AGENTS.md` files do not override the target root.
- When compressing existing source documents, preserve the source language sentence by sentence instead of
  normalizing the content to the target repository's language. This is an exception to the rule above for
  compressed source content.
- If the normative prose is mixed and has no discernible dominant language, ask the user before writing.
- Preserve untouched text. When existing text uses another language, apply the rule only to new or materially
  rewritten passages and report any resulting language mixture.
- Spelling-only and formatting-only edits, commit messages, ordinary chat, and read-only analysis or review
  output are outside this rule.

## Agent skills

### Issue tracker

Issues and specs for this repository live in GitHub Issues; use the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the five canonical triage labels documented for this repository. See `docs/agents/triage-labels.md`.

### Domain docs

Before any codebase exploration, read [docs/agents/domain.md](docs/agents/domain.md) regardless of the task's domain relevance. This repository uses a single-context domain-doc layout.

<!-- extra-setup-matt-pocock-skills:root-operations:start -->
<a id="session-and-checkout-operations"></a>
## Session and checkout operations

At session start, take a read-only snapshot of the checkout before any mutation: repository root, branch or detached state, full object ID when the version-control system provides one, and complete working-tree status. Do not update remote state merely to create this snapshot.

Immediately before the first local mutation or branch creation in the session, repeat the read-only snapshot. Compare exact values only when a handoff supplies expected values. Stop if a supplied expected repository root, branch or detached state, full object ID, or status no longer matches. Do not invent expected values or require a worktree.

Report existing tracked, untracked, or ignored changes. Preserve them. Never stash, clean, reset, checkout over, or otherwise overwrite another session's work. If the requested mutation cannot be isolated from existing changes, stop and ask before writing.

<a id="handoff-approval-records"></a>
### Handoff approval records

A handoff that carries authority records these fields:

| Field | Required content |
| --- | --- |
| `approval_id` | Stable identifier for the record |
| `source` | Who or what granted the approval |
| `action` | The externally visible action category |
| `target` | The exact repository, issue, branch, ref, or resource |
| `scope` | The exact resources and limits covered |
| `lifetime` | `one-use` or `current-group` |
| `invalidators` | Conditions that end the approval |

Match every field exactly. Do not infer a missing value, broaden a target, or extend a lifetime.

A `one-use` approval is consumed when the first externally visible attempt starts. A pre-execution sandbox or technical denial does not consume it. An uncertain outcome, or any outcome that may have reached the external system, consumes it.

A `current-group` approval requires a stable group identifier and ends when the approved group completes, the approval is withdrawn, or an invalidator occurs. It does not become thread-wide authority.

Store consumption state separately from the reusable approval record. Include the attempted action, time, and outcome evidence when the host records it. Stop when consumption or concurrent ownership cannot be established.

Technical failure or denial never becomes consent. Retries and elevation never bypass an approval, security gate, or confirmation gate. Never record secrets in an approval record.
<!-- extra-setup-matt-pocock-skills:root-operations:end -->
