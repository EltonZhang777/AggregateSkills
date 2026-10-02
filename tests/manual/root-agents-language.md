# Root AGENTS.md language manual scenarios

Use disposable fixture repositories. Keep normal user-confirmation, issue-write,
PR-write, push, and merge gates in place.

## New text with a different conversation language

Set the root AGENTS.md normative prose to English and converse in Chinese.
Ask /grill-duo-with-docs to record a confirmed project term, then ask
/conventional-git-messages for an issue title, description, and comment plus
a PR title, description, and comment.

Confirm new project text and all GitHub drafts use English, while ordinary
conversation remains Chinese.

## Existing text in another language

Keep existing Chinese passages in a project document and an existing PR body.
Ask /grill-duo-with-docs to add a confirmed statement, and ask
/pr-and-merge to materially revise an inaccurate or incomplete PR passage.
Also ask /compress-docs to materially compress prose in a project document
while leaving a separate Chinese passage untouched.

Confirm only new or materially revised passages use English, untouched
passages remain unchanged, and each resulting mixed-language artifact is
reported. For /compress-docs, verify this both after apply and in candidates-only
mode, where the candidate report must mention the mixture. Confirm compressed
candidates still pass all existing compression and protected-content checks.

## Ambiguous root language

Make the root AGENTS.md normative prose evenly mixed between English and
Chinese with no discernible dominant language. Start a documentation write,
an issue or PR draft, and a publishing workflow.

Confirm each pauses before writing or publishing and asks the user. No draft,
file change, issue write, or PR write occurs.

Also run /compress-docs in candidates-only mode on a project-document fixture
with compressible prose. With an ambiguous root, confirm the host asks which
language to use and waits before starting the compressor; no candidate is
returned before the answer. After the user selects English, confirm the
returned candidate's rewritten prose is English and the source file remains
unchanged.

Repeat with the native subagent unavailable. Confirm the host completes the
same language preflight before asking for inline-compression approval. After
the user selects English and approves, confirm the returned candidate uses
English and the source remains unchanged in candidates-only mode.

## Candidate language validation

Set the root AGENTS.md normative prose to English. Simulate a compressor
returning materially rewritten Chinese prose. Confirm the host requests a
targeted repair or rejects that candidate before apply; no wrong-language
candidate is applied.

## Nested language instructions

Set the root AGENTS.md normative prose to English and a nested AGENTS.md to
Chinese. Compress project documentation under the nested directory and confirm
the host preflight and returned candidate use English, following the root file.

## Minor edits and exclusions

Ask for spelling-only and formatting-only edits to an existing Chinese
document. Confirm its language is not normalized. Request a commit message in
Chinese and ordinary conversation or read-only review output in Chinese;
confirm the durable-project-text rule does not change those outputs.

## Rule propagation through workflows

In /requirements-to-spec-tickets, inspect the child prompt and confirm it
passes the root rule to /grill-with-docs, /to-spec, and /to-tickets.
In /spec-implement-loop, confirm the same for those dependencies when
invoked, and confirm any issue status comments follow the rule. In
/grill-duo-with-docs, confirm the rule is passed to
/grill-duo and /domain-modeling. In /pr-and-merge, confirm it is passed
to /conventional-git-messages before title and body drafting.

Confirm generated project text follows the rule, upstream skill sources are
not modified, and normal approval gates remain in force.
