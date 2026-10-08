# Commit messages

## Commit subject

- Use `<type>(<scope>): <imperative summary>`; omit the scope when it adds no useful context.
- Supported types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`, `style`, and `revert`.
- For a breaking change, put `!` before the colon, such as `feat(api)!:`.
- Match capitalization after the colon to explicit repository guidance, then recent commit subjects supplied in the context. Ask if the convention is unclear or conflicting. Never run Git commands to inspect history.
- Prefer 50 characters or fewer when the meaning stays clear. Never exceed 72 characters.
- Use an imperative summary and no trailing period.

## Commit body

- Omit the body when the subject fully explains a self-contained change.
- Add only useful, non-obvious rationale, breaking-change context, migration notes, or issue references.
- Always include a body for breaking changes, security fixes, data migrations, and reverts. For breaking changes, explain compatibility impact under `BREAKING CHANGE:` and give the supplied migration path. Preserve supplied impact and migration details; do not invent them.
- Wrap body lines at 72 characters. Use `-` for bullets.
- Put supplied issue or pull request references at the end, for example `Closes #42` or `Refs #17`.
- Do not write filler such as `This commit does`, `I`, `we`, `now`, or `currently`; do not repeat a filename already conveyed by the scope.
- If the user requests co-author credit, use a `Co-authored-by:` trailer instead of prose such as `As requested by...`. Do not invent author details.
- Do not add emoji or AI attribution unless the user or repository rules require it; if required, use the specified trailer.
