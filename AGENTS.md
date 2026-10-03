## Durable project text language

- For new or materially rewritten natural-language project text, follow only the normative prose in the root
  `AGENTS.md` of the target repository: the repository receiving the text, including the repository that owns a
  GitHub issue or pull request. When source and target repositories differ, do not use source-repository or
  skill-installation instructions as the target policy. When they are the same repository, its root file is the
  target policy. Nested `AGENTS.md` files do not override the target root.
- When compressing existing source documents, preserve the source language sentence by sentence instead of
  normalizing the content to the target repository's language. This is an exception to the rule above for
  compressed source content.
- If the normative prose is mixed and has no discernible dominant language, ask the user before writing.
- Preserve untouched text. When existing text uses another language, apply the rule only to new or materially
  rewritten passages and report any resulting language mixture.
- Spelling-only and formatting-only edits, commit messages, ordinary chat, and read-only analysis or review
  output are outside this rule.

## Agent skills

### Issue tracker

Issues and specs for this repository live in GitHub Issues; use the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the five canonical triage labels documented for this repository. See `docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single-context domain-doc layout. See `docs/agents/domain.md`.
