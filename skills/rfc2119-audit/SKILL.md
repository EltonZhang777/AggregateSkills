---
name: rfc2119-audit
description: Audit an explicitly supplied Markdown root for likely RFC 2119 requirement markers. The audit is read-only, reports candidates for manual review, and does not rewrite content.
---

# RFC 2119 Audit

## Dependencies

When this skill's own workflow explicitly reaches a call to one of its directly declared Skill prerequisites, the call is explicit and may proceed even if that prerequisite disables implicit invocation. This waives only that invocation gate. It does not waive other prerequisite instructions or confirmation, authorization, security, or safety gates. It does not authorize transitive calls, create new call steps, or override an explicit prohibition on invoking another skill.

This skill declares no skill prerequisite. Its audit command requires Python 3.9 or later and uses only the Python standard library.

## Workflow

1. The normative [RFC 2119 vocabulary contract](references/rfc2119-reference.md) defines the vocabulary and when the reference is read.
2. Candidate auditing MUST require an explicit Markdown root; it has no packaged-skill or current-directory default.
3. The agent MUST run `python scripts/audit_rfc2119.py --root <directory>` and MAY add `--strict` to fail when candidates exist.
4. The agent MUST report every candidate with its root-relative path, one-based line number, category, and source text.

## Read-only boundary

The audit reports likely lowercase requirement words, unmarked prohibitions, and unmarked imperatives for manual review. Candidate reporting does not decide whether descriptive prose is normative. The audit MUST NOT rewrite, normalize, replace, or create files in the audited root.

Normal mode exits successfully when candidates exist. Strict mode exits `1` when candidates exist and `0` when none exist. Operational failures exit `2`, write an error to stderr, and print no candidate summary.
