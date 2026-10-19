# Issue text

## Issue titles

- Reuse the [pull request title rules](pull-request-text.md#pull-request-titles) for the Conventional Commit format, type, scope, breaking `!`, capitalization, imperative summary, and punctuation.
- Resolve issue-title prefixes from explicit repository guidance that applies to issues, then same-type issue titles supplied in context. Do not infer an issue prefix from PR titles or commit subjects.
- Add an issue prefix only when that evidence supports it. If evidence conflicts, is stale, or is too sparse to establish the convention, ask a brief question. If no issue prefix convention is evident, omit it.
- Do not apply commit-specific title-length or body-wrapping limits.

## Issue descriptions

- Use the shortest useful structure for the reported problem and supplied context. Add sections only when they clarify the issue or the user requests them; do not use a fixed template or commit-specific numeric limits.
- In a full description, explain the supplied impact of breaking changes, security fixes, data migrations, and reverts, including relevant mitigation or follow-up. Ask for missing facts instead of inventing them.
- If the user asks for a title only, return only the title.

## Issue comments

- Draft concise comments from the supplied issue discussion.
- Return copy-ready text; never post the comment.
