---
name: grill-duo
description: "Use only when the user explicitly asks for a fixed independent subagent to review a multi-round grilling session. Use `/grill-duo-with-docs` when maintaining project documents; do not use for solo grilling or unrelated requests."
---

# /grill-duo

Run a portable two-agent grilling session. The host interviews the user; one independent reviewer assesses each current round. The host remains the user's only conversational counterpart.

## Activation Criteria & Objective

Use this entrypoint only when the user explicitly requests independent two-agent review while clarifying or pressure-testing a plan, requirement, design, or decision. Use `/grill-duo-with-docs` when the session needs to maintain confirmed project documents. Do not activate for ordinary solo grilling, group discussion, or unrelated implementation work.

## Dependencies

If any dependency is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

| Name | Type | Source |
| --- | --- | --- |
| /grilling | Skill | https://github.com/mattpocock/skills |
| SkillRoute CLI | Tool | https://github.com/erichare/skillroute |

## Roles and continuity

An unavailable reviewer is different from a missing dependency: only reviewer unavailability uses solo mode.

- The host is the only agent that speaks to the user, owns the decision tree, researches facts, and presents each round.
- Use the host runtime's independent subagent mechanism for one reviewer. Keep and reuse the same reviewer handle for the whole session. Do not assume a named-agent roster or choose or replace reviewers based on subjective topic fit.
- Change reviewers only when the user requests it and the runtime supports the change. If the runtime cannot preserve one reviewer across rounds, disclose that limitation and continue in solo mode rather than silently switching reviewers.
- If the runtime cannot start a reviewer invocation or recovery invocation, disclose that independent review is unavailable and continue the same grilling protocol in solo mode. Never invent or imply a second opinion.
- Keep the reviewer response in the host's private tool result. Do not create a group discussion or let the reviewer contact the user, implement the user's underlying request, delegate, or write project documents.

## Build the frontier

Maintain the user's goal, confirmed decisions and constraints, the open questions, their dependencies, the reviewer handle, and the active `review_request_id` and `invocation_id`.

- Use `/grilling` for the design-tree method and current answerable frontier. Give each question an ID unique across the session; never reuse it. Keep its ID and wording while it remains unchanged.
- Keep each round's frontier fixed. Defer newly answerable questions until the current round closes, then recompute the frontier.
- Form the host's recommendation independently. Do not send it to the reviewer before the reviewer returns.

## Review each round

Before presenting a round, send one bounded request to the same reviewer. Include:

- a `review_request_id` for the semantic request, retaining it when the request is unchanged;
- a unique `invocation_id` for this attempt;
- the user's goal and confirmed decisions or constraints needed to understand it;
- the complete open frontier, with each question ID, options, dependencies, and relevant constraints;
- which questions the reviewer should assess now.

For each requested question ID, ask the reviewer to assess:

- whether the question is worth asking;
- whether the supplied context supports its premise, flagging assumptions, uncertainty, or evidence the host should verify;
- whether its wording is ambiguous or leading;
- whether differences in option length or detail may bias the choice; and
- which relevant perspectives are missing.

Ask for advice, rationale, risks, and relevant factual findings for each requested question ID, plus a recommendation to keep, revise, or drop the question. The reviewer may offer draft wording or answer choices; these are non-binding suggestions for the host. The host alone decides whether to keep, revise, or drop a listed question.

If the reviewer identifies a distinct decision missing from the current frontier, it may offer a clearly marked **Candidate follow-up** with draft wording. The candidate remains outside the formal frontier, with no official question ID, until the host chooses to adopt it in a later round.

The reviewer must not decide for the user, edit the formal frontier, contact the user, start implementation, delegate, or write project documents. Validate the response against these bounds; do not act on out-of-scope suggestions or forward them as reviewer advice. If noncompliant content cannot be separated from valid feedback, treat the output as invalid, discard it, and recover using the same request and current frontier.

Accept a result only when it belongs to the active invocation and matches the current `review_request_id`. Reject late or superseded results; they cannot reopen, close, or advance a question. When a semantic change affects a review—including the user's goal or confirmed decisions, a question, its options or constraints, the current frontier, or which questions are assessed—invalidate the affected review and assign it a new `review_request_id`. Keep each question's ID and unaffected questions' reviews.

If the runtime cannot correlate a response to its invocation, require the reviewer to echo both IDs and accept only an exact `review_request_id`/`invocation_id` match. If the response abstains or does not assess a requested question, disclose that gap; do not fill it with invented reviewer advice.

## Recover abnormal reviewer invocations

Explicit abstention and completed partial coverage are normal outcomes, not invocation failures. Disclose each coverage gap and do not replace the reviewer for that reason. Runtime failure, interruption, or blank, invalid, or truncated output is abnormal; start a new invocation for the same reviewer without asking the user for approval. Give every attempt a new `invocation_id`. Keep the `review_request_id` for a retry only while the semantic request is unchanged, as defined above.

While an invocation is `running`, inspect its visible history. Do not interrupt it or trigger recovery because time has passed or history has not changed. Explicit abnormal execution evidence tied to the active invocation may trigger recovery even while its status is `running`.

Use visible history for host continuity, but build the replacement request from the original bounded request and current frontier; do not include the previous invocation's analysis. If history is unavailable, reconstruct the request from host-held context.

## Present and continue

After a valid review arrives, combine it with the host's independent analysis and present the current frontier together in ordinary text; do not use a harness or an agent question component. For each stable ID, show meaningful options, the host's recommendation, and the reviewer's advice, rationale, risks, and relevant factual findings. Separate facts from value judgments and describe disagreements accurately.

Present any **Candidate follow-up** separately from the formal frontier, and make clear it remains a suggestion until the host chooses to adopt it in a later round.

After the user responds, close only answered, cancelled, or invalidated questions; keep unanswered IDs open. Follow `/grilling` for round closure and frontier refresh. When no decision remains, summarize the goal, confirmed decisions, constraints, and material risks, then ask for the user's final shared-understanding confirmation. Treat only the user's response as a decision. Do not begin the underlying implementation before the user confirms.
