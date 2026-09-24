# Agent Skill Review

This context defines the shared language for code review skills and their review reports.

## Language

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
