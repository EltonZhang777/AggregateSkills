# Merge after approval

Merge each PR only after the user explicitly approves that exact PR. Follow the dependency order, then input order among independent entries. Immediately before each merge, recheck that PR's head and base, mergeability, required checks, and repository merge policy. A blocker stops that PR and its dependents; continue with other approved independent PRs. Also confirm the supplied worktree is clean; if it became dirty, stop and ask:

```sh
gh pr view NUMBER --repo OWNER/REPO --json state,isDraft,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,headRefName,headRefOid,baseRefName,baseRefOid,url
gh pr checks NUMBER --repo OWNER/REPO
```

A failed, pending, or unknown required check, an unmergeable PR, or an unclear policy blocks that PR. If either OID differs from the reviewed PR, refresh the diff and checks and get renewed approval. After an upstream PR merges, retarget each directly stacked downstream PR to the upstream PR's former base with gh pr edit NUMBER --repo OWNER/REPO --base TARGET_BASE. Re-read its head and base OIDs, diff, required checks, and mergeability. Get renewed explicit approval if retargeting materially changes the diff, invalidates the prior approval, or changes either OID. A retargeting or check failure blocks that PR and its dependents only. Follow the repository's explicitly documented merge method. If the policy does not select an enabled method, ask which enabled method to use; if none is enabled, block the merge. Do not infer a method from the available options alone. Merge with exactly one of `gh pr merge NUMBER --merge`, `gh pr merge NUMBER --squash`, or `gh pr merge NUMBER --rebase`, as the policy requires. Do not use auto-merge.

After the command succeeds, verify the PR result:

```sh
gh pr view NUMBER --repo OWNER/REPO --json state,mergedAt,url
```

Confirm `state` is `MERGED` and `mergedAt` is set before reporting success. Otherwise report the observed state and stop.

When an approved merge encounters a conflict, use `/resolving-merge-conflicts`, but stop before its commit step. Run required local checks on the resolved worktree and inspect its status. If any changed path is outside the conflict resolution, stop. Stage only the reviewed conflict-resolution files and inspect the staged diff. Present the exact resolved diff and results. Get renewed explicit approval for that diff's commit, push, and merge. After the push, confirm the PR diff still matches the approved resolution and record its head and base OIDs. Recheck PR checks and mergeability before merging; any later OID or diff change requires renewed approval.

Never merge a PR outside the supplied batch, post PR comments, or delete branches or worktrees as part of this workflow.
