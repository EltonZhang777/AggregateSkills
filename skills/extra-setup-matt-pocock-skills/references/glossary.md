<!-- extra-setup-matt-pocock-skills:glossary:start -->
## Operating contract terminology

**Authoritative checkout**:
The read-only repository root, branch or detached state, full object ID, and status snapshot taken at session start and rechecked before the first local mutation or branch creation. See [Session and checkout operations](<instruction-file>#session-and-checkout-operations).

**Authoritative issue read**:
A fresh direct read of tracker state used for requirements, writes, or closure decisions. See [Issue operations](docs/agents/issue-tracker.md#issue-operations).

**Navigation-only issue cache**:
An optional, non-authoritative index that may speed discovery but cannot supply issue state for writes, assignment, labels, closure, or verification. See [Issue operations](docs/agents/issue-tracker.md#issue-operations).

**Handoff approval record**:
A record with `approval_id`, `source`, `action`, `target`, `scope`, `lifetime`, and `invalidators`, matched exactly against the proposed action. See [Handoff approval records](<instruction-file>#handoff-approval-records).

**Tested tree state**:
The repository tree state covered by a verification result, recorded with the repository-native full object ID that produced it. See [Closure evidence](docs/agents/issue-tracker.md#closure-evidence).

**PARTIAL closure evidence**:
Closure evidence whose required coverage is missing, stale, or incomplete; it keeps the issue open unless separate approval records remaining scope and follow-up coverage or accepted risk. See [Closure evidence](docs/agents/issue-tracker.md#closure-evidence).
<!-- extra-setup-matt-pocock-skills:glossary:end -->
