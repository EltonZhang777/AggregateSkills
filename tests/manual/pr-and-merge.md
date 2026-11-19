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

Keep the shim active for the complete user-visible `/pr-and-merge` invocation. Set up the shim in a dedicated PowerShell process or an isolated test host, start the complete invocation from a child of that process (or import the same four variables into the isolated host process), capture the observations, and only then restore the environment and clean up. A setup block that exits before the invocation starts is invalid.

The plan is JSON. Each case maps an exact invoked API path to an ordered list of response fixtures. State is keyed by the exact route, so entries that use the same route consume one ordered queue. Each fixture supplies `stdout`, `stderr`, and `exit_status`; relative fixture paths resolve under the shim directory. The dispatcher consumes the next fixture for the exact path and repeats the last fixture after the sequence ends. For `transient-then-positive`, the permission route lists two 503 fixtures followed by an ADMIN fixture. For `batch-isolation`, entries A, B, and dependent C use the same exact repository; reuse the same shim directory and state across entries A, B, and C. A receives READ and B receives the next ADMIN response on the shared permission route. Do not reset `state.json` between A and B.

Create a distinct open merge-capable PR for each positive case and replace `OWNER`, `REPO`, `USER`, and each PR number with the actual disposable-repository values before writing the plan. Do not reuse a PR after a positive case has merged it.

```powershell
function Invoke-WithPermissionShim {
    param(
        [Parameter(Mandatory)][string]$Case,
        [Parameter(Mandatory)][scriptblock]$PopulateShim,
        [Parameter(Mandatory)][scriptblock]$Workflow
    )

    $shimDir = Join-Path ([IO.Path]::GetTempPath()) "pr-merge-gh-$([guid]::NewGuid())"
    $null = New-Item -ItemType Directory -Path $shimDir
    $names = @('PATH', 'PR_MERGE_REAL_GH', 'PR_MERGE_SHIM_PLAN', 'PR_MERGE_SHIM_CASE')
    $present = @{}
    $previous = @{}
    foreach ($name in $names) {
        $present[$name] = Test-Path -LiteralPath "Env:$name"
        $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }

    try {
        & $PopulateShim $shimDir
        $env:PR_MERGE_REAL_GH = (Get-Command gh -CommandType Application -ErrorAction Stop).Source
        $env:PR_MERGE_SHIM_PLAN = Join-Path $shimDir "plan.json"
        $env:PR_MERGE_SHIM_CASE = $Case
        $previousPath = $previous['PATH']
        $env:PATH = "$shimDir$([IO.Path]::PathSeparator)$previousPath"

        # Start the complete /pr-and-merge invocation here, wait for it to
        # return, and capture its observations before leaving this scope.
        $workflowResult = & $Workflow
        $mergeCalls = if (Test-Path -LiteralPath (Join-Path $shimDir 'merge-calls.log')) {
            @(Get-Content -LiteralPath (Join-Path $shimDir 'merge-calls.log'))
        } else {
            @()
        }
        [pscustomobject]@{ WorkflowResult = $workflowResult; MergeCalls = $mergeCalls }
    } finally {
        foreach ($name in $names) {
            if ($present[$name]) {
                [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process')
            } else {
                [Environment]::SetEnvironmentVariable($name, $null, 'Process')
            }
        }
        Remove-Item -LiteralPath $shimDir -Recurse -Force
    }
}

$record = Invoke-WithPermissionShim -Case "<case>" -PopulateShim {
    param($shimDir)
    # Materialize plan.json, the selected fixtures, the gh or gh.cmd
    # launcher, gh_shim.py on Windows, and any required state.json here.
} -Workflow {
    # Start the complete /pr-and-merge invocation in this process or a child
    # process that inherits this environment; return only after it finishes.
    Read-Host 'Press Enter after the complete /pr-and-merge invocation returns'
}
$record.MergeCalls
```

```json
{
  "positive-admin": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-admin.json"]
  },
  "positive-write": {
    "repos/OWNER/REPO/pulls/13": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-write.json"]
  },
  "positive-maintain": {
    "repos/OWNER/REPO/pulls/14": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-maintain.json"]
  },
  "positive-custom": {
    "repos/OWNER/REPO/pulls/15": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-custom.json"]
  },
  "denied-read": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-read.json"]
  },
  "denied-triage": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-triage.json"]
  },
  "inconclusive-404": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-404.json"]
  },
  "inconclusive-empty": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-empty.json"]
  },
  "inconclusive-missing-base": {
    "repos/OWNER/REPO/pulls/12": ["pull-missing-base.json"],
    "user": ["user.json"]
  },
  "inconclusive-missing-identity": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user-missing-login.json"]
  },
  "inconclusive-none": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-none.json"]
  },
  "inconclusive-conflict": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-conflict.json"]
  },
  "inconclusive-unmappable": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-unmappable.json"]
  },
  "transient-then-positive": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-503.json", "permission-503.json", "permission-admin.json"]
  },
  "timeout-then-positive": {
    "repos/OWNER/REPO/pulls/16": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-timeout.json", "permission-admin.json"]
  },
  "exhausted-budget": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-503.json"]
  },
  "user-authorized-retry": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-503.json", "permission-503.json", "permission-503.json", "permission-admin.json"]
  },
  "rate-limit-auto-wait": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-rate-limit-short.json", "permission-admin.json"]
  },
  "rate-limit-long": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-rate-limit-long.json"]
  },
  "rate-limit-no-headers": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-rate-limit-no-headers.json", "permission-admin.json"]
  },
  "auth-failure": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-auth-failure.json"]
  },
  "batch-isolation": {
    "repos/OWNER/REPO/pulls/12": ["pull.json"],
    "repos/OWNER/REPO/pulls/13": ["pull.json"],
    "repos/OWNER/REPO/pulls/14": ["pull.json"],
    "user": ["user.json"],
    "repos/OWNER/REPO/collaborators/USER/permission": ["permission-read.json", "permission-admin.json"]
  }
}
```

Write each value below to the file named by its key. Each `stdout` is the complete
`--include` output: status line, headers, a blank line, and the JSON body.

```json
{
  "pull.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"base\":{\"repo\":{\"full_name\":\"OWNER/REPO\"}}}\n", "stderr": "", "exit_status": 0},
  "pull-missing-base.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"number\":12}\n", "stderr": "", "exit_status": 0},
  "user.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"login\":\"USER\"}\n", "stderr": "", "exit_status": 0},
  "user-missing-login.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"id\":123}\n", "stderr": "", "exit_status": 0},
  "permission-admin.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"permission\":\"admin\",\"role_name\":\"admin\"}\n", "stderr": "", "exit_status": 0},
  "permission-write.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"permission\":\"write\",\"role_name\":\"write\"}\n", "stderr": "", "exit_status": 0},
  "permission-maintain.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"permission\":\"write\",\"role_name\":\"maintain\"}\n", "stderr": "", "exit_status": 0},
  "permission-custom.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"permission\":\"write\",\"role_name\":\"release-manager\"}\n", "stderr": "", "exit_status": 0},
  "permission-read.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"permission\":\"read\",\"role_name\":\"read\"}\n", "stderr": "", "exit_status": 0},
  "permission-triage.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"permission\":\"read\",\"role_name\":\"triage\"}\n", "stderr": "", "exit_status": 0},
  "permission-404.json": {"stdout": "HTTP/2 404\r\nContent-Type: application/json\r\n\r\n{\"message\":\"Not Found\"}\n", "stderr": "", "exit_status": 1},
  "permission-empty.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n\n", "stderr": "", "exit_status": 0},
  "permission-none.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"permission\":\"none\",\"role_name\":\"none\"}\n", "stderr": "", "exit_status": 0},
  "permission-conflict.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"permission\":\"read\",\"role_name\":\"maintain\"}\n", "stderr": "", "exit_status": 0},
  "permission-unmappable.json": {"stdout": "HTTP/2 200\r\nContent-Type: application/json\r\n\r\n{\"permission\":\"custom\",\"role_name\":\"custom\"}\n", "stderr": "", "exit_status": 0},
  "permission-timeout.json": {"stdout": "", "stderr": "gh: request timed out\n", "exit_status": 124},
  "permission-503.json": {"stdout": "HTTP/2 503\r\nContent-Type: application/json\r\n\r\n{\"message\":\"Service Unavailable\"}\n", "stderr": "", "exit_status": 1},
  "permission-rate-limit-short.json": {"stdout": "HTTP/2 429\r\nContent-Type: application/json\r\nRetry-After: 1\r\n\r\n{\"message\":\"secondary rate limit\"}\n", "stderr": "", "exit_status": 1},
  "permission-rate-limit-long.json": {"stdout": "HTTP/2 429\r\nContent-Type: application/json\r\nRetry-After: 600\r\n\r\n{\"message\":\"secondary rate limit\"}\n", "stderr": "", "exit_status": 1},
  "permission-rate-limit-no-headers.json": {"stdout": "HTTP/2 403\r\nContent-Type: application/json\r\n\r\n{\"message\":\"You have exceeded a secondary rate limit.\"}\n", "stderr": "", "exit_status": 1},
  "permission-auth-failure.json": {"stdout": "HTTP/2 401\r\nContent-Type: application/json\r\n\r\n{\"message\":\"Bad credentials\"}\n", "stderr": "", "exit_status": 1}
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
    if args[:2] == ["pr", "merge"]:
        with (shim_dir / "merge-calls.log").open("a", encoding="utf-8") as stream:
            stream.write("gh pr merge\n")
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
sys.stdout.buffer.write(response.get("stdout", "").encode("utf-8"))
sys.stdout.buffer.flush()
sys.stderr.buffer.write(response.get("stderr", "").encode("utf-8"))
sys.stderr.buffer.flush()
raise SystemExit(response.get("exit_status", 0))
```

Prepend only the shim directory to `PATH` for the invoked process; do not change a shell profile, user or machine environment, or repository file. The function snapshots both the value and presence of all four changed environment variables and restores or unsets each of them in `finally`. Before cleanup, `merge-calls.log` records whether the dispatcher forwarded `gh pr merge` for that case. After the run, confirm the original environment is restored, the temporary directory is removed, and a later `gh --version` resolves to the real executable.

### Permission fixtures

- For denied cases, create a PR from a disposable fork into its upstream
  repository. Give the current `gh` user WRITE on the fork and READ or TRIAGE on
  the upstream base. Confirm the lookup uses `.base.repo.full_name` and the base
  role blocks the PR without invoking `gh pr merge`.
- For positive cases, create a PR whose base repository grants the current `gh`
  user ADMIN, WRITE, or MAINTAIN. Use that merge-capable base for controlled
  positive responses so the approved merge can complete and be verified.
- For every executed case, use the matching fixture sequence below and record
  the base repository, login, controlled response, result category,
  started-check count, pause or retry decision, refreshed pre-merge gates, and
  whether `gh pr merge` was invoked.

The expected observations are fixed, not tester-defined. Any different result,
count, decision, gate refresh, or merge invocation fails that case.

| Case | Fixture sequence | Expected result | Started checks | Decision | Gates refreshed | Merge invoked |
| --- | --- | --- | ---: | --- | --- | --- |
| positive-admin | `permission-admin.json` | positive:admin | 1 | continue | yes | yes |
| positive-write | `permission-write.json` | positive:write | 1 | continue | yes | yes |
| positive-maintain | `permission-maintain.json` | positive:maintain | 1 | continue | yes | yes |
| positive-custom | `permission-custom.json` | positive:write (custom role) | 1 | continue | yes | yes |
| denied-read | `permission-read.json` | denied:read | 1 | block | no | no |
| denied-triage | `permission-triage.json` | denied:triage | 1 | block | no | no |
| inconclusive-404 | `permission-404.json` | inconclusive:404 | 1 | pause | no | no |
| inconclusive-empty | `permission-empty.json` | inconclusive:empty | 1 | pause | no | no |
| inconclusive-missing-base | `pull-missing-base.json` | inconclusive:missing-base | 1 | pause | no | no |
| inconclusive-missing-identity | `user-missing-login.json` | inconclusive:missing-identity | 1 | pause | no | no |
| inconclusive-none | `permission-none.json` | inconclusive:none | 1 | pause | no | no |
| inconclusive-conflict | `permission-conflict.json` | inconclusive:conflict | 1 | pause | no | no |
| inconclusive-unmappable | `permission-unmappable.json` | inconclusive:unmappable | 1 | pause | no | no |
| transient-then-positive | `permission-503.json` x2, `permission-admin.json` | positive:admin after transient | 3 | automatic retry | yes | yes |
| timeout-then-positive | `permission-timeout.json`, `permission-admin.json` | positive:admin after timeout | 2 | automatic retry | yes | yes |
| exhausted-budget | `permission-503.json` (repeats) | transient:exhausted | 3 | pause | no | no |
| user-authorized-retry | `permission-503.json` x3, `permission-admin.json` | positive:admin after authorized retry | 4 | user retry | yes | yes |
| rate-limit-auto-wait | `permission-rate-limit-short.json`, `permission-admin.json` | positive:admin after wait | 2 | wait, continue | yes | yes |
| rate-limit-long | `permission-rate-limit-long.json` | transient:rate-limit-long | 1 | pause until safe time | no | no |
| rate-limit-no-headers | `permission-rate-limit-no-headers.json`, `permission-admin.json` | positive:admin after backoff | 2 | backoff, continue | yes | yes |
| auth-failure | `permission-auth-failure.json` | access-failure | 1 | pause | no | no |
| batch-isolation A | `permission-read.json` | denied:read | 1 | block A and C | no | no |
| batch-isolation B | next `permission-admin.json` on the shared route | positive:admin | 1 | continue | yes | yes |
| batch-isolation C | none | blocked by A | 0 | block | no | no |

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
