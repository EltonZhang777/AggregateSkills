---
name: prune-worktrees-and-branches
description: Preview registered Git worktrees and local or remote branch cleanup candidates against a user-supplied base branch.
metadata:
  prerequisites: '{"skills":[],"mcps":[],"tools":[]}'
---

# Prune worktrees and branches

Run this skill only for a cleanup request. The preview is the required first phase of cleanup. Do not use it as a general inventory or status-reporting mode.

## Preview contract

- Ask for the intended base branch if the user did not supply one. Do not guess.
- Preview is read-only. Never remove a worktree or branch, prune metadata, fetch, push, update a ref, or change remote state while building it.
- Report every registered worktree, local branch, and configured-remote branch as **safe to clean**, **keep**, or **needs manual confirmation**, with evidence and a reason.
- Unknown, failed, incomplete, or out-of-date evidence must never produce **safe to clean**. The only stale-state candidate that can be safe is an exact worktree metadata target reported by a successful dry run.
- This ticket implements preview only. Stop after presenting it; do not perform cleanup.

## Resolve the base first

1. Confirm the current directory is inside the intended Git repository with `git rev-parse --show-toplevel`.
2. Collect branch refs with `git for-each-ref --format='%(refname)' refs/heads refs/remotes`.
3. Resolve the supplied value only against branch refs:
   - If it starts with `refs/heads/` or `refs/remotes/`, require that exact ref.
   - Otherwise derive candidates by removing only the refs/heads/ or refs/remotes/ prefix from each full ref, then compare exact strings; do not use Git auto-abbreviation or DWIM.
   - Require exactly one full ref match, then verify that it resolves to a commit with `git rev-parse --verify <full-ref>^{commit}`.
4. Stop before the inventory if the value is empty, missing, ambiguous, is only a tag, or does not resolve to a commit. Ask the user to provide a fully qualified branch ref when needed.
5. If the resolved ref is under `refs/remotes/`, split it into exactly one configured remote name and branch name; remote names and branch names may contain `/`. Query `git ls-remote --heads <remote>` and require exactly one live `refs/heads/<branch>` whose object ID matches the resolved base. If the split, query, exact ref, or object ID is missing or ambiguous, stop before inventory and ask for a refreshed base. Do not fetch.

Do not fetch to make a missing base available.

## Collect the preview evidence

Run Git commands from this repository. Preserve their exit codes and error output; a failed command makes the affected state unknown.

### Worktrees

- Read `git worktree list --porcelain`. Record each path, HEAD, checked-out branch or detached state, lock reason, and any prunable marker. If the output cannot be parsed unambiguously, mark the affected entry **needs manual confirmation**.
- Identify the current worktree by comparing its path with `git rev-parse --show-toplevel`. On Windows, compare normalized paths without treating case differences as distinct.
- For each existing non-bare worktree, run `git -C <path> status --porcelain=v1 --untracked-files=all --ignored=matching`. Empty output means clean; ordinary status entries mean dirty, including untracked files. Record `!!` entries as ignored data and classify that worktree **needs manual confirmation**; ignored files may contain user data. If the path is missing or status fails, do not infer cleanliness.
- Run `git worktree prune --dry-run --verbose` once for the preview. Capture both stdout and stderr while preserving the exit code; some Git builds emit verbose targets on stderr. If it succeeds, show its exact stale metadata targets in a separate list; if it fails, classify them as unknown. This is a dry run: never repeat it without `--dry-run`, and never run the actual prune during this ticket.

### Local and remote branches

- Read local and remote-tracking refs with `git for-each-ref`; record each ref's full name, tip commit, upstream, and ahead/behind tracking information when present.
- For every configured remote, query live heads with `git ls-remote --heads <remote>`. This reads remote refs without updating local refs. Do not run `git fetch`, `git pull`, or `git remote prune`.
- For each local branch, compare its tip to the resolved base with `git merge-base --is-ancestor <branch-ref> <base-ref>`. Exit 0 means merged; exit 1 means not merged; any other result is unknown.
- If a local branch has an upstream, resolve the upstream's configured remote and exact branch ref. Confirm the live `ls-remote` object ID matches the local tracking ref before using `git rev-list --left-right --count <upstream>...<branch-ref>`; the left count is behind and the right count is ahead. If the remote query fails, the refs differ, or the object needed for comparison is unavailable locally, mark pushed state **unknown**. Do not fetch to fill the gap.
- If a branch has no upstream, report that fact and do not claim it is pushed. Mark it **needs manual confirmation** unless its state can otherwise be proved without assuming remote state.
- For each live remote branch, record the remote URL, branch name, and live object ID. Test ancestry against the base only when the required commit objects are already available locally; otherwise mark ancestry unknown. Never fetch during preview.

### GitHub pull requests, protection, and default branch

- Use GitHub CLI checks only for a remote whose URL identifies a GitHub repository. Resolve its exact host, owner, and repository; verify authentication with `gh auth status --hostname <host>`. Use `<host>/<owner>/<repo>` for repository and PR commands, and `--hostname <host>` for API commands. If any value, host-specific authentication, network, or response is uncertain, mark the affected PR, protection, or default-branch state **unknown**.
- Read the repository default branch and fork relationship with `gh repo view <host>/<owner>/<repo> --json nameWithOwner,defaultBranchRef,isFork,parent`. Do not assume the default branch is named `main` or `master`. If a fork parent cannot be read, PR coverage is unknown.
- For each candidate branch, query all PR states in its source repository and every known possible base repository with `gh pr list --repo <host>/<owner>/<repo> --state all --head <branch> --limit 1000 --json number,state,mergedAt,headRefName,headRepositoryOwner,baseRefName,url`. Match exact `headRefName` and `headRepositoryOwner.login` to the source remote owner; missing or ambiguous head metadata makes PR state unknown. The `--head` option does not accept `owner:branch`. An open PR or a closed PR with no `mergedAt` is unmerged; keep that branch. If a result reaches the limit or is otherwise incomplete, PR state is unknown.
- For a fork source, inspect its `parent` repository and the parent chain, and query each configured GitHub remote that could be a PR base. If the complete set of possible base repositories cannot be identified and queried, PR state is **unknown** and the branch needs manual confirmation, even when queried lists are empty. Never treat an empty result from the fork repository alone as proof that no PR exists.
- Read branch protection and ruleset status with `gh api --hostname <host> --paginate --method GET "repos/<owner>/<repo>/branches?per_page=100" --jq '.[] | [.name, (.protected | tostring)] | @tsv'`. Match branch names exactly. A protected branch is **keep**. A failed or incomplete query means protection is unknown, not unprotected.
- If a required GitHub check is unavailable, do not mark the affected branch **safe to clean**. Preserve the error or unavailable reason in the report.

## Classify conservatively

Apply the strongest applicable result: **keep** when evidence proves a preserve condition; otherwise **needs manual confirmation** when any required evidence is unknown; use **safe to clean** only when every relevant check succeeded.

**Keep** a worktree or branch when it is current, is the supplied base, is the repository default, is protected, is dirty, is locked, is unmerged, has unpushed commits, or has an open or unmerged PR. Keep a worktree when its branch is kept.

Use **needs manual confirmation** for detached HEADs, missing or inaccessible worktrees, any `!!` ignored entries, absent or stale upstream data, unavailable remote/PR/protection/default-branch state, command errors, or any ambiguous relationship. A stale worktree metadata target listed by a successful dry run is a separate **safe to clean** metadata candidate; it is not a worktree path to delete. If the dry run fails or its targets cannot be read exactly, classify the metadata as **needs manual confirmation**. Never infer that an arbitrary filesystem directory is safe to delete.

A worktree is **safe to clean** only when it exists, is not current or locked, has no tracked, untracked, or ignored files, and its checked-out branch independently qualifies as safe. A local branch is **safe to clean** only when it is merged into the base, has no unpushed commits, is not current/base/default/protected, has no open or unmerged PR, and has no worktree that must be kept. A remote branch is **safe to clean** only when its live ref, ancestry, PR state, and protection state are all positively established as safe. If any check does not apply, explain why; if applicability is uncertain, use manual confirmation.

## Report

Start with the resolved base ref and commit ID. Then report:

1. One row per registered worktree, local branch, and remote branch: target, classification, evidence (including cleanliness/lock, ancestry, upstream and ahead/behind or pushed state, remote state, PR state when available, and protection), and reason.
2. The exact stale metadata targets printed by the prune dry run, each classified safe or manual, separate from worktree paths.
3. Every unavailable check or command failure and which candidates it affected.

Do not collapse several targets into one row. Do not call a candidate safe based only on its name, age, or absence from a worktree.

## Shell handling

Git options are the same in PowerShell and POSIX shells. Pass each path and ref as one quoted argument; do not build shell commands by concatenating untrusted values. In PowerShell, use an argument array and splatting for dynamic paths (for example, `$gitArgs = @('-C', $worktreePath, 'status', '--porcelain=v1', '--untracked-files=all', '--ignored=matching'); git @gitArgs`); in POSIX shells, quote expansions (for example, `git -C "$worktree_path" status --porcelain=v1 --untracked-files=all --ignored=matching`). Keep commands on one line when possible: POSIX uses `\` for line continuation, while PowerShell uses a backtick. Do not copy POSIX-only pipes or path commands into PowerShell.
