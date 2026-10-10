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

Immediately before drafting or materially updating a PR title or body, pass the durable-project-text language rule from the root `AGENTS.md` of the repository that will own the PR to `/conventional-git-messages`. If the target differs from this skill's source repository, do not use the source or installation `AGENTS.md` as target policy; if both are the same repository, use its root file as the target policy. Preserve untouched existing PR text; use the target language only for new or materially revised passages and report a resulting language mixture.

From the PR candidates gathered above, match the exact source repository, source branch, and resolved base. If exactly one matching open PR exists, reuse it, even when matching merged PR history also exists. If multiple matching open PRs exist, report the candidates and ask. If no matching open PR exists and exactly one matching PR has `state=MERGED`, verify it with `gh pr view NUMBER --repo OWNER/REPO --json state,mergedAt,headRepository,headRefName,headRefOid,baseRefName`; require the returned repository, head branch, and base branch to still match, plus `state=MERGED`, a non-null `mergedAt`, and `headRefOid` equal to the recorded source OID, then mark the entry completed without pushing or creating or updating a PR. If the merged PR's head OID differs from the source OID, block the entry, report both OIDs, and ask before opening another PR; do not mark the entry completed. If the merge or identity cannot be verified, block the entry and report the uncertainty. If multiple remaining matches make the result ambiguous, report the candidates and ask. If only a closed unmerged or differently based PR exists, report the candidates and ask before opening another. Do not create a duplicate.

Only an explicit request to prepare or create this PR authorizes pushing the supplied source branch or creating/updating that exact PR. An inspection or drafting request stays read-only; report any source-branch mismatch without publishing it.

After required local checks, recheck `git status --porcelain=v1 --untracked-files=all`. Repeat this check immediately before any push, PR creation, or PR edit. If a check leaves the worktree dirty, stop without publishing or cleaning it.

Before deciding whether a source push is needed, compare local `HEAD` with the exact source branch published on GitHub. Fetch it with `git fetch REMOTE HEAD_BRANCH`. For an existing PR, confirm the fetched OID matches its `headRefOid`; if not, reload the PR and ask if they still disagree. Distinguish a missing source ref from authentication or network errors; treat an unknown result as a blocker. If no source branch is published and there is no existing PR candidate, classify a source push as required. If a PR candidate exists but its source branch is unpublished, stop and ask. If local HEAD is strictly ahead, classify a source push as required. If the published branch points to local HEAD, no source push is needed. If the published branch is ahead or the histories diverge, stop and ask; never force-push or rewrite.

### Prepare or reuse PR text

Use this shared procedure for eligible PR-preparation entries. Complete it before a required source push; if no push is needed, complete it before creating or editing the PR. It does not itself push, create, or edit a PR.

Inspect any exact matching open PR against the current diff, target-repository guidance, and supplied change facts. Resolve the facts and conventions needed to verify existing text. Reuse accurate title and body text without rewriting; draft only when there is no matching open PR or a correction is necessary.

Before drafting new or corrected text, resolve all prerequisites declared by /conventional-git-messages, including /pr, /skill-scout, and SkillRoute CLI. Follow /skill-scout's documented resolution flow and selected inventory; inspect the original source of each selected skill before invoking it. If a prerequisite is missing or unresolved, the inventory is incomplete, or a user decision is required, block this entry before any required push or PR write, and report the prerequisite, evidence, and recovery condition. Do not install a dependency or switch discovery modes automatically.

If a draft or correction is needed, resolve its required facts and conventions, then delegate the title and body or only the necessary correction to /conventional-git-messages using the current diff, target-repository PR title and description guidance, supplied change facts, and relevant same-type examples. Follow the target repository's AGENTS.md language rule and the /pr Summary, Evidence, and Merge Danger body template. If any fact or convention needed to verify existing text or prepare a draft is unresolved, stop and report what is missing before any required push or PR write.

### PR-text preflight before the first source push

Run this gate only for eligible entries whose requested outcome includes PR preparation and whose source comparison above classified a source push as required. Skip entries already completed by an exact merged-PR match, merge-only entries, and entries that do not request PR preparation. For an entry classified as needing no source push, skip this pre-push gate but complete the shared text-preparation procedure above before any PR write. Keep the user's existing choice and authorization for the push.

For a required-push entry, the title and body or confirmation that existing text is accurate must be ready before the first source-branch push. This preflight does not authorize a push; follow the existing status and push-authorization gates.

Immediately before any push, PR creation, or PR edit, repeat the clean-worktree check and confirm `git branch --show-current` and `git rev-parse HEAD` still match the source branch and OID recorded above. Run `git fetch REMOTE HEAD_BRANCH` again. Before the first push, or before a PR write on the no-push path, require its published OID (or missing-ref state) to match the initial classification snapshot. After a successful push, require the published OID to equal the recorded source OID before any PR write. For an existing PR, also require its current `headRefOid` to match the fetched OID. If local or remote state changed, stop and redo source/PR classification and any required local checks and text preparation; do not write using stale results. If the branch no longer matches the user-supplied source identity, ask before proceeding. A failed or unknown check blocks the write.

For an entry still classified as requiring a push after the final comparison, use only this normal fast-forward push:

```sh
git push REMOTE HEAD:refs/heads/HEAD_BRANCH
```

After a required push, run `git fetch REMOTE HEAD_BRANCH` again and reload the PR candidates; require the published source head to equal the recorded source OID. For an existing PR, reload its head OID, diff, and checks. If the source branch was classified as needing no push, proceed without pushing. Create a new PR with the resolved head and base and the text prepared for this entry:

```sh
gh pr create --repo OWNER/REPO --head HEAD_BRANCH --base BASE --title "TITLE" --body-file BODY_FILE
```

Pass the title and `BODY_FILE` path as single arguments using the active shell's quoting rules. Write the exact multiline body to a temporary UTF-8 file.

For a fork head, pass `OWNER:HEAD_BRANCH` to `--head`. If `gh pr create` cannot represent the exact source owner, stop and ask rather than using another head.

For an existing exact match, reuse it and update only fields that need correction with `gh pr edit NUMBER --repo OWNER/REPO`. Pass `--title` as one shell argument and `--body-file BODY_FILE` for an updated body; omit unchanged fields.

For every created or reused PR, read its head and base names and OIDs with gh pr view, and read its diff and required checks with gh pr diff and gh pr checks. Return each PR link, head and base names and OIDs, relevant diff, and required-check results. Record a separate approval snapshot for each PR, then pause for review. Do not merge yet.

## Merge after approval

Only when the user requests a merge and explicitly approves that exact PR, read the
[merge-after-approval procedure](references/merge-after-approval.md).
