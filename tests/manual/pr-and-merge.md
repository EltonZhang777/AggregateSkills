# /pr-and-merge manual scenarios

Run these through the user-visible `/pr-and-merge` skill invocation in a disposable GitHub repository unless the user explicitly authorizes a same-repository test. For issue #42, the user authorized this repository; use only `codex/issue-40-pr-and-merge` as the target. Use one or more supplied branches or worktrees per invocation. Record the repository, source branches, target branches, PR links, required checks, dependency order, and each approval boundary. Do not use a production repository or important branch.

## Clean single-branch PR

Create a clean feature branch in the disposable repository, configure a
default branch and an explicit merge policy, and make the required checks
pass. Ask the skill to prepare a PR for that branch without naming a target.

Confirm the skill verifies the exact repository and branch, reads the repo
instructions, selects the repository default branch, checks the required
status, and creates one PR with that head and base. The title and body follow
the repository evidence and `/conventional-git-messages` rules. It returns
the PR link, diff, and required-check status, then pauses without merging.
Repeat with a second clean branch and an explicit non-default target; confirm
it uses the requested base.

## Reuse an existing matching PR

Create an open PR for the exact source branch with a non-default base. Add a
commit to the supplied local branch without publishing it, and make the PR
title or body stale. Ask the skill to prepare that branch again without
naming a target.

Confirm it pushes only that branch normally, refreshes the PR head, diff, and
checks, preserves the existing base, reuses the exact open PR, and updates
only inaccurate PR text using repository evidence and
`/conventional-git-messages`. Repeat with an explicit target that conflicts
with the existing PR; confirm it reports the conflict and asks before opening
another PR. A closed PR must also be reported before another is opened.

## Dirty branch and failed required check

Run once with an uncommitted or untracked file in the supplied worktree. Run
again with a required precheck failing or unavailable, and once with a
required precheck that creates an untracked output file.

Confirm each affected run is blocked before creating or editing a PR or
pushing. The skill reports the exact dirty state or check result and does not
invent additional checks.

## Ambiguous input and merge policy

Supply two plausible repositories or targets without identifying which one
to use. In a separate run, configure multiple allowed merge methods without
documenting a preferred method.

Confirm the skill asks a concise question before any dependent external
action. It must not guess the repository, target, or merge method.
When a supplied branch has a known stacked base but the request names a
different target, confirm it asks before changing that relationship.

## Merge approval and live gates

For an open PR with passing required checks and an explicit repository merge
policy, approve that exact PR. Immediately before merging, change a required
check to pending or failing; run the merge step.

Confirm the skill rechecks mergeability and required checks and blocks the
merge. Restore passing checks and repeat. Confirm it uses the documented
method and merges only after the per-PR approval.
In separate runs, change the PR head and base after approval; confirm each
time it refreshes the diff and checks and asks for renewed approval before
merging.

## Conflict resolution and second approval

Create a branch that conflicts with its target. Prepare its PR, then approve
that exact PR for merging.

Confirm the skill uses `/resolving-merge-conflicts`, runs the required checks,
and presents the resolved diff and results. It must pause for a second
explicit approval covering the conflict-fix commit, its push, and that PR's
merge. After the approved push, confirm it checks the PR's required CI gates
again and that the published diff matches the approved resolution before
merging. Confirm any later head or base OID change requires renewed approval.

## Multi-PR batch: ordering, stacked retarget, and failure isolation

Prepare three clean worktrees in one test repository: branch A and branch B independently target the same base, and branch C is explicitly stacked on branch A. Supply them in the order C, B, A in one /pr-and-merge invocation. Confirm the workflow processes B, then A, then C: the dependency requires A before C, while the input order puts independent B before A. Confirm it creates or reuses one exact PR per eligible source, then returns separate review snapshots and pauses before merging.

Approve and merge branch A. Confirm branch C is retargeted from A to A's former base, then its head and base OIDs, diff, mergeability, and required checks are refreshed. If retargeting changes either OID, materially changes the diff, or invalidates approval, confirm the workflow asks for renewed approval before merging C. Branch B remains independent and can proceed only with its own approval and passing gates.

In a separate batch, supply a dirty branch D, branch E explicitly stacked on D, and a clean independent branch F. Confirm D and dependent E are blocked without publishing them, while F continues through its own prechecks and PR preparation. Repeat with a required check failing for one entry if the test repository can configure that check; confirm only that entry and its dependents stop.

## Other hosting platform

Invoke the skill for a repository hosted outside GitHub.

Confirm it says in one sentence that the invoking agent handles that
platform and adds no provider-specific workflow.
