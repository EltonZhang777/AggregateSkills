---
name: pr-and-merge
description: Prepare GitHub pull requests from one or more supplied branches or worktrees, then merge only after explicit per-PR approval.
---

# /pr-and-merge

## Activation Criteria & Objective

Use this skill when the user asks to prepare GitHub pull requests for supplied branches or worktrees, or to merge prepared PRs after explicit per-PR approval. It handles GitHub only. For another hosting platform, say in one sentence that the invoking agent handles that platform.

## Dependencies

If any dependency is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

| Name | Type | Source |
| --- | --- | --- |
| /conventional-git-messages | Skill | https://github.com/EltonZhang777/AggregateSkills |
| /resolving-merge-conflicts | Skill | https://github.com/mattpocock/skills |
| SkillRoute CLI | Tool | https://github.com/erichare/skillroute |

## Process a batch

Treat every supplied source as an entry identified by its exact repository and branch or worktree. Resolve authentication, repository identity, target, existing PR, and required checks for each entry separately. If the repository for the whole batch is unclear, pause the batch. If one entry is unclear, ask about it in plain text, block that entry and its dependents, and continue unrelated entries whose inputs are clear. Never stash, stage, or clean a supplied worktree.

Build dependencies only from relationships stated by the user or an exact existing PR whose base is another supplied source branch; do not infer a stacked target from commit ancestry alone, and link dependencies only within the same repository. Preserve each existing PR base. If the user supplies a complete merge order, follow it only when it respects every dependency; otherwise ask before merging. When no explicit order is supplied, order entries topologically and choose the earliest input entry whenever multiple entries are ready. If an order remains ambiguous, ask a plain-text question. A cycle or unresolved relationship blocks those entries and their dependents while the answer is pending; continue the rest.

Prepare or reuse each eligible PR in that order. A dirty worktree, failed or unknown required check, or other blocking condition blocks only that entry and its dependents. Skip dependent entries whose required upstream is blocked, but continue independent entries. Finish preparing every eligible PR before merging any. Present a separate approval snapshot for each PR and pause. Approval applies only to the exact PR named by the user.

At every pause, stop, or batch completion, return one outcome summary with each supplied entry exactly once. Mark an entry `completed` only after its matching PR's merge is verified. Mark an entry `pending` only when its PR is otherwise eligible to proceed and is waiting for review, approval, or a follow-up action; that wait alone is not a blocker. Mark an entry `blocked` when an unmet prerequisite or safety gate, beyond an ordinary review or approval wait, prevents the next authorized action. Examples include unresolved input, dirty worktree, a failed, pending, or unknown required check, an unmergeable PR, or a blocked prerequisite. Include the exact repository and source branch or worktree, plus the PR link when one exists. Give each pending or blocked entry its concrete reason; name the unmet prerequisite for a blocked dependent. For each pending PR, keep a separate approval snapshot with that PR's head and base names and OIDs.

## Resolve the source and target

Require an exact source repository and branch or worktree. From that checkout, inspect `git rev-parse --show-toplevel`, `git remote -v`, `git branch --show-current`, `git rev-parse HEAD`, and `git status --porcelain=v1 --untracked-files=all`; record the source OID. Verify the supplied worktree belongs to the intended repository and branch. If the repository, source branch, target, or existing stacked relationship is ambiguous for this entry, ask before acting on this entry. A dirty worktree blocks this entry; do not stash, stage, or clean it.

For GitHub, verify `gh auth status --hostname github.com` and resolve the exact `OWNER/REPO`. Read the default branch with:

```sh
gh repo view OWNER/REPO --json nameWithOwner,defaultBranchRef
```

Find existing PRs for the source branch before resolving its target:

```sh
gh pr list --repo OWNER/REPO --head HEAD_BRANCH --state all --limit 1000 --json number,state,title,body,headRefName,headRefOid,headRepository,baseRefName,url
```

Match the exact source repository using `headRepository.nameWithOwner` and the exact branch using `headRefName`. If the result reaches the limit or cannot be read completely, treat it as incomplete and ask. Use a user-specified target when present. Otherwise, preserve the base of exactly one matching open PR. If there is no matching open PR but exactly one matching merged PR, use its base to verify whether it is an exact completed match. If multiple candidates make the base or state ambiguous, ask. If no PR establishes the base, preserve a stacked base only when the invocation or repository evidence identifies it unambiguously; if a stacked relationship is indicated but its base is unclear, ask. Use the repository default only when no existing PR or known stack establishes another base. When an existing PR conflicts with the requested target, report it and ask before opening another PR. If a requested target conflicts with a known stacked base, report the conflict and ask before retargeting it.

## Check repository requirements

Read the target repository's root `AGENTS.md`, contribution guidance, pull request template, and relevant GitHub workflow files. Identify the checks those sources require for this change. Read the target branch's protection state, applicable rulesets, and the repository's enabled merge methods and documented merge policy:

```sh
gh api repos/OWNER/REPO/branches/BASE --jq '{name,protected}'
gh api --paginate 'repos/OWNER/REPO/rulesets?includes_parents=true'
gh api repos/OWNER/REPO --jq '{allow_merge_commit,allow_squash_merge,allow_rebase_merge}'
```

If `protected` is true, read its required status checks:

```sh
gh api repos/OWNER/REPO/branches/BASE/protection/required_status_checks
```

If `protected` is false, there is no classic branch protection; still inspect rulesets. Match active rulesets to the exact target branch. Treat permission, network, or incomplete-response errors as unknown; do not infer that checks or rules are absent. Unknown or unavailable check requirements block this entry and its dependents from any source-branch push or PR creation/update; continue with independent entries. Run only required local checks named by repository instructions; a failed, unknown, or unavailable required precheck blocks this entry and its dependents, while independent entries continue. Once a PR exists, compare its results with the required checks using `gh pr checks NUMBER --repo OWNER/REPO`. Pending, failed, or unknown required checks block that PR and its dependents; continue with independent approved PRs.

## Reuse or prepare the PR

Before drafting new PR title or body text, pass the durable-project-text language rule from the root `AGENTS.md` of the repository that will own the PR to `/conventional-git-messages`. If the target differs from this skill's source repository, do not use the source or installation `AGENTS.md` as target policy; if both are the same repository, use its root file as the target policy. Preserve untouched existing PR text; use the target language only for new or materially revised passages and report a resulting language mixture.

From the PR candidates gathered above, match the exact source repository, source branch, and resolved base. If exactly one matching open PR exists, reuse it, even when matching merged PR history also exists. If multiple matching open PRs exist, report the candidates and ask. If no matching open PR exists and exactly one matching PR has `state=MERGED`, verify it with `gh pr view NUMBER --repo OWNER/REPO --json state,mergedAt,headRepository,headRefName,headRefOid,baseRefName`; require the returned repository, head branch, and base branch to still match, plus `state=MERGED`, a non-null `mergedAt`, and `headRefOid` equal to the recorded source OID, then mark the entry completed without pushing or creating or updating a PR. If the merged PR's head OID differs from the source OID, block the entry, report both OIDs, and ask before opening another PR; do not mark the entry completed. If the merge or identity cannot be verified, block the entry and report the uncertainty. If multiple remaining matches make the result ambiguous, report the candidates and ask. If only a closed unmerged or differently based PR exists, report the candidates and ask before opening another. Do not create a duplicate.

Only an explicit request to prepare or create this PR authorizes pushing the supplied source branch or creating/updating that exact PR. An inspection or drafting request stays read-only; report any source-branch mismatch without publishing it.

After required local checks, recheck `git status --porcelain=v1 --untracked-files=all`. Repeat this check immediately before any push, PR creation, or PR edit. If a check leaves the worktree dirty, stop without publishing or cleaning it.

Before creating or updating a PR, compare local `HEAD` with the exact source branch published on GitHub. Fetch it with `git fetch REMOTE HEAD_BRANCH`. For an existing PR, confirm the fetched OID matches its `headRefOid`; if not, reload the PR and ask if they still disagree. Distinguish a missing source ref from authentication or network errors; treat an unknown result as a blocker. If no source branch is published and there is no existing PR candidate, push only the supplied branch normally. If a PR candidate exists but its source branch is unpublished, stop and ask. If local HEAD is strictly ahead, push only that branch with a normal fast-forward push. If the published branch is ahead or the histories diverge, stop and ask; never force-push or rewrite. After a push, reload the PR candidates and verify the published source head. If a PR already exists, reload its head OID, diff, and checks. If creating a new PR, create it next and use the shared post-create verification below.

The only push command is:

```sh
git push REMOTE HEAD:refs/heads/HEAD_BRANCH
```

Immediately before drafting or materially updating a PR title or body, read and follow `/conventional-git-messages`. Read the current diff and the repository's PR title and description guidance. Delegate title and body drafting to `/conventional-git-messages`, supplying those sources, the change facts, and recent same-type PR examples. Follow that skill's rules; ask when required facts or prefix conventions are unclear. Update an existing PR's text only when it is inaccurate, materially incomplete, or clearly inconsistent with current repository guidance. Consider `/show-me` or `/archify` only when a diagram materially improves clarity and an accessible skill is available; otherwise omit it.

After synchronizing the source branch as above, create a new PR with the resolved head, base, title, and body:

```sh
gh pr create --repo OWNER/REPO --head HEAD_BRANCH --base BASE --title "TITLE" --body-file BODY_FILE
```

Pass the title and `BODY_FILE` path as single arguments using the active shell's quoting rules. Write the exact multiline body to a temporary UTF-8 file.

For a fork head, pass `OWNER:HEAD_BRANCH` to `--head`. If `gh pr create` cannot represent the exact source owner, stop and ask rather than using another head.

For an existing exact match, reuse it and update only fields that need correction with `gh pr edit NUMBER --repo OWNER/REPO`. Pass `--title` as one shell argument and `--body-file BODY_FILE` for an updated body; omit unchanged fields.

For every created or reused PR, read its head and base names and OIDs with gh pr view, and read its diff and required checks with gh pr diff and gh pr checks. Return each PR link, head and base names and OIDs, relevant diff, and required-check results. Record a separate approval snapshot for each PR, then pause for review. Do not merge yet.

## Merge after approval

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
