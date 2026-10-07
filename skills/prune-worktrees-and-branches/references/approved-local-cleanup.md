# Approved local cleanup

Before each destructive local action, re-resolve the supplied base and require the same full ref and commit OID as the preview; for a remote-tracking base, also require the live remote OID to match. If the base changed or is unavailable, skip the affected action and report why.

For each approved worktree, immediately before removal:

1. Re-read `git worktree list --porcelain`; require the same registered path, branch, and HEAD as the preview. Confirm it is not the current worktree, is not locked, and still exists.
2. Re-run `git -C <path> status --porcelain=v1 --untracked-files=all --ignored=matching`; require empty output. Recheck that its branch is still safe against the resolved base and that required upstream, remote, PR, default-branch, and protection evidence is still known and safe.
3. If any target identity or required evidence changed, or any command fails, skip that item and report why. Otherwise run `git worktree remove <path>` without `--force` or `-f`. Never remove the directory with a filesystem command. On failure, report the error (including Windows lock errors), retain the associated branch, and continue with independent approved worktrees.

After the worktree-removal attempts, run actual worktree pruning exactly once if the user approved any worktree or stale-metadata cleanup target. Immediately beforehand, run `git worktree prune --dry-run --verbose` and preserve its exit code and output. Because actual prune is repository-wide, proceed only when this dry run succeeds and its exact target set equals the approved stale-metadata set; if targets changed, are unreadable, or include anything unapproved, skip actual prune and report why. Otherwise run `git worktree prune --verbose` once. Do not retry it. Do not run actual prune for branch-only cleanup.

Only after worktree removal attempts, handle approved local branches, one at a time. Immediately before each deletion, require the exact branch ref and tip OID from the preview, recheck that it is not current, base, default, protected, or checked out in any remaining worktree, and recheck merged ancestry, pushed state, and PR state. Skip it if any check changed or became unknown, or if its associated worktree removal failed. Otherwise run `git branch -d -- <branch>` with the exact branch name. Never use `-D`, `--force`, or `-f`. A failed deletion is reported; continue with independent approved branches.
