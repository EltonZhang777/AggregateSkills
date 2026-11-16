<!-- extra-setup-matt-pocock-skills:root-operations:start -->
<a id="session-and-checkout-operations"></a>
## Session and checkout operations

At session start, take a read-only snapshot of the checkout before any mutation: repository root, branch or detached state, full object ID when the version-control system provides one, and complete working-tree status. Do not update remote state merely to create this snapshot.

Immediately before the first local mutation or branch creation in the session, repeat the read-only snapshot. Compare exact values only when a handoff supplies expected values. Stop if a supplied expected repository root, branch or detached state, full object ID, or status no longer matches. Do not invent expected values. Do not require a worktree unless the target repository or a valid handoff explicitly selects one. A selected worktree is the authoritative execution location. When the repository identifies a shared checkout as integration-only, do not execute ticket work there.

Report existing tracked, untracked, or ignored changes. Preserve them. Never stash, clean, reset, checkout over, or otherwise overwrite another session's work. If the requested mutation cannot be isolated from existing changes, stop and ask before writing.

<a id="handoff-approval-records"></a>
### Handoff approval records

A handoff that carries authority records these required fields:

| Field | Required content |
| --- | --- |
| `source` | The source thread and user message, or other verifiable user instruction evidence |
| `action` | The externally visible action category |
| `normalized_target` | The normalized repository, worktree, issue, or external-resource target |
| `lifetime` | `one-time` or `task` |
| `invalidators` | Conditions that end the approval |

Match the required fields exactly. Do not infer a missing value or accept a renamed substitute. A target, scope, or action change invalidates reuse.

A `one-time` approval is consumed when the first externally visible attempt starts. A pre-execution sandbox or technical denial does not consume it. An uncertain outcome, or any outcome that may have reached the external system, consumes it.

A `task` lifetime lasts only while that task is open. It ends when the task completes, the approval is withdrawn, or any invalidator occurs. It does not become thread-wide authority.

Store consumption state separately from the reusable approval record. Include the attempted action, time, and outcome evidence when the host records it. Stop when consumption or concurrent ownership cannot be established.

Technical failure or denial never becomes consent. Retries and elevation never bypass an approval, security gate, or confirmation gate. Never record secrets in an approval record.
<!-- extra-setup-matt-pocock-skills:root-operations:end -->
