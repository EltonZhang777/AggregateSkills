# Release notes

Draft one copy-ready release-notes block for one shipped single-project release from supplied change facts or user-authorized read-only Git and GitHub evidence inspection within the named repository and release scope. Never stage, commit, or push. Do not create a tag, Release, or CHANGELOG entry; write an issue or pull request; change authentication; post a comment; or perform release-note publication.

## Inputs

- Require one explicit release scope as defined under Evidence. Use the supplied or inspected facts to describe each item, including affected users, problem, change, impact, breaking-change details, and deprecation details when available.
- Accept optional product, version, and date metadata when supplied or evidence-backed. Do not invent missing metadata.
- The audience defaults to general end users without a follow-up.
- If the supplied or inspected facts do not support a requested statement, ask for the missing fact instead of guessing.

## Scope

Draft exactly one shipped release for one single-project repository or product. A whole-repository release is allowed only for a single-project repository.

Reject a monorepo, multi-project, multi-platform, or multi-product request and ask for a separately scoped single-project input. Do not discover packages, apps, platforms, or release units.

## Evidence

Use only the supplied facts and user-authorized read-only Git and GitHub evidence inspection within the named repository and release scope. Verification and drafting perform no release or GitHub write.

Accept the release scope only from one of these inputs:

- An explicit change list.
- An exact ref set or tag pair.
- A PR or issue list supported by containment or merge evidence, or by a user attestation that the set shipped.

Version and release-date metadata are optional. Use supplied or evidence-backed metadata only. Session, meeting, or theme information may supply only labeled highlights and cannot substitute for a complete release scope.

For `START..END`, inspect commits reachable from `END` but not `START`. The opening boundary is excluded and the closing boundary is included. If the user asks to include the opening commit or supplies a three-dot range, request `START..END` or an exact ref set instead of silently changing the range. Do not treat a three-dot range as a chronological release range.

A read failure or unavailable authentication leaves an unresolved gap. Absent containment evidence or incomplete evidence also leaves an unresolved gap. Do not infer the missing release content.

- Omit a change fully reverted within scope.
- Ask when a revert or squash commit has an unclear net effect.
- Split a squash commit only with authorized PR or issue evidence.

## Audience and language

Use general end users only when the user does not select an audience. Otherwise accept exactly one explicitly selected external or customer-facing audience, such as administrators, operators, or developers/integrators. Do not infer any other audience. Reject or clarify an internal PM/QA audience or multiple audience variants in one response.

Repository-owned text follows the target repository root `AGENTS.md` language rule. When the external publication surface or its language cannot be determined, ask instead of guessing. Preserve non-sensitive quotations and names.

## Content gates

Every breaking change must state evidence-backed affected users or systems, compatibility impact, and an audience-appropriate migration, verification, or mitigation action. An evidence-backed `no action required` may serve as the action. A missing or unsupported breaking impact or action blocks the final copy-ready block.

A `!` marker or breaking-change phrase is only a signal; it does not replace impact or action evidence.

Every deprecation must state evidence-backed affected behavior. Any asserted removal timing or migration work also requires evidence.

Internal QA-only checklists never appear in external release notes. Include a QA step only when it can be rewritten as an external user action without exposing internal systems, credentials, or sensitive process information.

Collect missing mandatory facts, material evidence conflicts, and unresolved language or security authorization into one batch of blocking questions. Do not return a final copy-ready block while any mandatory gap remains.

After explicit user acceptance, a clearly labeled `Non-copy-ready preview` may be returned without placeholders. Do not label or format a preview as copy-ready. A preview does not satisfy these content gates: omit a fact that fails its gate, identify it as unresolved in the blocking questions, and never present it as verified release content.

## Disclosure and redaction

Omit or redact credentials, tokens, customer PII, private URLs, internal hostnames, and sensitive internal identifiers from both the release notes and `Draft basis`. Use a redacted category label instead of the sensitive value.

Omit an undisclosed or embargoed security item entirely until the user authorizes the exact disclosure scope or the specific fields are already public. Omit its existence from the `Draft basis` too.

Public disclosure permits only repetition of already-public fields. Do not expand to other affected systems, exploitation details, or fix details. The `Security` marker and `Draft basis` follow the same disclosure authorization rule as the security item.

## Version safety

Never calculate or assert a major, minor, or patch bump, and never recommend or create a tag. Repeat only supplied or evidence-backed SemVer implications where relevant.

Check a version label against change types only when the user explicitly states that the project uses SemVer and supplies its release policy. Otherwise no versioning scheme is inferred. If that check finds a version label inconsistent with the supplied policy or change types, treat it as a material evidence conflict and include it in the blocking questions; do not return the final copy-ready block.

## Classification and copy-ready output

Classify each item into exactly one section. Use this section order and precedence: Breaking Changes, Deprecations, Features, Fixes, Maintenance. Omit every section without items. Place a performance change under Feature or Fix according to the supplied or inspected effect.

When disclosure is authorized, place a security fix under Fixes with a visible `Security` marker; do not create a separate security section.

Return the release notes in one fenced `markdown` block.

- Include a level-one title only when the supplied or evidence-backed facts support it. Use only supplied or evidence-backed product, version, and date fields.
- If a title is present, follow it with a one-to-three-sentence overview grounded in the supplied or inspected change facts. If no title is present, begin with the overview.
- Use compact Problem, Change, and Impact information when the supplied or inspected facts support each label. Omit the Problem label when no problem fact is available.
- Use one canonical section per item. Do not repeat an item across sections.
- Produce no placeholders or `TBD` markers. Do not use tables or JSON.
- Return text only.

## Draft basis

In addition to the copy-ready block or accepted preview, return a compact `Draft basis` outside the fenced copy-ready block immediately after it. Report:

- Authorized source types.
- Exact available refs and commit SHAs.
- PR or issue numbers.
- Inspection date, or `not applicable` when only supplied facts were used.
- Unresolved gaps, or `None`.

When neither a final block nor an accepted preview is returned, include the `Draft basis` with the blocking questions.

Do not put evidence metadata or a raw appendix in the copy-ready text. Include item-level citations or links only when requested, required to resolve conflicting evidence, or needed to verify a specific claim.

Use redacted locators rather than private links or tokens. For a final draft, keep release notes inside the copy-ready block and the evidence summary outside it. Keep an accepted preview outside the copy-ready block.

## Example

Supplied facts: the legacy import command is removed; existing automation that calls it stops working; users must switch to the supported import command. The user also supplies product Workbench, version 2.4, and date 2026-12-01.

```markdown
# Workbench 2.4 - 2026-12-01

Workbench 2.4 changes how imports are invoked.

## Breaking Changes

- **Legacy import command removed** — Problem: Existing automation can no
  longer call the command it uses today. Change: The legacy import command is
  removed. Impact: Automations that call it stop working and must switch to the
  supported import command before upgrading.
```

### Draft basis

- Sources: supplied change facts.
- Scope: explicit change list.
- Refs, SHAs, PRs, issues: none.
- Inspection date: not applicable (no evidence inspection).
- Gaps: none.
