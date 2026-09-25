---
name: grill-duo
description: "Use only when the user explicitly asks for a fixed independent subagent to review a multi-round grilling session. Use `/grill-duo-with-docs` when maintaining project documents; do not use for solo grilling or unrelated requests."
metadata:
  prerequisites: '{"skills":[["grilling","mattpocock/skills"]],"mcps":[],"tools":[]}'
---

# `/grill-duo`

Run a portable two-agent grilling session. The host interviews the user; one independent reviewer assesses each current round. The host remains the user's only conversational counterpart.

## Activation and dependency

Use this entrypoint only when the user explicitly requests independent two-agent review while clarifying or pressure-testing a plan, requirement, design, or decision. Use `/grill-duo-with-docs` when the session needs to maintain confirmed project documents. Do not activate for ordinary solo grilling, group discussion, or unrelated implementation work.

At activation, resolve the exact `/grilling` skill through an authoritative, complete skill catalog or runtime and read its original SKILL.md. Use Skill Scout when available; otherwise use the host runtime's complete skill-discovery facility. Do not infer that the skill is missing from the loaded-skills list alone, and do not vendor or silently replace it. If no authoritative resolver can find it, stop and tell the user it cannot be verified and can be installed with:

    npx skills@latest add mattpocock/skills --skill=grilling

This missing-dependency stop is different from an unavailable reviewer: only the latter uses solo mode.

## Roles and continuity

- The host is the only agent that speaks to the user, owns the decision tree, researches facts, and presents each round.
- Use the host runtime's independent subagent mechanism for one reviewer. Keep and reuse the same reviewer handle for the whole session. Do not assume a named-agent roster or choose or replace reviewers based on subjective topic fit.
- Change reviewers only when the user requests it and the runtime supports the change. If the runtime cannot preserve one reviewer across rounds, disclose that limitation and continue in solo mode rather than silently switching reviewers.
- If reviewer invocation is unavailable, fails, or the reviewer abstains, say that independent review was unavailable and continue the same grilling protocol in solo mode. Never invent or imply a second opinion.
- Keep the reviewer response in the host's private tool result. Do not create a group discussion or let the reviewer contact the user, implement the user's underlying request, delegate, or write project documents.

## Build the frontier

Maintain the user's goal, confirmed decisions and constraints, the open questions, their dependencies, the reviewer handle, and the active review request ID.

- Follow the current `/grilling` skill's design-tree method. Ask every decision whose prerequisites are settled and that can be answered now. Defer questions that depend on an unresolved answer. There is no fixed question-count cap.
- Give each question a stable ID such as Q1. Do not reuse an ID during the session. Keep an unanswered question's ID and wording when it remains unchanged. Do not add newly answerable questions to an open round; recompute the frontier after that round closes.
- Research facts with available tools or agents instead of asking the user to supply facts they could not decide. Keep genuine preferences and trade-offs for the user.
- Form the host's recommendation independently. Do not send it to the reviewer before the reviewer returns.

## Review each round

Before presenting a round, send one bounded request to the same reviewer. Include:

- a unique review request ID for this round or revision;
- the user's goal and confirmed decisions or constraints needed to understand it;
- the complete open frontier, with each question ID, options, dependencies, and relevant constraints;
- which questions the reviewer should assess now.

Ask for advice, rationale, risks, and relevant factual findings for each requested question ID. The reviewer must not add questions, choose for the user, start implementation, contact the user, delegate, or write project documents. Validate the response against these bounds; do not act on out-of-scope suggestions or forward them as reviewer advice. If noncompliant content cannot be separated from valid feedback, discard the result and disclose that independent review was unavailable.

Accept a result only when it belongs to the active reviewer invocation and matches the current review request ID. Reject late or superseded results; they cannot reopen, close, or advance a question. If a question or its options or constraints change, retain its ID, invalidate its old review, assign a new review request ID, and ask the reviewer to reassess only that question. Other open questions keep their current reviews.

If the runtime cannot correlate a response to its invocation, require the reviewer to echo the request ID and accept only an exact match. If the response abstains or does not assess a requested question, disclose that gap; do not fill it with invented reviewer advice.

## Present and continue

After a valid review arrives, combine it with the host's independent analysis. Present the entire current frontier to the user at once. For every question, show its stable ID, the meaningful options, the host's recommendation, and the reviewer's advice, reason, and risks. State factual findings separately from value judgments and accurately describe any disagreement.

Wait for the user's answers. Close only answered, cancelled, or invalidated questions. Keep unanswered questions and their IDs open. After the current round closes, update confirmed decisions and constraints, recompute the tree, and review the next answerable frontier. Do not treat silence, a reviewer suggestion, or an assumption as the user's decision.

When no decision remains open, summarize the goal, confirmed decisions, constraints, and material risks. Ask the user to confirm that shared understanding. Do not begin the user's underlying implementation until they confirm.
