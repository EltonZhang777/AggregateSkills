# ADR 0003: Task-scoped write authorization

Status: Accepted.

Approval of a local-artifact group authorizes focused commits and ordinary
non-force pushes only to that group's dedicated task branch, including the
initial push that creates its matching remote ref. The authorization ends
with that group and does not authorize force-pushes, remote-ref deletion,
writes to other branches, pull request actions, or other GitHub writes.

For `/spec-implement-loop` roots, approval also covers the focused integration
commits and normal pushes already defined by that workflow. This added
authorization is limited to status synchronization for the root and its
tickets in the repository containing the root, at the existing checkpoints:
sync ticket status after the ticket review checkpoint and confirmed push; sync
the root after final verification and review, before the separate
root completion checkpoint. It does not waive either checkpoint or authorize
non-status writes such as issue creation, comments, labels, pull requests, or
merges. Other repositories retain their own approval rules.

For a multi-root `/spec-implement-loop` batch, one batch-start approval may
authorize cross-root base or merge operations only when each operation names
the source root and branch, the dependent root and exact destination branch or
worktree, and whether it creates a dependent ticket branch from the source or
merges the source branch into the dependent integration branch. The
batch-start approval authorizes only those listed cross-root operations
for that batch. It supplements the existing per-root task-scoped grants;
every other Git or GitHub write keeps its existing approval gate.
