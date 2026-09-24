# grill-duo manual scenarios

Run these at the user-facing skill boundary in a host that can invoke an independent subagent. Record reviewer requests and responses separately from the host's user-visible messages.

## Complete frontier and bounded review

Ask the host to pressure-test a plan with five independent decisions and a sixth decision that depends on Q1. Confirm one bounded request goes to the reviewer with the goal, confirmed decisions, options, constraints, and the full open question set: Q1-Q5 are marked answerable now and Q6 is included as deferred because it depends on Q1. The host's recommendations stay private until the review returns. The reviewer should give advice, rationale, risks, and relevant factual findings for each requested question; it must not assess Q6 yet. Confirm the host presents all five answerable questions together with stable IDs and recommendations. This checks that there is no four-question cap.

## Partial answers, revisions, and reviewer continuity

Answer only some questions. Confirm answered items close while unanswered items retain their IDs and current review. Then change one open question's options or constraints. Confirm its ID stays the same, only that item is re-reviewed under a new request ID, and a delayed response to its superseded request cannot affect the round. After closing the round, confirm the same reviewer handle is used for the newly answerable Q6 with a fresh request ID.

## Reviewer boundary and fallback

Run once with reviewer invocation unavailable and once with a reviewer that abstains. Confirm the host discloses that no independent review occurred and continues in solo mode. If a reviewer response adds questions, chooses for the user, addresses the user, delegates, or writes project files, confirm the host ignores that content and never presents it as review advice.

## Final confirmation gate

Resolve or cancel every open decision. Confirm the host summarizes the goal, confirmed decisions, constraints, and material risks, then asks for final shared-understanding confirmation. It must not begin the user's underlying implementation before the user confirms.

## Research facts before asking

In a fixture repository, provide an authoritative runtime-support document stating that the project requires Node 22. Ask whether Node 20 is compatible and whether to deploy Tuesday or Saturday. Confirm the host reads the document, reports the Node 20 incompatibility with its source, and asks the user only about the deployment-date trade-off. It must not turn the findable compatibility fact into a user preference question.

## Documentation routing and confirmation gate

In a fixture repository, provide AGENTS.md and docs/agents/domain.md that route terms through CONTEXT-MAP.md to a context-specific CONTEXT.md, and route a difficult decision to an existing authoritative architecture or decision document. Ask the docs variant to clarify a term and a decision. Confirm it reads the repository map and applicable docs before writing, keeps the reviewer away from project documents, and makes no edit before the user confirms a specific term or decision. After confirmation, confirm the host writes only that item to the routed document and preserves unrelated content. Repeat in a single-context fixture without CONTEXT-MAP.md; confirm the host reads the root CONTEXT.md and relevant docs/adr/ files instead of looking for a nonexistent map.

## Additive reconciliation and semantic conflict

Give the routed document independent content and an exact duplicate of one newly confirmed term. Confirm the host preserves the independent content and removes only the exact duplicate. In a separate fixture, make the existing definition semantically conflict with the proposed confirmed term. Confirm the host reports both meanings and pauses without choosing or writing. Reviewer suggestions and unanswered questions must never be recorded as settled facts.

## Glossary and decision routing

Confirm CONTEXT.md receives glossary terms only, while implementation decisions go to the repository's authoritative decision document. Ask about a possible ADR; confirm one is created only when the decision is hard to reverse, surprising without context, and a genuine trade-off. The docs entrypoint must preserve the final shared-understanding gate before implementation.
