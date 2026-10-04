---
name: grill-duo
description: "Use only when the user explicitly asks for independent subagent review during a multi-round grilling session without project-document maintenance."
metadata:
  prerequisites: '{"skills":[["grilling","mattpocock/skills"]],"mcps":[],"tools":[]}'
---

# /grill-duo

Run a portable two-agent grilling session. The host interviews the user; one independent reviewer assesses each current round. The host remains the user's only conversational counterpart.

## Activation Criteria & Objective

Use this entrypoint only when the user explicitly requests independent two-agent review while clarifying or pressure-testing a plan, requirement, design, or decision, and the session does not maintain confirmed project documents. Do not activate for ordinary solo grilling, group discussion, or unrelated implementation work.

## Dependencies

Read the original `/grilling` `SKILL.md` from the active skill roots regardless of its invocation metadata. This exception permits source reading only. Before invoking the dependency, follow its invocation metadata and preserve all user-confirmation, authorization, and clarification gates in its instructions; if direct user invocation is required, pause at that gate. If the source is missing or unreadable, stop and direct the user to `/grilling` in the [prerequisite guide](../../docs/prerequisites.md).

An unavailable reviewer is different from a missing dependency: only reviewer unavailability uses solo mode.

## Roles and continuity

- The host is the only agent that speaks to the user, owns the decision tree, researches facts, and presents each round.
- Use the host runtime's independent subagent mechanism for one reviewer. Keep and reuse the same reviewer handle for the whole session. Do not assume a named-agent roster or choose or replace reviewers based on subjective topic fit.
- Change reviewers only when the user requests it and the runtime supports the change. If the runtime cannot preserve one reviewer across rounds, disclose that limitation and continue in solo mode rather than silently switching reviewers.
- If the runtime cannot start a reviewer invocation or recovery invocation, disclose that independent review is unavailable and continue the same grilling protocol in solo mode. Never invent or imply a second opinion.
- Keep the reviewer response in the host's private tool result. Do not create a group discussion or let the reviewer contact the user, implement the user's underlying request, delegate, or write project documents.

## Build the frontier

Maintain the user's goal, confirmed decisions and constraints, the open questions, their dependencies, the reviewer handle, and the active `review_request_id` and `invocation_id`.

- Follow the current `/grilling` skill's design-tree method. Ask every decision whose prerequisites are settled and that can be answered now. Defer questions that depend on an unresolved answer. There is no fixed question-count cap.
- Give each question a stable ID such as Q1. Do not reuse an ID during the session. Keep an unanswered question's ID and wording when it remains unchanged. Do not add newly answerable questions to an open round; recompute the frontier after that round closes.
- Research facts with available tools or agents instead of asking the user to supply facts they could not decide. If no suitable research capability is available, state which fact remains unverified, defer questions that depend on it, and continue with independent questions. Never present an unsupported claim as fact.
- Form the host's recommendation independently. Do not send it to the reviewer before the reviewer returns.

## Review each round

Before presenting a round, send one bounded request to the same reviewer. Include:

- a `review_request_id` for the semantic request, retaining it when the request is unchanged;
- a unique `invocation_id` for this attempt;
- the user's goal and confirmed decisions or constraints needed to understand it;
- the complete open frontier, with each question ID, options, dependencies, and relevant constraints;
- which questions the reviewer should assess now.

Ask for advice, rationale, risks, and relevant factual findings for each requested question ID. The reviewer must not add questions, choose for the user, start implementation, contact the user, delegate, or write project documents. Validate the response against these bounds; do not act on out-of-scope suggestions or forward them as reviewer advice. If noncompliant content cannot be separated from valid feedback, treat the output as invalid, discard it, and recover using the same request and current frontier.

Accept a result only when it belongs to the active invocation and matches the current `review_request_id`. Reject late or superseded results; they cannot reopen, close, or advance a question. When a semantic change affects a review—including the user's goal or confirmed decisions, a question, its options or constraints, the current frontier, or which questions are assessed—invalidate the affected review and assign it a new `review_request_id`. Keep each question's ID and unaffected questions' reviews.

If the runtime cannot correlate a response to its invocation, require the reviewer to echo both IDs and accept only an exact `review_request_id`/`invocation_id` match. If the response abstains or does not assess a requested question, disclose that gap; do not fill it with invented reviewer advice.

## Recover abnormal reviewer invocations

Explicit abstention and completed partial coverage are normal outcomes, not invocation failures. Disclose each coverage gap and do not replace the reviewer for that reason. Runtime failure, interruption, or blank, invalid, or truncated output is abnormal; start a new invocation for the same reviewer without asking the user for approval. Give every attempt a new `invocation_id`. Keep the `review_request_id` for a retry only while the semantic request is unchanged, as defined above.

While an invocation is `running`, inspect its visible history. Do not interrupt it or trigger recovery because time has passed or history has not changed. Explicit abnormal execution evidence tied to the active invocation may trigger recovery even while its status is `running`.

Use visible history for host continuity, but build the replacement request from the original bounded request and current frontier; do not include the previous invocation's analysis. If history is unavailable, reconstruct the request from host-held context.

## Present and continue

After a valid review arrives, combine it with the host's independent analysis. Present all currently answerable questions together in one ordinary-text message. Do not use a harness or an agent question component. For every question, show its stable ID, meaningful options, the host's recommendation, and the reviewer's advice, rationale, risks, and relevant factual findings. State factual findings separately from value judgments and accurately describe any disagreement.

Wait for the user's batch response. Close only answered, cancelled, or invalidated questions; keep unanswered questions and their IDs open for later rounds. After the current round closes, update confirmed decisions and constraints, recompute the tree, and review the next answerable frontier. Do not treat silence, a reviewer suggestion, or an assumption as the user's decision.

When no decision remains open, summarize the goal, confirmed decisions, constraints, and material risks. Ask the user to confirm that shared understanding. Do not begin the user's underlying implementation until they confirm.
