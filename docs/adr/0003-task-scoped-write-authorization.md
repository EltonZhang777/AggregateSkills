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
