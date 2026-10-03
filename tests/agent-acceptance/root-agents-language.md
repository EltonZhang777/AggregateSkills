# Root AGENTS.md language acceptance

Run one fresh native subagent for each request. Give each subagent only the installed skill under test, the fixture request, and the target repository's root `AGENTS.md`; include a conflicting nested `AGENTS.md` only in the scenario that tests root precedence. Do not provide AggregateSkills' source-repository `AGENTS.md`. Use disposable fixture content and prohibit file writes and external service actions. For `/compress-docs`, the isolated worker returns only candidate text as its skill requires; the host supplies the conversation-facing report. For ordinary writing requests, ask for JSON containing the generated artifact and report; for ambiguous-policy requests, ask for an empty artifact and a clarification question. Keep the captured responses in `results.json` and run `check_language_policy.py` against it. The checker inspects generated text; a subagent's claim that it passed is not evidence.

## Compression content and report language

Use a target-root policy that requires English for new project text and explicitly exempts compressed source
content, which keeps its sentence-by-sentence source language. Keep the conversation in Chinese. Ask one isolated
`/compress-docs` compression worker to shorten this project document:

```markdown
# Language notes
The service checks the current account status before it saves the request.
The account is suspended.
As a result, the service rejects the request.
账户暂停时，系统会拒绝该请求。
账户已暂停。
因此，服务拒绝该请求。
The transition is unclear. 这句附近缺少语言线索。
`Service.validate()`
```

Ask the worker to keep each source sentence on its own line, compress where useful, and preserve sentence language rather than exact wording. Keep the unclear mixed-language sentence unchanged. Store its candidate and a Chinese host report without embedded English words as `compression_mixed`. The report must explicitly mention that the result contains both English and Chinese. Check that the document is shorter in UTF-8 bytes, the heading and inline code are unchanged, each rewritten English sentence is English, each rewritten Chinese sentence is Chinese, both causal links remain in their source language and with the effect they introduce, and no connector was added to the unclear mixed sentence. Reject negative regression examples that negate the pre-save account-status check or claim the account is not suspended. Equivalent causal wording is allowed.

In a separate subagent request, reuse the source-preserving compression exception but set the target-root rule for new project text to Japanese. Compress the English source `The guide stores all user-visible labels in a central map.` while keeping the conversation in Chinese. Compression preserves English source content, while the host report uses Chinese; these three language roles must remain distinct. Store the candidate and a Chinese host report with no embedded English words as `compression_report`, with fixture languages `{"target":"Japanese","source":"English","conversation":"Chinese"}`. Check that the candidate is shorter and uses English, while the report uses Chinese.

Also simulate compressing a standalone, non-project `notes.txt` containing `缓存失效后，应按顺序恢复各项设置。该文件面向独立用户，不应翻译。` Set the target repository policy to English and the conversation language to English. Store the candidate and an English host report as `compression_nonproject`; check it is shorter, contains the Chinese source terms `缓存`, `恢复`, and `设置` without Latin letters or Japanese kana, and the report is in English. This verifies source-language validation also applies outside project documentation.

## Target-repository policy for project text

Use one isolated subagent for each skill below. Give each an English target-root rule, an existing Chinese passage `已有说明：保留这段中文。`, and a Chinese conversation. Ask for a small new or materially revised project-text artifact and a one-sentence Chinese chat-facing report; a common acronym such as PR may appear naturally. Simulations must not publish or modify anything.

- `/conventional-git-messages`: draft an issue title and body.
- `/grill-duo-with-docs`: record one already-confirmed project statement in `docs/decisions.md`. For this simulation, the target root requires English and `docs/AGENTS.md` requires Chinese; the new statement follows the root rule. Record these fixture languages in the result JSON.
- `/pr-and-merge`: draft a PR title and body, and naturally refer to the PR in the Chinese report.
- `/requirements-to-spec-tickets`: produce a child prompt and a spec issue draft. The checker inspects the issue draft as project text and separately checks that the prompt carries the target-root rule without relying on AggregateSkills' source `AGENTS.md`.
- `/spec-implement-loop`: draft an issue status comment.

Give each subagent only its installed skill and the target fixture; for these five cases, the AggregateSkills source-root file is unavailable. For every result, check that the existing Chinese passage is unchanged, all new or materially revised project prose follows the English target rule, and the report is Chinese. A completed artifact from each isolated run verifies that the simulation did not require the source repository's `AGENTS.md`.

## Same repository as the skill source

Run one additional isolated `/conventional-git-messages` request where both the skill source and the issue's target repository are AggregateSkills. Provide the shared root `AGENTS.md` language rule as the target policy; its normative language is English. With a Chinese conversation and the existing passage `已有说明：保留这段中文。`, draft an English issue title and body that preserve the passage, plus a Chinese report. Return `same_repo` with `artifact`, `report`, and `languages: {"target":"English","skill_source":"English","conversation":"Chinese"}`. This checks that source-policy exclusion applies only when source and target differ.

## Ambiguous target policy

Set target-root normative prose to an even English/Chinese mix with no discernible dominant language. Start one isolated subagent request for each of the five named project-text skills above, asking for the artifact relevant to that skill. Each response returns an empty artifact and a Chinese clarification question. Check that every skill asks which language to use before drafting.

## Checker input

Combine the fourteen subagent responses into one JSON object:

```json
{
  "compression_mixed": {"candidate": "...", "report": "..."},
  "compression_report": {"candidate": "...", "report": "...", "languages": {"target": "Japanese", "source": "English", "conversation": "Chinese"}},
  "compression_nonproject": {"candidate": "...", "report": "..."},
  "project_text": {
    "conventional-git-messages": {"artifact": "...", "report": "..."},
    "grill-duo-with-docs": {"artifact": "...", "report": "...", "languages": {"target_root": "English", "nested": "Chinese", "conversation": "Chinese"}},
    "pr-and-merge": {"artifact": "...", "report": "..."},
    "requirements-to-spec-tickets": {"artifact": "...", "child_prompt": "...", "report": "..."},
    "spec-implement-loop": {"artifact": "...", "report": "..."}
  },
  "same_repo": {"artifact": {"title": "...", "body": "..."}, "report": "...", "languages": {"target": "English", "skill_source": "English", "conversation": "Chinese"}},
  "ambiguous_policy": {
    "conventional-git-messages": {"artifact": "", "question": "..."},
    "grill-duo-with-docs": {"artifact": "", "question": "..."},
    "pr-and-merge": {"artifact": "", "question": "..."},
    "requirements-to-spec-tickets": {"artifact": "", "question": "..."},
    "spec-implement-loop": {"artifact": "", "question": "..."}
  }
}
```

Combine the fourteen isolated subagent responses in `tests/agent-acceptance/results.json`, then run `python tests/agent-acceptance/check_language_policy.py tests/agent-acceptance/results.json` with the repository's Python 3 runtime.
