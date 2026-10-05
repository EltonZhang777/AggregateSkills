# Skill Package Portability Audit

This audit captures a repeatable, evidence-based baseline for the skill packages in `skills/`. The inventory and checker use only the Python standard library. Reviewers inspect package content; they do not execute package instructions or perform external actions.

## Host fixture

Use `generic-agent-skills-host-v1` for every review. Assume the host can read the selected package and can describe its own capabilities. Do not assume the source repository, sibling packages, repository-only documents, a named agent harness, SkillRoute, GitHub access, credentials, network access, or subagent support as capabilities available to a user installing one skill. The isolated reviewers are a test-runner capability only; their availability says nothing about an individual skill's portability.

Assess each package's ordinary, user-visible workflow from its own files. Report any additional capability needed by a core or optional workflow and what the instructions say happens when it is unavailable. A generic host capability is not automatically a portability defect when the package identifies it and explains the effect of its absence. An undisclosed hard dependency in a core workflow is a failure. Report uncertainty as blocked or not-run, with a finding; do not infer a pass.

Classify a capability as `core` when its absence prevents the ordinary user-facing outcome after documented gates. Classify it as `optional` when a documented alternative completes the same outcome, even if that alternative requires user consent. When independent reviewers cite the same exact set of evidence anchors (package-relative path and inclusive line bounds), different capability scopes are a `reviewer_disagreement`, regardless of capability name or wording. Partially overlapping or different anchor sets are not the same evidence.

## Inventory and isolated reviews

Capture the inventory before starting reviews. It covers each immediate child directory of `skills/`, including directories without `SKILL.md`, and every nested file, including hidden, generated, and unused files. Symlinks are recorded without following them. Keep the package files unchanged until the checker finishes.

Launch two independent reviewers per package. Give both the same frozen inventory and host fixture. Reviewers must not share findings or see each other's result before submitting.

The `completeness` reviewer evaluates exactly these criteria:

- `entrypoint_and_format`: entrypoint presence and Agent Skills format.
- `resource_closure`: instructions and resources needed by the package are available within the package or through stable external references.
- `references_and_cycles`: package references resolve or are reported; skill-reference cycles are identified. Prerequisite declaration and prerequisite-owned section findings are reported for the owning governance work and are not edited here.
- `all_files_classified`: every inventoried file has a useful role classification, including generated or unused files.

The `workflow_portability` reviewer evaluates exactly these criteria:

- `generic_workflow_primary`: the ordinary workflow is understandable and presented before host-specific guidance.
- `harness_independence`: core instructions do not require a named harness API; any required generic capability and its unavailable behavior are explicit.
- `capabilities_and_unavailable_behavior`: core and optional host capabilities, their scope, and their unavailable behavior are accurately stated.
- `external_requirements`: external tools, services, credentials, and other requirements are reported and generic fallbacks are assessed.

Each review must use a unique `reviewer_id`, the exact fixture ID and inventory digest, one criterion result per role criterion, package-relative evidence for every criterion, findings for every non-pass criterion, required capabilities, and one file-coverage record per inventoried package file. Evidence locations use the exact package-relative path and one-based line bounds; the excerpt must occur on the declared lines. Binary or otherwise non-text files still need a file classification and disposition, but do not invent line evidence for them. A review with any `not_reviewed` file cannot pass.

Criterion and overall statuses are `pass`, `fail`, `blocked`, or `not_run`. Derive a review's overall status from its criteria (`fail` takes precedence, then `blocked`, then `not_run`, otherwise `pass`). A reviewer must not promote a non-pass criterion. Human review cannot convert a failure, block, or not-run result into a pass.

## CLI

From the repository root, use Python 3 from an active environment. This repository's Windows host uses Anaconda; activate that environment or use the available workspace runtime instead of assuming a Python command is on `PATH`. Set `$python` to the active interpreter path before running these PowerShell examples:

```powershell
$python = 'PATH_TO_ACTIVE_PYTHON_3'
& $python tests/test_skill_package_audit.py
& $python tests/agent-acceptance/audit_skill_packages.py inventory --skills-root skills --output tests/agent-acceptance/skill-package-baseline-inventory.json
& $python tests/agent-acceptance/audit_skill_packages.py check --skills-root skills --inventory tests/agent-acceptance/skill-package-baseline-inventory.json --results tests/agent-acceptance/skill-package-baseline-reviews.json --output tests/agent-acceptance/skill-package-baseline-report.json
```

The inventory command emits the schema-versioned package/file inventory and SHA-256 digest to stdout and, when `--output` is given, saves UTF-8 JSON outside the skills root. The checker likewise emits its aggregate result to stdout and can save it to an output file. Save reviewer output as UTF-8 without a BOM, using exactly one JSON object with `schema_version`, `fixture_id`, `inventory_sha256`, and a `reviews` array. Each review must use the exact field names and structures exercised by `tests/test_skill_package_audit.py`. The checker verifies current files still match the frozen inventory, exact skill and file coverage, schemas, evidence paths and excerpts, and reviewer role uniqueness and agreement. Neither command writes to skill packages.

Exit status `0` means every package passed. Exit status `1` means the report is valid and at least one package failed, is blocked, or was not run. Exit status `2` means invalid or incomplete inputs/coverage, reviewer disagreement, or another checker error; treat the result as blocked. A fresh inventory is required after any package file changes.

## Baseline interpretation

Keep the inventory and raw reviewer results as audit artifacts. Do not edit skill packages to make the baseline pass. Record unresolved package findings and required capabilities as they are observed. Findings about prerequisite declarations or their governed sections belong to the prerequisite-governance work; preserve those findings for handoff rather than changing the owned sections here.
