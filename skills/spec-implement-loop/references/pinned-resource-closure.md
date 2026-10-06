# Pinned prerequisite resource closure

## Conditional support resources

These transitive files belong to the pinned-source closure. Read each only when its stated branch applies; the links use the same pinned revisions as the prerequisite metadata.

For `/setup-matt-pocock-skills`:

- [`issue-tracker-github.md`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md) — Use only when GitHub is selected as the issue tracker.
- [`issue-tracker-gitlab.md`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/setup-matt-pocock-skills/issue-tracker-gitlab.md) — Use only when GitLab is selected as the issue tracker.
- [`issue-tracker-local.md`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md) — Use only when local Markdown is selected as the issue tracker.
- [`triage-labels.md`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/setup-matt-pocock-skills/triage-labels.md) — Use only when `triage` is installed and Section B runs.
- [`domain.md`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/setup-matt-pocock-skills/domain.md) — Use for the selected domain-doc layout.

For `/archify`:

- [`references/repository-authoring.md`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/repository-authoring.md) — Read when tracing a real codebase.
- [`references/authoring-defaults.md`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/authoring-defaults.md) — Read for ordinary generation.
- [`references/brand-marks.md`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/brand-marks.md) — Read only for an explicitly requested unknown mark with a user-provided URL.
- [`schemas/architecture.schema.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/schemas/architecture.schema.json) — Read for Architecture mode.
- [`examples/web-app.architecture.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/examples/web-app.architecture.json) — Read for a system-description Architecture example.
- [`examples/production-deployment.architecture.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/examples/production-deployment.architecture.json) — Read for a deployment-repository Architecture example.
- [`schemas/workflow.schema.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/schemas/workflow.schema.json), [`examples/agent-tool-call.workflow.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/examples/agent-tool-call.workflow.json) — Read for Workflow mode.
- [`schemas/sequence.schema.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/schemas/sequence.schema.json), [`schemas/common.schema.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/schemas/common.schema.json), [`examples/cache-miss-request.sequence.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/examples/cache-miss-request.sequence.json) — Read for Sequence mode.
- [`schemas/dataflow.schema.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/schemas/dataflow.schema.json), [`schemas/common.schema.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/schemas/common.schema.json), [`examples/product-analytics.dataflow.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/examples/product-analytics.dataflow.json) — Read for Dataflow mode.
- [`schemas/lifecycle.schema.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/schemas/lifecycle.schema.json), [`schemas/common.schema.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/schemas/common.schema.json), [`examples/deployment-release.lifecycle.json`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/examples/deployment-release.lifecycle.json) — Read for Lifecycle mode.
- [`references/delivery-contract.md#failed-finalize-and-candidate-repair`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/delivery-contract.md#failed-finalize-and-candidate-repair) — Read after a non-zero `finalize` exit.
- [`references/architecture-layout-repair.md`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/architecture-layout-repair.md) — Read for several tangled Architecture routes.
- [`references/authoring-contract.md`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/authoring-contract.md) — Read for measured field or geometry failures.
- [`references/update-awareness.md`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/update-awareness.md) — Read when `update.noticeRequired` is true.
- [`references/authoring-contract.md#node-icons`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/authoring-contract.md#node-icons) — Read for an everyday subject.
- [`references/delivery-contract.md#sequence-width-review`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/delivery-contract.md#sequence-width-review) — Read when `layoutReviewRecommendation.action` is `inspect-sequence-width`.
- [`references/delivery-contract.md#optional-capture-evidence`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/delivery-contract.md#optional-capture-evidence) — Read for a requested visual review, a development audit, or a concrete route/browser concern.
- [`references/delivery-contract.md`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/delivery-contract.md) — Read for failed gates, standalone commands, provenance or recovery, repeated delivery, exports, or opening.
- [`references/authoring-contract.md#workflow-viewport-repair`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/authoring-contract.md#workflow-viewport-repair) — Read before the next layout edit when workflow viewport overflow occurs.
- [`references/delivery-contract.md#optional-opening`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/delivery-contract.md#optional-opening) — Read for an explicitly requested immediate preview or active desktop loop.
- [`references/viewer-runtime.md`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/viewer-runtime.md) — Read only for explicitly requested reader-facing viewer features.
- [`assets/template.html`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/assets/template.html), [`references/delivery-contract.md`](https://github.com/tt-a1i/archify/blob/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify/references/delivery-contract.md) — Use when shell access is unavailable.

For conditional `/codebase-design` reached through `/tdd`:

- [`DEEPENING.md`](https://github.com/mattpocock/skills/blob/6fd947921b935b7e1e69293a200400f0fdd5c15f/skills/engineering/codebase-design/DEEPENING.md) — Read when deepening a cluster given its dependencies.
- [`DESIGN-IT-TWICE.md`](https://github.com/mattpocock/skills/blob/6fd947921b935b7e1e69293a200400f0fdd5c15f/skills/engineering/codebase-design/DESIGN-IT-TWICE.md) — Read when exploring alternative interfaces for a chosen deepening candidate.

This package uses `/codebase-design` as vocabulary only; the two additional references are followed only when their specific branch applies. Both link back to the pinned `SKILL.md`; `DESIGN-IT-TWICE.md` also links to `DEEPENING.md`, so those paths resolve within the same pinned source.
