# Multi-PR batch reference

Use this reference before discovering scope or changes for a request that may cover multiple PRs or source branches. It defines batch selection and coordination. Shared per-entry safeguards and outcome summaries remain canonical in [Process a batch](../SKILL.md#process-a-batch); resolve and execute each operation through the main skill's [source and target resolution](../SKILL.md#resolve-the-source-and-target), [repository requirements](../SKILL.md#check-repository-requirements), [PR preparation](../SKILL.md#reuse-or-prepare-the-pr), and [merge approval](../SKILL.md#merge-after-approval). Follow those sections for the shared workflow and gates.

## Discover and deduplicate selectors

Resolve selectors within the one exact repository named for the batch. Accept PR numbers, inclusive PR ranges, source branches, worktree paths, and mixtures of those selectors. Expand each range inclusively and resolve every number; do not silently skip an unmatched value. Verify each branch or worktree's repository and source branch, then use the main skill's source and target procedure to find its exact PR and base. If selectors point to different or unclear repositories, pause and ask before discovery continues.

Keep each original selector as an alias. Deduplicate selectors only when they resolve to the same exact PR in the same repository. When no PR exists, combine selectors only when they identify the same repository, source branch, and explicit base. Show all selector aliases on the resulting operation. Do not collapse entries merely because they share a title, OID, or changed paths. If a branch maps to multiple plausible PRs or bases, retain it as an ambiguous selector instead of guessing.

Different bases stay separate operations. An explicit stack relationship established by the user or an exact PR may link them for ordering, but never deduplicates them.

## Report the complete scope

Return one row per deduplicated operation and include all selector aliases. Give unmatched selectors, ambiguous branch-to-PR mappings, and missing base values their own blocked rows with the evidence and the specific input needed to unblock them. A source branch with no matching PR requires an explicit base; when supplied, it is a prospective PR operation. Without an explicit base, report a blocked row. Closed and merged PRs are report-only and produce no planned writes. Continue processing unrelated operations whose scope is clear.

Include selected draft PRs in the scope report with their draft state. Explicitly include selected already-blocked PRs, with the concrete blocker and affected dependents. Closed and merged PRs remain report-only. Each row identifies the exact repository and PR or source branch/worktree, its resolved base when known, and its state: eligible, report-only, or blocked with a concrete reason. Do not omit an unresolved selector or combine it with an unrelated operation.

## Present the exact plan and authorize the batch

Read all selected diffs before finalizing the plan. Before the first write, present one row per operation with its repository; PR link or source branch/worktree; resolved base; source head SHA; dependencies; planned pushes, PR creation or update, and merges; and all blockers. Identify an existing PR by its number and link. For a PR to be created, identify its source branch, base, and source head SHA. List conflict-resolution work separately, including the exact PR and any intended commit, push, or merge.

Ask for one explicit authorization for the complete listed write set. That authorization covers only the named entries and actions in this plan. For every planned merge, list the exact PR and its head and base names and OIDs. This explicitly satisfies the main skill's per-PR merge approval for that PR and snapshot; live merge checks for that PR still apply. A base OID advancement alone does not revoke batch authorization when the approved source head is unchanged and no new conflict-resolution work is required: refresh the diff, mergeability, reviews, and checks, then proceed under the existing authorization if live gates pass. For a PR to be created, identify its source branch, source head SHA, and base, then verify the created PR matches those values before merging. A plan with no writes needs no authorization prompt. If the source head, target base ref, scope, or planned write changes before execution, or new conflict-resolution work is required, stop that operation, refresh the plan, and obtain renewed authorization before its next write. Never infer authorization for an unlisted action.

## Order dependencies and conflict candidates

Read every selected diff before ordering. Treat dependencies stated by the user or established by an exact existing PR base as hard constraints; do not infer a stack from commit ancestry. Process operations topologically. Among dependency-ready operations, prefer conflict-free work before conflict candidates; use the supplied order or original input order only to break ties within either group. A supplied complete order cannot bypass this preference.

Use changed-path overlap only to group potential conflicts for PRs with the same base, unless an explicit stack relationship applies. Overlap is a conflict candidate, not proof of a dependency or an actual merge conflict. Do not let path overlap create or remove a dependency. A cycle or unresolved relationship blocks the affected operations and their dependents; continue unrelated work.

## Execute the approved batch

Start writes only after the batch plan is authorized. Prepare or reuse every eligible PR in the approved order before merging any, then merge them in that same order. Apply the main skill's per-entry blockers throughout: a blocked operation blocks its dependents, while unrelated eligible operations continue.

Before each merge, compare the PR, source head, and target base ref with the authorized plan. Do not ask again for that unchanged merge. Do not ask again solely because the base OID advanced when the approved source head is unchanged and no new conflict-resolution work is required. Run the live per-PR merge checks in the main skill immediately before merging. If a merge was not listed, obtain its exact per-PR approval once before merging. If the source head, target base ref, or planned action changed, or new conflict-resolution work is required, refresh the plan and obtain renewed authorization before that operation's next write. Use the main skill's outcome summary at every pause, stop, and batch completion.

## Gate conflict resolution

When an authorized merge encounters a conflict, reuse a matching clean worktree if one exists. Create a worktree under the repository root's `.wt` directory only when needed. A dirty worktree blocks the affected operation; never clean it to proceed. Use the main skill's conflict-resolution procedure and run the required checks on the resolved worktree.

Never stage, commit, stash, discard, or push automatically. Inspect the complete unstaged conflict-resolution diff and worktree status, run the required checks, then present the diff, check results, and intended commit, push, and merge. Obtain explicit approval for that exact diff and write set before staging or any other write. After approval, stage only the approved files and inspect the staged diff. If the staged diff differs from the approved diff, stop, present the changed diff, and obtain renewed approval before proceeding. A changed path outside the conflict resolution blocks that operation until the scope is reviewed. Keep the conflict-specific approval separate from the batch authorization and follow [the canonical merge procedure](../merge-after-approval.md).

## Refresh after source or base changes

Before each write or merge, compare and record the current head and base OIDs against the approved plan and PR snapshot. After a base advances, refresh the affected diff, mergeability, reviews, and required checks. Base OID advancement alone does not revoke batch authorization when the approved source head and target base ref are unchanged and no new conflict-resolution work is required; do not request renewed authorization solely for that OID change. When an upstream PR merges, retarget its directly stacked downstream PR to the upstream PR's former base as described in the canonical merge procedure, then refresh those same facts.

If a source head changes outside an authorized planned push, report the old and new OIDs, the commits between them, and the current diff against the approved source snapshot. Pause that PR and its dependents for review; unrelated operations continue. A changed source head or target base ref invalidates the affected authorization. Refresh the plan, diff, mergeability, reviews, and checks, then obtain renewed authorization or per-PR approval before proceeding. A base OID change with the same target base ref and approved source head retains batch authorization unless new conflict-resolution work is required. Never act on stale source or base state.
