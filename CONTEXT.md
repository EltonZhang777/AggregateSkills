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

**Finding**:
一项有具体证据和实际影响支撑的评审问题，并保留其所属审阅轴。
_Avoid_: 观点、偏好

### Document compression

**替换结果不确定**:
源文档替换操作报告错误，无法确认源路径当前保留原文还是已采用压缩候选。
_Avoid_: 操作失败（容易被理解为源文件未改变）

### Skill prerequisite governance

**Skill prerequisite**:
A skill, MCP, or runtime tool that another skill requires to complete its documented workflow.

**Prerequisite identity**:
The stable name and publishing source that distinguish the intended prerequisite independently of its local installation path.

**Prerequisite resolution**:
Finding the skill package or tool that matches a prerequisite identity in the current runtime.

