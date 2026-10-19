# ADR 0003: Task-scoped write authorization

Status: Accepted.

Approval of a local-artifact group authorizes focused commits and ordinary
non-force pushes only to that group's dedicated task branch, including the
initial push that creates its matching remote ref. The authorization ends
with that group and does not authorize force-pushes, remote-ref deletion,
writes to other branches, pull request actions, or other GitHub writes.

For a `/spec-implement-loop` batch, the root-level coordinator requests one
task-start authorization before dispatching any implementation spec. The
request names the complete frozen spec set, affected repositories and
branches, and each authorized Git and GitHub issue action category. The grant
covers only those listed resources and categories across that batch; it
replaces repeated per-root authorization requests within the batch. It does
not authorize force-pushes, remote-ref deletion, unlisted branches, pull
requests, unlisted cross-root operations, or unlisted issue-write categories.
Other repositories retain their own approval rules unless they are explicitly
named in the request.

If authorization is pending or does not cover a required spec, resource, or
action, pause the batch before dispatch or the covered write; do not fall back
to separate per-root requests. Retry transient push and status-sync failures
up to three total attempts. Before retrying an operation with an uncertain
outcome, reconcile the remote state; do not retry permanent failures.

For the repository containing each named root, the grant may include the
focused integration commits and normal pushes already defined by the
workflow, plus the approved issue status synchronization at the existing
checkpoints: sync ticket status after the ticket review checkpoint and
confirmed push; the ticket review checkpoint is an internal workflow review
and does not require human approval. Sync the root after final verification
and review, before the separate root completion checkpoint. The grant does
not replace the separate root completion approval.

For a multi-root `/spec-implement-loop` batch, one task-start authorization may
authorize cross-root base or merge operations only when each operation names
the source root and branch, the dependent root and exact destination branch or
worktree, and whether it creates a dependent ticket branch from the source or
merges the source branch into the dependent integration branch. The
task-start authorization covers only those listed cross-root operations for
that batch. Every other Git or GitHub write keeps its existing approval gate.
