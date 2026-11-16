# First-run tracker migration

Use this GitHub migration only when summary-first issue reads are enabled and
at least one legacy default is present. If any is present, all three must match
exactly once by their full content. Stop if any is missing, duplicated, or
materially changed. If none is present, do not migrate the tracker.

## Remove these legacy defaults

```Markdown
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
```

```Markdown
Run `gh issue view <number> --comments`.
```

## Replace them with these pointers

Replace the two read/list bullets with this one bullet:

```Markdown
- **Read or list issues**: follow [Issue operations](#issue-operations) for summary fields, body and comment escalation, and pagination.
```

Replace the repeated full-read command with this sentence:

```Markdown
Follow [Issue operations](#issue-operations) before reading a ticket.
```
