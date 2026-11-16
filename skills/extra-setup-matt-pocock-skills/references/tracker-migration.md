# First-run tracker migration

Detect the state before asking for summary-first reads:

- `unmigrated`: all recognized legacy defaults occur exactly once, every
  reviewed replacement is absent, and the managed issue-operations section is
  either absent or has one complete marker pair.
- `fully migrated`: all recognized legacy defaults are absent, every reviewed
  replacement occurs exactly once, and the managed issue-operations section has
  one complete marker pair.
- `ambiguous`: any other missing, duplicated, altered, partial, or mixed state.

Scan complete HTML comments across line breaks before validation and require
every managed-namespace comment to match the exact one-line marker grammar. A
wrapped, missing, duplicate, reversed, crossed, nested, unclosed, or otherwise
invalid marker sequence is `ambiguous`.

Use this GitHub migration only when the state is `unmigrated`.

## Rerun decision matrix

| Detected state | Summary-first reads | Action |
| --- | --- | --- |
| Unmigrated | Enabled | Include the exact migration in the complete draft |
| Unmigrated | Disabled | Preserve the legacy read conventions; update only an existing managed issue-operations section |
| Fully migrated | Enabled | Replace only the managed issue-operations section |
| Fully migrated | Disabled | Stop before drafting or writing: the existing pointers require the managed summary rules |
| Ambiguous | Either | Stop before drafting or writing with the conflicting evidence |

For an unmigrated tracker, every recognized legacy default must match exactly
once by its full content and no reviewed replacement may appear. Stop if any
known fact is missing, duplicated, mixed, or materially changed. For a fully
migrated tracker, every reviewed replacement and the managed marker pair must be
complete. If none of the recognized states applies, report `ambiguous` and do
not write.

Unchanged legacy reads with one complete managed issue-operations section are a
valid summary-disabled first run. Keep that state `unmigrated`, and update only
the managed section on a consistent rerun. A later summary-first opt-in applies
the exact migration below once, then produces `fully migrated`; it never creates
a duplicate replacement or a second managed section.

## Remove these recognized legacy defaults

```Markdown
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
```

```Markdown
Run `gh issue view <number> --comments`.
```

```Markdown
- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` then keep only `authorAssociation` of `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE` (drop `OWNER`/`MEMBER`/`COLLABORATOR`).
```

```Markdown
GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.
```

```Markdown
- **Frontier query**: list the map's open children (`gh issue list --state open`, scoped to the map's sub-issues / task list), drop any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
```

## Replace them with these reviewed reads

Replace the two read/list bullets with this one bullet:

```Markdown
- **Read or list issues**: follow [Issue operations](#issue-operations) for summary fields, body and comment escalation, and pagination.
```

Replace the repeated full-read command with this sentence:

```Markdown
Follow [Issue operations](#issue-operations) before reading a ticket.
```

Replace the pull-request read and triage-list bullets with these:

```Markdown
- **Read a PR**: use summary-only `gh pr view <number>` from [Issue operations](#issue-operations); request a full body, comments, or `gh pr diff <number>` only for a named triage need.
- **List external PRs for triage**: use `gh pr list --state open --limit <bound> --json number,title,state,labels,assignees,updatedAt,url,authorAssociation`, keep only `authorAssociation` values `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE`, and paginate or narrow the query when the bound is reached.
```

Replace the bare-number routing sentence with:

```Markdown
GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve it with summary-only `gh pr view <number>` and fall back to summary-only `gh issue view <number>` from [Issue operations](#issue-operations). Request the full body or comments only after this summary identifies the routing need.
```

Replace the Wayfinding frontier bullet with:

```Markdown
- **Frontier query**: use `gh issue list --state open --limit <bound> --json number,title,state,labels,assignees,updatedAt,url`, scoped to the map's sub-issues or task list. Drop any child with an assignee. For each remaining child, read only `gh issue view <number> --json number,state,blockedBy`; drop any open `blockedBy` entry or open issue in a `Blocked by` fallback line. First in map order wins.
```
