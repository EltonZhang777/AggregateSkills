# First-run tracker migration

Detect the state before asking for summary-first reads:

- `unmigrated`: all three legacy defaults occur exactly once, both replacement
  pointers are absent, and the managed issue-operations section is absent.
- `fully migrated`: all three legacy defaults are absent, both replacement
  pointers occur exactly once, and the managed issue-operations section has one
  complete marker pair.
- `ambiguous`: any other missing, duplicated, altered, partial, or mixed state.

Use this GitHub migration only when the state is `unmigrated`.

## Rerun decision matrix

| Detected state | Summary-first reads | Action |
| --- | --- | --- |
| Unmigrated | Enabled | Include the exact migration in the complete draft |
| Unmigrated | Disabled | Preserve the legacy read conventions |
| Fully migrated | Enabled | Replace only the managed issue-operations section |
| Fully migrated | Disabled | Stop before drafting or writing: the existing pointers require the managed summary rules |
| Ambiguous | Either | Stop before drafting or writing with the conflicting evidence |

For an unmigrated tracker, all three legacy defaults must match exactly once by
their full content. Stop if any is missing, duplicated, or materially changed.
For a fully migrated tracker, both pointers and the managed marker pair must be
complete. If none of the recognized states applies, report `ambiguous` and do
not write.

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
