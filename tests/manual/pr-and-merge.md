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

## PR-text preflight before the first push

In a disposable repository, prepare a new PR from a source branch that needs
a push. Run one case with a required drafting prerequisite unavailable and
another with a required change fact missing. Confirm each case blocks before
any source-branch push and reports the exact missing item and recovery action.

For a ready case, provide all required change facts and repository guidance.
Confirm the skill uses the current diff, target-repository PR guidance,
supplied facts, and relevant same-type examples to prepare the title and body
with the /pr Summary, Evidence, and Merge Danger template. Confirm it invokes
/pr before drafting the body. Inspect the run order and confirm the complete
draft is ready before the first push; the
preflight itself performs no push and does not create or edit a PR.

In another disposable run, advance the published source branch after the
initial comparison but before the final write-time check (for example, while
the title and body are being prepared). In a separate run, advance local
`HEAD` or switch the current branch after preparation. In a third run, advance
the remote again after a successful source push but before the PR write-time
fetch. Confirm the changed OID or branch identity is reported and no push or
PR write uses the old snapshot.
The workflow must recheck required local checks, reclassify, and repeat any
required text preparation before continuing, or stop if the source identity
no longer matches or the new state blocks progress.

Repeat with an exact matching open PR whose text is accurate, then with text
that needs correction. Confirm accurate text is reused and any required
correction is prepared before the push. Run another PR-preparation entry with
no matching PR whose source branch is published at the same OID as local
`HEAD`; confirm the read-only comparison classifies it as no-push, skips the
pre-push gate, and leaves any needed draft ready before PR creation.
Also confirm merge-only entries and completed exact matches for merged PRs
skip this preflight, and an explicit choice not to push remains unchanged.

## Reuse an existing matching PR

Create an open PR for the exact source branch with a non-default base. Add a
commit to the supplied local branch without publishing it, and make the PR
title or body stale. Ask the skill to prepare that branch again without
naming a target.

Confirm the needed title or body correction is prepared before the push.
Then confirm it pushes only that branch normally, refreshes the PR head,
diff and checks, preserves the existing base, reuses the exact open PR, and
updates only inaccurate PR text using repository evidence and
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

## Base-repository permission gate immediately before merge

Run these cases through the user-visible `/pr-and-merge` invocation in a
disposable GitHub repository. For positive cases, provide explicit approval for
the exact PR; the skill may merge it after all live gates pass. Apply the
canonical [merge permission gate](../../skills/pr-and-merge/references/merge-after-approval.md#merge-permission-gate)
for permission mapping, retry budgets, rate-limit waits, status classification,
and renewed-approval rules. This scenario supplies controlled inputs and records
observations only.

### Controlled-response shim

Supply controlled responses through a temporary `gh` executable created outside the reviewed repository. On POSIX create an executable `gh`; on Windows create `gh.cmd`. Select a non-secret case selector such as `PR_MERGE_SHIM_CASE`; store the selected plan and response fixtures only in the temporary run directory. Do not make the wrapper inspect credentials, tokens, or the real `gh` configuration. Capture the real executable path before changing `PATH`, pass it as `PR_MERGE_REAL_GH`, and forward every invocation whose exact API path is not in the selected case to that executable with the original arguments unchanged. Forwarded commands include the live `gh pr view`, `gh pr checks`, and `gh pr merge` gates; only the exact permission-gate API paths named by the case are controlled.

The plan is JSON. Each case maps an exact invoked API path to an ordered list of response fixtures, so entries A and B have independent counters in one batch. Each fixture supplies `stdout`, `stderr`, and `exit_status`; relative fixture paths resolve under the shim directory. The dispatcher consumes the next fixture for the exact path and repeats the last fixture after the sequence ends. For `transient-then-positive`, the permission route lists a 503 fixture first and an ADMIN fixture second. For `batch-isolation`, entry A's permission route lists READ while entry B's distinct base-repository permission route lists ADMIN; only entry B's later `gh pr merge` reaches the real executable. Run entries sequentially and use one shim directory per invocation.

```powershell
$shimDir = Join-Path ([IO.Path]::GetTempPath()) "pr-merge-gh-$([guid]::NewGuid())"
$null = New-Item -ItemType Directory -Path $shimDir
$env:PR_MERGE_REAL_GH = (Get-Command gh -CommandType Application -ErrorAction Stop).Source
$env:PR_MERGE_SHIM_PLAN = Join-Path $shimDir "plan.json"
$env:PR_MERGE_SHIM_CASE = "<case>"
$originalPath = $env:PATH
$env:PATH = "$shimDir$([IO.Path]::PathSeparator)$originalPath"
try {
    # Write plan.json, response fixtures, gh_shim.py, and gh.cmd or gh here.
} finally {
    $env:PATH = $originalPath
    Remove-Item -LiteralPath $shimDir -Recurse -Force
}
```

```json
{
  "transient-then-positive": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-503.json", "permission-admin.json"]
  },
  "batch-isolation": {
    "repos/OWNER-A/REPO-A/pulls/12": ["a-pull.json"],
    "user": ["user.json"],
    "repos/OWNER-A/REPO-A/collaborators/USER/permission": ["permission-read.json"],
    "repos/OWNER-B/REPO-B/pulls/13": ["b-pull.json"],
    "repos/OWNER-B/REPO-B/collaborators/USER/permission": ["permission-admin.json"]
  }
}
```

On POSIX capture `PR_MERGE_REAL_GH="$(command -v gh)"` before prepending the shim directory, write the dispatcher below to `gh`, and run `chmod 700 "$shimDir/gh"`. On Windows write the same dispatcher to `gh_shim.py` and create this `gh.cmd` beside it:

```bat
@echo off
python "%~dp0gh_shim.py" %*
```

Use this dispatcher, or an equivalent that preserves the same route and forwarding contract:

```python
#!/usr/bin/env python3

import json
import os
import pathlib
import subprocess
import sys

shim_dir = pathlib.Path(__file__).resolve().parent
real_gh = os.environ["PR_MERGE_REAL_GH"]
case_name = os.environ["PR_MERGE_SHIM_CASE"]
plan = json.loads(pathlib.Path(os.environ["PR_MERGE_SHIM_PLAN"]).read_text(encoding="utf-8"))
args = sys.argv[1:]

def api_route(arguments):
    for argument in arguments:
        if argument == "user":
            return argument
        if argument.startswith("repos/") and ("/pulls/" in argument or argument.endswith("/permission")):
            return argument
    return None

route = api_route(args)
responses = plan[case_name].get(route) if route else None
if not responses:
    raise SystemExit(subprocess.run([real_gh, *args]).returncode)

state_path = shim_dir / "state.json"
state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
index = state.get(route, 0)
fixture = pathlib.Path(responses[min(index, len(responses) - 1)])
if not fixture.is_absolute():
    fixture = shim_dir / fixture
state[route] = index + 1
state_path.write_text(json.dumps(state), encoding="utf-8")
response = json.loads(fixture.read_text(encoding="utf-8"))
sys.stdout.write(response.get("stdout", ""))
sys.stderr.write(response.get("stderr", ""))
raise SystemExit(response.get("exit_status", 0))
```

Prepend only the shim directory to `PATH` for the invoked process; do not change a shell profile, user or machine environment, or repository file. After the run, confirm the original `PATH` is restored, the temporary directory is removed, and a later `gh --version` resolves to the real executable.

### Permission fixtures

- For denied cases, create a PR from a disposable fork into its upstream
  repository. Give the current `gh` user WRITE on the fork and READ or TRIAGE on
  the upstream base. Confirm the lookup uses `.base.repo.full_name` and the base
  role blocks the PR without invoking `gh pr merge`.
- For positive cases, create a PR whose base repository grants the current `gh`
  user ADMIN, WRITE, or MAINTAIN. Use that merge-capable base for controlled
  positive responses so the approved merge can complete and be verified.
- For every executed case, record the base repository, login, controlled
  response, result category, started-check count, pause or retry decision,
  refreshed pre-merge gates, and whether `gh pr merge` was invoked.

| Case | Controlled input | Expected observation |
| --- | --- | --- |
| Positive | A controlled response that yields ADMIN, WRITE, or MAINTAIN, including a custom role name | Positive result; record the started-check count; refreshed pre-merge gates; merge allowed only with the exact PR approval; verify the post-merge result |
| Denied | A controlled response that yields READ or TRIAGE | READ or TRIAGE; entry blocked immediately; no retry prompt; `gh pr merge` not invoked |
| Inconclusive | Empty or malformed evidence, a missing base or identity, 404, `permission=none`, conflicting fields, or an unmappable custom value | Inconclusive; pause and ask retry or skip; no automatic retry; `gh pr merge` not invoked |
| Transient | A recognizable timeout, reset, or retryable HTTP response | Transient result; automatic checks stay within the canonical budget; waiting consumes no check; after the budget, pause and ask; merge only after a later positive result and refreshed gates |
| Exhausted budget | The canonical automatic budget ends without a positive result or known denial | Pause and ask whether to authorize an extra check or skip; start no further automatic check |
| User-authorized retry | A user-authorized extra check returns positive, READ/TRIAGE, or inconclusive | Positive may proceed after gate refresh; READ/TRIAGE blocks; inconclusive pauses again; skip never merges |
| Rate-limit wait | A primary or secondary limit within the canonical auto-wait window, a longer delay, and a secondary limit without timing headers | Within the window: wait, refresh gates, and continue within the budget; longer: pause with the earliest safe time and make no call before it; no headers: apply the canonical backoff; waits consume no check |
| Authentication or access failure | A 401/403 without rate-limit evidence, or an identity or configuration lookup failure | Pause and ask retry or skip; after a retry, refresh gates before the extra check; a definite denial blocks; skip never merges |
| Batch isolation | Independent positive entry B beside denied or inconclusive entry A and dependent entry C stacked on A | A and C blocked; B continues and may merge under its own approval and live gates; `gh pr merge` not invoked for A or C |

For every denied or inconclusive result, confirm `gh pr merge` is never
invoked, including after automatic retries, rate-limit waits, and skipped or
inconclusive user-selected extra checks. Confirm the observed result category,
started-check count, pause or retry decision, refreshed pre-merge gates, and
merge invocation for each executed case.

## Conflict resolution and second approval

Create a branch that conflicts with its target. Prepare its PR, then approve that exact PR for merging. Run conflict resolution in an explicitly supplied, clean worktree for the exact repository and source branch.

Confirm the run follows the linked canonical [conflict-resolution approval](../../skills/pr-and-merge/references/merge-after-approval.md#conflict-resolution-approval) and record each boundary outcome: it pauses before staging or any write with the complete unstaged diff and check results; after approval, the staged write set matches the approved diff; a changed staged diff pauses before commit, push, or merge; and a later head or base OID change requires renewed approval before merging.

## Multi-PR batch: ordering, stacked retarget, and failure isolation

Prepare three clean worktrees in one test repository: branch A and branch B independently target the same base with disjoint changed paths, and branch C is explicitly stacked on branch A. Supply them in the order C, B, A in one /pr-and-merge invocation. Confirm the workflow presents one exact batch plan and requests one authorization for its listed writes. For each planned merge, name the exact PR and head/base names and OIDs; this authorizes each listed merge while live per-PR checks remain active. Confirm it creates or reuses one exact PR per eligible source and does not pause again for a merge already listed in the authorized batch. The workflow processes dependency-ready work in order: A must precede C, while conflict-free B is considered before conflict-free A by input order.

In a separate batch, select three independent PRs against the same base: A and B have overlapping changed paths, while C has disjoint paths. Supply them in the order A, C, B. Confirm C is prepared and merged before A and B despite the supplied order, and A remains before B within the conflict-candidate group. The merge phase must preserve the same computed order as preparation.

Confirm branch A merges under its listed batch authorization. Branch C is retargeted from A to A's former base, then its head and base OIDs, diff, mergeability, reviews, and required checks are refreshed. If the target base ref changes or new conflict-resolution work is required, confirm the workflow refreshes the plan and obtains renewed authorization before C's next write. Branch B remains independent and can proceed under the same batch authorization if it was listed and its live gates pass.

In a separate batch, supply a dirty branch D, branch E explicitly stacked on D, and a clean independent branch F. Confirm D and dependent E are blocked without publishing them, while F continues through its own prechecks and PR preparation. Repeat with a required check failing for one entry if the test repository can configure that check; confirm only that entry and its dependents stop.

## Multi-PR batch: post-merge verification

In a disposable repository, prepare two or more clean PRs that target the same base and supply one specified test command for the batch. In the first merge pass, confirm one pull request is confirmed as merged while another remains pending or blocked. At the end of that pass, fetch the target branch from its remote and use the fetched base OID to create a new retained worktree; run only the specified test command there. The report must include the base ref, tested commit, retained worktree path, exact command, and observed exit status; label coverage as partial and identify the unresolved entry. Resume the batch without another merge and with the same base ref and OID; confirm the completed result for that base ref and OID is not rerun solely because the batch resumed. Then merge another PR in a later pass; confirm the new resulting base commit is fetched and verified separately in a new retained worktree. Keep each verification outcome separate from each PR's merge status. For failed commands, confirm it includes a concise relevant output excerpt when available and records a reason for every test not run. Report verification as passed only after observing a successful exit status.

Repeat the same single-base batch with no test commands. Confirm the workflow asks before running any test command, runs no inferred default command, and keeps the confirmed PR merge outcome separate from the missing-test-command decision.

## Multi-PR batch: multiple target bases

In a disposable repository, prepare at least two PRs for each of two distinct
target bases, such as `main` and `release`, and specify one test command
confirmed to apply to both. Run the user-visible `/pr-and-merge` invocation and
follow the canonical [verify each distinct target
base](../../skills/pr-and-merge/references/multi-pr-batch.md#verify-each-distinct-target-base)
for fetching, retained worktrees, command execution, result tracking, and
failure isolation.

In the first merge pass, confirm one PR targeting each base is merged while
other entries remain pending or blocked. For each base, record the base ref,
tested commit OID, validation provenance (`reused` or `newly executed`), a
separate retained worktree path, exact command and observed exit status,
coverage status, and every unresolved entry. Mark overall coverage as partial
while any entry remains unresolved. A newly advanced base OID is newly executed.

Repeat with the command's applicability to `release` unclear. Confirm the
workflow asks before running a test command when its applicability to a base is
unclear, records the not-run reason, and does not report that base as passed.
Confirm each failed command includes a concise relevant output excerpt when
available; give a reason for every test not run, and report a test as passed
only after observing a successful exit status.

Resume the batch and merge one more entry for each base. Confirm each new
resulting base commit is reported as newly executed and verified separately in
a new retained worktree. Confirm a completed same-base and same-OID validation
is not rerun solely because the batch resumed; report its provenance as reused.
Allow a same-commit rerun only on explicit user request or to retry a blocked or
interrupted attempt after its cause is resolved. Keep validation outcomes
separate from PR merge states. Do not execute this scenario outside a disposable
repository.

## Multi-PR batch: post-merge validation failure isolation

In a disposable repository, prepare merged PRs on two independent bases and specify multiple test commands confirmed to apply to both. Make one command report an ordinary test failure on one base. Confirm the failed command and relevant output are recorded, while every remaining confirmed command for that base and validations on the other independent base continue.

In a separate run, cause verification worktree creation to fail locally for one base. Confirm that base is reported as `validation_blocked`, each affected command is listed under `tests_not_run` with its reason, and validation continues on the other base. Repeat with a test-preparation failure confirmed local to one base.

In another run, simulate a known shared runner or setup failure after validation has started. Confirm no new validations start, already-running commands finish or time out, and the report includes their outcomes and every test not run with its reason.

In a separate unknown-scope run, confirm new validations pause across all bases. The report must include the uncertainty, evidence needed to classify it, commands still running, and confirmed tests not started. Start no validation until an operator classifies the failure; if classified as local to one base, resume validation on unaffected bases and retry that base only after its cause is resolved; if classified as shared, wait until the shared failure is cleared. In every run, keep validation outcomes separate from PR merge outcomes.

## Complete batch outcome summary

In a disposable repository, supply six entries in one batch: A's repository, source branch, and resolved base exactly match an already merged PR, and A's current source OID matches that PR's head OID; B and E are independent open PRs with passing checks; C has a failing required check; D's exact existing PR targets C; and F is a closed unmerged PR. In the initial scope report, confirm A and F are report-only with no planned writes. At the batch authorization plan, confirm B and E are pending and C and D are blocked. List B's exact PR/head/base merge in the plan and authorize that write set once; leave E's merge unapproved. Execute B's listed merge without a second approval prompt, then inspect the final stop summary: A and B are completed, F remains report-only, E is pending, and C and D remain blocked.

At every summary boundary, confirm every source appears exactly once with its repository and branch/worktree, and its PR link when one exists. Give B and E their own waiting reason and head/base names and OIDs at the initial batch plan; do not combine entries. One authorization covers only the listed actions and exact merge snapshots, so do not ask again for a listed merge. In the final summary, verify E remains pending with its own current head/base names and OIDs. Give C its failed-check reason and D the unmet prerequisite C. Repeat with C's required check pending and then unknown/unavailable; in both runs, C and D must be blocked with the exact check state or uncertainty reported. No unapproved PR is merged.

Also test a source with one matching merged PR and one matching open PR for the same repository, source branch, and base. Reuse the open PR, classify the entry as pending with its own approval snapshot, and do not mark it completed based on the merged history.

Advance a source branch after its matching PR is merged. On the next batch, verify the old PR's `headRefOid` differs from the recorded source OID, report both, and classify the entry as `blocked` until the user decides whether to prepare a new PR; do not mark the newer source `completed`.

## Multi-PR batch: exact worktree match and dirtiness

For a PR requiring conflict resolution, provide a clean worktree for the exact repository and source branch, a clean worktree for the same repository on a different branch, and a clean worktree for a different repository on the same branch. Confirm only the exact repository-and-branch match is reused. Repeat with the exact-match worktree containing a modified file and then an untracked file; confirm the operation is blocked and the worktree is left untouched.

## Other hosting platform

Invoke the skill for a repository hosted outside GitHub.

Confirm it says in one sentence that the invoking agent handles that platform and adds no provider-specific workflow.
