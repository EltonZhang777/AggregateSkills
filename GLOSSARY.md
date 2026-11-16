# Agent Skill Workflows

This context defines shared language for the repository's engineering skill workflows, including code review, document compression, and skill prerequisite governance.

## Language

### Code review

**双代理代码评审**:
两位代理针对同一评审范围，分别从规范与质量、需求符合度两个审阅轴独立评估，并分别报告结论。
_Avoid_: 双人评审（容易被理解为必须由人类审阅者参与）

**评审范围**:
一份评审结论所适用的代码改动，以及解释该改动应如何工作的需求来源和仓库规范来源。
_Avoid_: 分支范围（分支名本身不能说明结论适用的确切改动）

**审阅轴**:
评审结论所采用的独立视角；本项目区分“规范与质量”和“需求符合度”。
_Avoid_: 总评（会掩盖两个视角之间的差异）

**Review track**:
An outer independent review path, such as `/code-review` or
`/ponytail-review`, executed by its own sub-agent. A review track can contain
one or more review axes.
_Avoid_: using "track" for an individual Standards or Spec axis.

**Partial root exception**:
A separately approved exception that lets a root proceed to status
synchronization after a one-track partial review, without changing that review
into a complete review.
_Avoid_: treating partial-mode approval as root completion.

**Finding**:
一项有具体证据和实际影响支撑的评审问题，并保留其所属审阅轴。
_Avoid_: 观点、偏好

### Document compression

**替换结果不确定**:
源文档替换操作报告错误，无法确认源路径当前保留原文还是已采用压缩候选。
_Avoid_: 操作失败（容易被理解为源文件未改变）

**Version-conditional write (CAS)**:
An atomic commit writes the candidate only if the target version token still matches the validated snapshot; a mismatch leaves the target unchanged.
_Avoid_: last-minute recheck (does not make compare and write atomic)

### Skill prerequisite governance

**Skill prerequisite**:
A skill, MCP, or runtime tool that another skill requires to complete its documented workflow.

**Skill dependency**:
An alias for Skill prerequisite.

**Prerequisite identity**:
The stable name and publishing source that distinguish the intended prerequisite independently of its local installation path.

**Prerequisite resolution**:
Finding the skill package or tool that matches a prerequisite identity in the current runtime.

### Multi-PR batches

**Merge pass**:
One execution of an authorized batch's ordered merge sequence, from its first merge attempt until all eligible merges are handled or the workflow pauses or stops.

**Post-merge verification**:
An assessment of each distinct target-base commit produced by a batch merge pass with at least one confirmed merge to that base.

**Validation-blocked base**: A target base whose post-merge verification cannot proceed because a preparation failure is confirmed local to that base.

### Multi-root implementation

**Task-start authorization**:
A one-time authorization requested by the root-level coordinator before it
dispatches any implementation spec in a frozen batch. The request names the
complete spec set, affected repositories and branches, and the Git and issue
action categories it covers. It applies only to those listed resources and
categories; if authorization is missing, the coordinator does not dispatch
the batch. It does not replace root completion approval.

**Batch-start approval**:
A task-start authorization for a frozen multi-root implementation batch, with
each root's task scope and permitted dependency-directed cross-root Git
operations named explicitly.
_Avoid_: Batch approval (too broad; loses the explicit authorization boundary)

<!-- extra-setup-matt-pocock-skills:glossary:start -->
## Operating contract terminology

**Authoritative checkout**:
The read-only repository root, branch or detached state, full object ID, and status snapshot taken at session start and rechecked before the first local mutation or branch creation. See [Session and checkout operations](AGENTS.md#session-and-checkout-operations).

**Authoritative issue read**:
A fresh direct read of tracker state used for requirements, writes, or closure decisions. See [Issue operations](docs/agents/issue-tracker.md#issue-operations).

**Navigation-only issue cache**:
An optional, non-authoritative index that may speed discovery but cannot supply issue state for writes, assignment, labels, closure, or verification. See [Issue operations](docs/agents/issue-tracker.md#issue-operations).

**Handoff approval record**:
A record with `source`, `action`, `normalized_target`, `lifetime`, and `invalidators`, using `one-time` or `task` and matched exactly against the proposed action. See [Handoff approval records](AGENTS.md#handoff-approval-records).

**Tested tree state**:
The repository tree state covered by a verification result, recorded with the repository-native full object ID that produced it. See [Closure evidence](docs/agents/issue-tracker.md#closure-evidence).

**PARTIAL closure evidence**:
Closure evidence allowed only when all original ticket deliverables are complete but required verification evidence is missing, or when remaining scope has a clearly linked follow-up issue. It keeps the issue open unless separate approval records remaining scope and current or linked follow-up coverage. See [Closure evidence](docs/agents/issue-tracker.md#closure-evidence).
<!-- extra-setup-matt-pocock-skills:glossary:end -->
