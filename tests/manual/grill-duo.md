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