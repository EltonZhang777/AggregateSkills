---
name: pr-and-merge
description: Prepare GitHub pull requests from one supplied branch or worktree, then merge only after explicit per-PR approval.
metadata:
  prerequisites: '{"skills":[["conventional-git-messages","EltonZhang777/AggregateSkills"],["resolving-merge-conflicts","mattpocock/skills"]],"mcps":[],"tools":[["GitHub CLI (gh)","https://cli.github.com/","Install from https://cli.github.com/","Authenticate with `gh auth login`"]]}'
---

# PR and merge

This workflow is for GitHub. For another hosting platform, say in one sentence
that the invoking agent handles that platform. Process one supplied branch or
worktree per invocation.

## Resolve the source and target

Require an exact source repository and branch or worktree. From that checkout,
inspect `git rev-parse --show-toplevel`, `git remote -v`,
`git branch --show-current`, and `git status --porcelain=v1 --untracked-files=all`.
Verify the supplied worktree belongs to the intended repository and branch. If
the repository, source branch, target, or existing stacked relationship is
ambiguous, ask before any external action. A dirty worktree blocks this PR; do
not stash, stage, or clean it.

For GitHub, verify `gh auth status --hostname github.com` and resolve the exact
`OWNER/REPO`. Read the default branch with:

```sh
gh repo view OWNER/REPO --json nameWithOwner,defaultBranchRef
```

Find existing PRs for the source branch before resolving its target:

```sh
gh pr list --repo OWNER/REPO --head HEAD_BRANCH --state all --limit 1000 --json number,state,title,body,headRefName,headRefOid,headRepository,baseRefName,url
```

Match the exact source repository using `headRepository.nameWithOwner` and
the exact branch using `headRefName`. If the result reaches the limit or
cannot be read completely, treat it as incomplete and ask. Use a
user-specified target when present. Otherwise, preserve the base of one
matching open PR. If no open PR exists, preserve a stacked base only when the
invocation or repository evidence identifies it unambiguously; if a stacked
relationship is indicated but its base is unclear, ask. Use the repository
default only when no existing PR or known stack establishes another base.
When an existing PR conflicts with the requested target, report it and ask
before opening another PR. If a requested target conflicts with a known
stacked base, report the conflict and ask before retargeting it.

## Check repository requirements

Read the target repository's `AGENTS.md`, contribution guidance, pull request
template, and relevant GitHub workflow files. Identify the checks those sources
require for this change. Read the target branch's protection state, applicable
rulesets, and the repository's enabled merge methods and documented merge
policy:

```sh
gh api repos/OWNER/REPO/branches/BASE --jq '{name,protected}'
gh api --paginate 'repos/OWNER/REPO/rulesets?includes_parents=true'
gh api repos/OWNER/REPO --jq '{allow_merge_commit,allow_squash_merge,allow_rebase_merge}'
```

If `protected` is true, read its required status checks:

```sh
gh api repos/OWNER/REPO/branches/BASE/protection/required_status_checks
```

If `protected` is false, there is no classic branch protection; still inspect
rulesets. Match active rulesets to the exact target branch. Treat permission,
network, or incomplete-response errors as unknown; do not infer that checks
or rules are absent. Unknown or unavailable check requirements block any
source-branch push or PR creation/update. Run only required local checks named
by repository instructions; a failed, unknown, or unavailable required
precheck blocks any such external write. Once a PR exists, compare its
results with the required checks using `gh pr checks NUMBER --repo OWNER/REPO`.
Pending, failed, or unknown required PR checks block merging.

## Reuse or prepare the PR

From the PR candidates gathered above, reuse one exact matching open PR with
the resolved base. If there are multiple matches, or only a closed or
differently based PR exists, report the candidates and ask before opening
another. Do not create a duplicate.

Only an explicit request to prepare or create this PR authorizes pushing the
supplied source branch or creating/updating that exact PR. An inspection or
drafting request stays read-only; report any source-branch mismatch without
publishing it.

After required local checks, recheck `git status --porcelain=v1 --untracked-files=all`.
Repeat this check immediately before any push, PR creation, or PR edit. If a
check leaves the worktree dirty, stop without publishing or cleaning it.

Before creating or updating a PR, compare local `HEAD` with the exact source
branch published on GitHub. Fetch it with `git fetch REMOTE HEAD_BRANCH`. For
an existing PR, confirm the fetched OID matches its `headRefOid`; if not,
reload the PR and ask if they still disagree. Distinguish a missing source ref
from authentication or network errors; treat an unknown result as a blocker.
If no source branch is published and there is no existing PR candidate, push
only the supplied branch normally. If a PR candidate exists but its source
branch is unpublished, stop and ask.
If local HEAD is strictly ahead, push only that branch with a normal
fast-forward push. If the published branch is ahead or the histories diverge,
stop and ask; never force-push or rewrite. After a push, reload the PR
candidates and verify the published source head. If a PR already exists,
reload its head OID, diff, and checks. If creating a new PR, create it next and
use the shared post-create verification below.

The only push command is:

```sh
git push REMOTE HEAD:refs/heads/HEAD_BRANCH
```

Read the current diff and the repository's PR title and description guidance.
Delegate title and body drafting to `conventional-git-messages`, supplying
those sources, the change facts, and recent same-type PR examples. Follow that
skill's rules; ask when required facts or prefix conventions are unclear.
Update an existing PR's text only when it is inaccurate, materially
incomplete, or clearly inconsistent with current repository guidance. Consider
`show-me` or `archify` only when a diagram materially
improves clarity and an accessible skill is available; otherwise omit it.

After synchronizing the source branch as above, create a new PR with the
resolved head, base, title, and body:

```sh
gh pr create --repo OWNER/REPO --head HEAD_BRANCH --base BASE --title "TITLE" --body-file BODY_FILE
```

Pass the title and `BODY_FILE` path as single arguments using the active
shell's quoting rules. Write the exact multiline body to a temporary UTF-8
file.

For a fork head, pass `OWNER:HEAD_BRANCH` to `--head`. If `gh pr create` cannot
represent the exact source owner, stop and ask rather than using another head.

For an existing exact match, reuse it and update only fields that need
correction with `gh pr edit NUMBER --repo OWNER/REPO`. Pass `--title` as one
shell argument and `--body-file BODY_FILE` for an updated body; omit unchanged
fields.

After creating or reusing a PR, read it with `gh pr view NUMBER --repo OWNER/REPO --json headRefOid,baseRefOid,headRefName,baseRefName,url`
and read its diff and checks with `gh pr diff NUMBER --repo OWNER/REPO` and
`gh pr checks NUMBER --repo OWNER/REPO`. Return the PR link, head and base
names and OIDs, relevant diff, and required-check results. Record those OIDs as
the approval snapshot. Then pause for review. Do not merge yet.

## Merge after approval

Merge only after the user explicitly approves that exact PR. Immediately
before merging, recheck the PR's head and base, mergeability, required checks,
and repository merge policy. Also confirm the supplied worktree is clean; if it
became dirty, stop and ask:

```sh
gh pr view NUMBER --repo OWNER/REPO --json state,isDraft,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,headRefName,headRefOid,baseRefName,baseRefOid,url
gh pr checks NUMBER --repo OWNER/REPO
```

A failed, pending, or unknown required check, an unmergeable PR, or an unclear
policy blocks that PR. If either OID differs from the reviewed PR, refresh the
diff and checks and get renewed approval. Follow the repository's explicitly
documented merge method. If the policy does not select an enabled method, ask
which enabled method to use; if none is enabled, block the merge. Do not infer
a method from the available options alone. Merge with exactly one of
`gh pr merge NUMBER --merge`,
`gh pr merge NUMBER --squash`, or `gh pr merge NUMBER --rebase`, as the policy
requires. Do not use auto-merge.

After the command succeeds, verify the PR result:

```sh
gh pr view NUMBER --repo OWNER/REPO --json state,mergedAt,url
```

Confirm `state` is `MERGED` and `mergedAt` is set before reporting success.
Otherwise report the observed state and stop.

Use `resolving-merge-conflicts` for a conflict, but stop before its commit
step. Run required local checks on the resolved worktree and inspect its
status. If any changed path is outside the conflict resolution, stop. Stage
only the reviewed conflict-resolution files and inspect the staged diff.
Present the exact resolved diff and results. Get renewed explicit approval for
that diff's commit, push, and merge. After the push, confirm the PR diff still
matches the approved resolution and record its head and base OIDs. Recheck PR
checks and mergeability before merging; any later OID or diff change requires
renewed approval.

Never merge another PR, post PR comments, or delete branches or worktrees as
part of this workflow.
