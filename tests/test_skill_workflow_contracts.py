"""Focused behavior contracts retained from the retired prerequisite checks."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def skill(name):
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def skill_reference(name, filename):
    return (
        ROOT / "skills" / name / "references" / filename
    ).read_text(encoding="utf-8")


def section(text, heading):
    start = text.index(heading) + len(heading)
    end = text.find("\n## ", start)
    if heading.startswith("### "):
        same_level = text.find("\n### ", start)
        if same_level != -1 and (end == -1 or same_level < end):
            end = same_level
    return text[start:] if end == -1 else text[start:end]


class SkillPrerequisiteInvocationTests(unittest.TestCase):
    def test_all_entrypoints_put_the_bounded_invocation_rule_first(self):
        entrypoints = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertEqual(11, len(entrypoints))

        for path in entrypoints:
            with self.subTest(skill=path.parent.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("## Dependencies", text)
                dependencies = section(text, "## Dependencies")
                rule = " ".join(dependencies.strip().split("\n\n", 1)[0].split()).lower()

                required_concepts = (
                    "explicitly reaches a call",
                    "directly declared skill prerequisite",
                    "may proceed",
                    "disables implicit invocation",
                    "waives only",
                    "other prerequisite instructions",
                    "confirmation",
                    "authorization",
                    "security",
                    "safety",
                    "does not authorize transitive calls",
                    "new call steps",
                    "explicit prohibition",
                )
                missing = [phrase for phrase in required_concepts if phrase not in rule]
                self.assertEqual([], missing, f"{path}: incomplete or misplaced rule")

    def test_skill_scout_remains_plan_only(self):
        text = skill("skill-scout").lower()
        self.assertIn("return a selection plan to the caller", text)
        self.assertIn("does not invoke selected workflows", text)

    def test_user_only_workflows_keep_invocation_metadata(self):
        for name in ("requirements-to-spec-tickets", "spec-implement-loop"):
            with self.subTest(skill=name):
                frontmatter = skill(name).split("---", 2)[1]
                self.assertIn("disable-model-invocation: true", frontmatter)

    def test_implicit_discovery_remains_disabled_where_configured(self):
        for name in ("requirements-to-spec-tickets", "review-duo", "skill-scout", "spec-implement-loop"):
            with self.subTest(skill=name):
                policy = (ROOT / "skills" / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
                self.assertIn("allow_implicit_invocation: false", policy)


class SpecReviewBehaviorTests(unittest.TestCase):
    def test_entrypoint_has_distinct_model_invocation_branches(self):
        path = ROOT / "skills" / "spec-review" / "SKILL.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1].lower()

        self.assertIn("name: spec-review", frontmatter)
        self.assertIn("initial review", frontmatter)
        self.assertIn("re-review after approved edits", frontmatter)
        self.assertNotIn("disable-model-invocation: true", frontmatter)
        self.assertNotIn("allow_implicit_invocation: false", text.lower())
        dependencies = section(text.lower(), "## dependencies")
        self.assertIn("no direct skill prerequisites", dependencies)

        policy = ROOT / "skills" / "spec-review" / "agents" / "openai.yaml"
        if policy.exists():
            self.assertNotIn("allow_implicit_invocation: false", policy.read_text(encoding="utf-8").lower())

        workflow = text.lower()
        self.assertIn("## review triggers", workflow)
        self.assertIn("initial review", workflow)
        self.assertIn("re-review after approved edits", workflow)
        self.assertIn("named staged specification", workflow)
        self.assertIn("identify its target repository", workflow)

    def test_review_lenses_and_conditional_triggers_are_declared(self):
        text = skill("spec-review").lower().replace(chr(96), "")

        for required in (
            "business scope",
            "engineering and test decisions",
            "affected-codebase evidence",
            "fresh isolated primary invocation",
            "independent adversary-a invocation",
            "for every affected technical stack",
            "root instructions, domain documents, and stack-specific checklist sources",
            "domain checklist triggers",
            "not applicable",
            "trigger is ambiguous",
            "coverage is incomplete",
            "developer-experience review",
            "cli/api/config/comparable developer-facing interface changes",
            "do not request cross-model opinions",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_coverage_states_gate_a_pass(self):
        text = skill("spec-review").lower().replace(chr(96), "")

        for state in ("covered", "not applicable", "incomplete"):
            with self.subTest(state=state):
                self.assertIn(state, text)
        self.assertIn("missing required coverage must never count as passed", text)
        self.assertIn("report the review as passed only when", text)
        self.assertIn("result is valid, complete, and recorded", text)
        self.assertIn("invocation or result is unavailable, partial, or abstains", text)
        self.assertIn("host identity or isolation cannot be verified", text)
        self.assertIn("all required invocations completed without a partial or abstaining result", text)

    def test_round_inputs_are_frozen_and_hashed_in_a_canonical_manifest(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        freeze = section(text, "## freeze the round inputs")
        manifest = section(text, "## canonical manifest")

        self.assertIn("at round start, freeze draft bytes", freeze)
        for source in (
            "target-repository snapshot",
            "scope/exclusions",
            "requirements",
            "applicable domain and decision documents",
            "relevant implementation, tests, configuration",
            "checks",
        ):
            with self.subTest(source=source):
                self.assertIn(source, freeze)
        for identity in ("stable source identifier", "exact byte size", "sha-256"):
            with self.subTest(identity=identity):
                self.assertIn(identity, freeze)
        for representation in (
            "immutable repository or file revision identifier",
            "without copying an entire repository snapshot",
            "for each source whose bytes are read",
            "exact source bytes",
            "do not use a hash of the revision-id string as a substitute for a source-content hash",
        ):
            with self.subTest(representation=representation):
                self.assertIn(representation, freeze)

        for rule in (
            "canonical utf-8 json",
            "recursively sorted object keys",
            "include every frozen source in the sources array",
            "ensure_ascii: false",
            "compact separators",
            "deterministically by stable source identifier",
            "hash the exact manifest bytes with sha-256",
            "manifest hash outside the manifest",
            "identical byte-based frozen inputs",
            "identical byte-based frozen inputs or the same immutable revision identifiers",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, manifest)

        for field in (
            "decide the complete required assignment set",
            "draft hash",
            "repository snapshot identity",
            "source_hashes",
            "checks",
            "required_assignments",
            "unique initial invocation id",
            "before hashing or freezing the manifest",
            "adversary-b",
            "single primary assignment's lens set",
            "every triggered non-adversarial lens",
            "high_risk_decision",
            "every trigger considered",
            "met, absent, or uncertain",
            "resulting required adversarial slots",
            "validate that required_assignments exactly matches that recorded decision before launching",
        ):
            with self.subTest(field=field):
                self.assertIn(field, manifest)

    def test_invocation_envelope_binds_assignments_to_host_identity(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        envelope = section(text, "## invocation envelope and host identity")

        for field in (
            "canonical utf-8 json invocation envelope",
            "manifest sha-256",
            "exact request identifier",
            "request sha-256",
            "cycle identifier",
            "round identifier",
            "exact assigned lens set",
            "adversarial slot",
            "unique invocation id",
            "reserved initial invocation id",
            "current active invocation id",
            "authorized retry",
            "unique active replacement id",
            "mark the prior id superseded",
            "recorded active id",
            "envelope bytes with sha-256",
            "identical frozen inputs and manifest",
            "host-returned session id",
            "matching host invocation and session binding",
            "self-reported invocation id",
        ):
            with self.subTest(field=field):
                self.assertIn(field, envelope)

    def test_risk_classification_selects_adversarial_slots(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        risk = section(text, "## risk and adversarial slots")

        self.assertIn("launch adversary-a in every round", risk)
        for trigger in (
            "security/privacy",
            "data loss/destructive behavior",
            "financial/charged data",
            "irreversible publication/ticket change",
            "review/approval gate",
            "core acceptance path",
        ):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, risk)
        self.assertIn("high-risk trigger is met or cannot be ruled out", risk)
        self.assertIn("require adversary-b", risk)
        self.assertIn("record the trigger and its evidence", risk)
        self.assertIn("do not launch adversary-b", risk)
        self.assertIn("separate fresh isolated invocations", risk)
        self.assertIn("neither adversary sees primary findings or the other adversary's findings", risk)

    def test_primary_is_one_invocation_for_all_triggered_non_adversarial_lenses(self):
        text = skill("spec-review").lower().replace(chr(96), "").replace("*", "")
        for phrase in (
            "exactly one fresh isolated primary invocation",
            "single primary assignment containing every triggered non-adversarial lens",
            "do not start one primary invocation per lens",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_results_require_complete_matching_attestations(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        attestation = section(text, "## result attestation")

        for field in (
            "primary invocation returns one distinct result for each lens",
            "all those per-lens results share that invocation's id, envelope hash, and host session binding",
            "each adversarial invocation returns its own result",
            "result lens or adversarial slot",
            "manifest, draft, and envelope sha-256 values",
            "checked source's stable identifier and sha-256",
            "unchecked source's stable identifier with a reason",
            "partition the manifest's frozen sources",
            "each source id appears exactly once",
            "with none omitted",
            "host-returned session binding to each result",
            "reject a result with a missing or mismatched attestation as stale or incomplete",
            "host session",
            "assignment",
            "checked source id/hash",
            "unchecked source id is absent from the frozen sources",
            "lacks a non-empty reason",
            "source lists omit, duplicate, or overlap a frozen source",
            "cannot make a lens covered",
        ):
            with self.subTest(field=field):
                self.assertIn(field, attestation)

    def test_cross_result_acceptance_keeps_retry_compatibility_without_retry_policy(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        acceptance = section(text, "## cross-result acceptance")

        for rule in (
            "initialize each assignment's active invocation id to its reserved initial id",
            "for an authorized retry, register one unique active replacement id",
            "mark the prior id superseded",
            "accept only the recorded active id",
            "never rewrite the frozen manifest",
            "supersede all of that invocation's lens results",
            "a late result from a superseded invocation id is rejected or excluded",
            "late result from a superseded invocation id",
            "rejected or excluded from the active result set",
            "retaining that rejected result with superseded status in history does not invalidate",
            "duplicate result slots",
            "superseded result presented or used as active leaves coverage incomplete",
            "does not define retry counts, retry limits, or review-cycle policy",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, acceptance)

    def test_cross_result_acceptance_requires_one_host_matched_result_per_manifest_slot(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        acceptance = section(text, "## cross-result acceptance")

        for rule in (
            "expand the primary assignment into one result slot per assigned lens",
            "one result slot for each adversarial assignment",
            "key a result slot by its exact assignment and result lens or adversarial slot",
            "all per-lens results from the same primary invocation intentionally share one invocation id",
            "an invocation id must remain unique to its manifest assignment",
            "duplicate result slots",
            "swapped lenses or assignments",
            "result slots absent from the manifest",
            "extra results",
            "superseded invocation ids",
            "repeated invocation ids are valid only across distinct per-lens results",
            "reject reuse across assignments",
            "every derived result slot has exactly one active, host-matched result",
            "without an unavailable, partial, or abstaining result",
            "stale or incomplete",
            "does not define retry counts, retry limits, or review-cycle policy",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, acceptance)

    def test_candidate_batch_binds_exact_edits_source_version_and_destination(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        batch = section(text, "## candidate batch and approval")

        for rule in (
            "one exact candidate batch",
            "stable identifier",
            "group the proposed edit hunks for each named source into one complete candidate draft",
            "exact source path and frozen sha-256",
            "unambiguous source span or insertion anchor",
            "exact replacement or insertion text",
            "affected draft section",
            "unique proposed destination path",
            "preserve all source text outside the proposed edit hunks",
            "never write to or replace the source path",
            "multiple candidate destinations as one resulting draft input set",
            "scope- or seam-changing proposals out of the approvable batch",
            "read-only until the user approves the exact candidate batch",
            "separately authorizes creation at its exact destination",
            "bind both decisions to the batch identifier",
            "every exact edit",
            "each source path and frozen sha-256",
            "each unique destination",
            "preserve those decisions in the task progress summary",
            "if any edit text, source version, destination, or batch membership changes",
            "obtain approval and write authorization for the new exact tuple",
            "a finding's disposition or review pass does not itself authorize a candidate write",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, batch)

    def test_candidate_write_obeys_cycle_budget_and_new_cycle_revalidation(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        batch = section(text, "## candidate batch and approval")

        for rule in (
            "before applying an approved batch, verify that the named cycle has a review round remaining",
            "if none remains, apply nothing",
            "record not_applied",
            "present the cycle-limit handoff",
            "explicitly authorizes a new named cycle",
            "after explicit new-cycle authorization",
            "prior exact batch approval and destination authorization still match",
            "source version is unchanged",
            "destination remains unused",
            "review a candidate applied under the new cycle as round 1",
            "preserve the previous cycle history",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, batch)

    def test_candidate_bytes_and_prepared_operation_are_derived_from_frozen_snapshot(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        writes = section(text, "## candidate creation and reconciliation")

        for rule in (
            "frozen bytes as an immutable byte snapshot",
            "read the source once into the snapshot",
            "verify its sha-256 matches the candidate's frozen hash",
            "derive candidate bytes only from that snapshot plus the approved edits",
            "preserve untouched bytes",
            "compute the expected sha-256 from the exact resulting bytes",
            "cannot be applied unambiguously",
            "stop before writing",
            "for each candidate destination, before its creation persist in the task progress summary one unique candidate-write operation id",
            "batch and destination identity",
            "source path and frozen hash",
            "exact expected candidate bytes",
            "expected sha-256",
            "prepared status",
            "serialize candidate-write operations for the same source path",
            "stable source-scoped lock where supported",
            "hold it through final source checks and destination creation",
            "do not run overlapping writes for a source",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, writes)

    def test_candidate_creation_is_create_new_and_source_races_preserve_files(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        writes = section(text, "## candidate creation and reconciliation")

        for rule in (
            "immediately before exclusive destination creation",
            "hash the current source path and require the frozen hash",
            "mark the operation stale",
            "immediately after successful creation, hash the source path again",
            "preserve both source and destination",
            "stop before review",
            "create the destination with create-new semantics only",
            "never overwrite",
            "an existing destination or failed create-new means not_applied",
            "do not silently choose another path",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, writes)

    def test_candidate_destination_verification_and_resume_reconcile_without_overwrite(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        writes = section(text, "## candidate creation and reconciliation")

        for rule in (
            "after creation, reread the destination",
            "byte-for-byte equality with the expected candidate snapshot",
            "sha-256 with the expected hash",
            "before marking the operation applied",
            "needs-reconcile",
            "preserve both files and stop before review",
            "batch remains incomplete",
            "every approved destination is verified",
            "on resume, treat an existing destination as applied only when",
            "matching operation id",
            "destination bytes and hash exactly match the persisted expected candidate",
            "otherwise mark needs-reconcile",
            "never overwrite",
            "infer success from path existence alone",
            "do not create a second operation",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, writes)

    def test_verified_candidate_starts_fresh_same_cycle_review_and_keeps_scope_gates(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        post_edit = section(text, "## post-edit review and completion")

        for rule in (
            "freeze all verified resulting bytes and hashes together as the next round's draft input set",
            "start the next numbered round in the same named cycle",
            "fresh primary invocation for all triggered non-adversarial lenses",
            "fresh invocations for every required adversarial slot",
            "count that review against the cycle's existing three-round budget",
            "stale, not_applied, or needs-reconcile candidate does not start",
            "candidate that changes scope or seams",
            "requirements-workflow seam confirmation",
            "seam confirmation alone grants no write permission",
            "exact revised draft text and a unique proposed temporary path",
            "explicit approval of that text and authorization for that path",
            "recheck the named-cycle round budget before writing",
            "if no round remains, apply nothing and use the cycle-limit handoff",
            "same candidate creation safeguards",
            "keep the existing round budget unless the user explicitly authorizes a new named cycle",
            "does not constitute final specification approval or publication",
            "do not publish an issue in this workflow",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, post_edit)

        record = section(text, "## named cycles and resumable state")
        self.assertIn("candidate-write operation records and statuses", record)

    def test_finding_gates_require_evidence_severity_disposition_and_scope(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        gates = section(text, "## finding and scope gates")

        for rule in (
            "evidence-based failure, not a preference",
            "name the affected draft section",
            "cite supporting evidence",
            "practical impact",
            "smallest exact change",
            "preference without a concrete failure, evidence, and impact is not a finding",
            "p0/p1/p2-or-lower definitions",
            "repository's p0/p1/p2-or-lower definitions",
            "preserve each reported severity and rationale",
            "a p0/p1 finding blocks early exit only when it cites an approved acceptance clause and shows a reproducible failure",
            "retain the original rating and rationale as an unverified observation",
            "not an established blocker",
            "do not downgrade it solely to satisfy the exit gate",
            "approved acceptance clause",
            "reproducible failure",
            "lack of safety proof alone does not establish a blocker",
            "p2-or-lower finding must be fixed",
            "explicitly declined, deferred, or otherwise resolved by the user",
            "recorded reason",
            "merge duplicate findings",
            "new evidence or a changed approved requirement",
            "within the approved scope and acceptance criteria",
            "changes the requested scope or crosses a seam",
            "route it back to the requirements workflow",
            "seam-confirmation gate",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, gates)

    def test_invalid_execution_retries_are_bounded_and_leave_unresolved_coverage_incomplete(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        retries = section(text, "## execution validity and retries")

        for rule in (
            "source, hash, manifest, file-access, and host-attribution failures",
            "invalid executions, not product findings",
            "truncated invocation is also an invalid execution",
            "never a valid partial review or abstention",
            "retry counts against the same-round attempt limit",
            "does not satisfy its assignment",
            "same round",
            "fresh invocation and a new invocation id",
            "complete assigned lens set as one assignment",
            "initial invocation and each retry as attempts",
            "at most three attempts per assignment per round",
            "reconcile or cancel",
            "status remains unresolved",
            "leave the assignment and review coverage incomplete",
            "after three failed or invalid attempts",
            "stop automatic retries",
            "without changing those rules",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, retries)

    def test_named_cycles_preserve_limits_resumable_state_and_incomplete_gates(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        cycles = section(text, "## named cycles and resumable state")

        for rule in (
            "at most three numbered rounds, including the initial round",
            "end a cycle early only when no p0/p1 finding remains",
            "every p2-or-lower finding is fixed or explicitly disposed of by the user with a reason",
            "pending user decision",
            "incomplete coverage blocks early exit, pass, and publication",
            "starting another named cycle requires the user's explicit authorization",
            "fresh three-round budget",
            "do not reset a round or attempt counter",
            "preserve a resumable cycle record",
            "round/attempt counts",
            "including per-assignment attempt counts",
            "active and superseded invocation and host ids",
            "frozen draft and manifest hashes",
            "user decisions",
            "finding dispositions",
            "reconcile that record with authoritative host or invocation evidence",
            "never reuse an invocation id",
            "missing or conflicting state",
            "needs-reconcile",
            "do not create a separate local authoritative database",
            "valid partial review or abstention consumes its numbered round",
            "is not an invalid-execution retry",
            "supplying missing evidence does not reopen that round",
            "if the named cycle has a round remaining",
            "incorporate the evidence into a new frozen manifest",
            "next numbered round on the unchanged draft",
            "fresh primary and every required adversarial invocation",
            "if no round remains, use the cycle-limit handoff",
            "three-round limit is reached and the review has not passed",
            "present the current frozen draft and every unresolved finding",
            "every unresolved finding, incomplete lens or slot",
            "pending user decision",
            "unresolved execution reconciliation",
            "review has not passed",
            "ask whether the user authorizes another named cycle or wants another action",
            "not final approval or publication",
            "new named cycle preserves prior reports and findings as history",
            "append the new cycle to the resumable record",
            "do not reset or mutate prior cycle history",
            "prior cycle reports and findings",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, cycles)

    def test_rereview_scope_stays_on_approved_edits_and_affected_criteria(self):
        text = skill("spec-review").lower().replace(chr(96), "")
        triggers = section(text, "## review triggers")

        for rule in (
            "focus the re-review on the approved edits and directly affected criteria",
            "expand scope only when new evidence implicates another approved requirement",
            "evidence that changes scope or crosses a seam remains separate",
            "requirements workflow's seam-confirmation gate",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, triggers)

    def test_manual_spec_review_covers_frozen_evidence_and_adversarial_slots(self):
        manual = (ROOT / "tests" / "manual" / "spec-review.md").read_text(encoding="utf-8").lower()
        for phrase in (
            "at round start",
            "stable source identifier",
            "immutable repository or file revision identifiers",
            "for each source whose bytes are read",
            "exact source bytes",
            "do not use a hash of the revision-id string",
            "canonical utf-8 json",
            "manifest sha-256",
            "host-returned session id",
            "adversary-a launches every round",
            "high-risk",
            "adversary-b",
            "missing or mismatched attestation",
            "stale or incomplete",
            "required_assignments",
            "initial invocation id",
            "duplicate result slots",
            "swapped lenses or assignments",
            "extra results",
            "superseded invocation ids",
            "exactly one active, host-matched result",
            "high_risk_decision",
            "every trigger considered",
            "met`, `absent`, or `uncertain",
            "required adversarial slots",
            "exactly one primary assignment",
            "every triggered non-adversarial lens",
            "unchecked source ids",
            "unchecked sources carrying reasons",
            "authorized retry",
            "active replacement id",
            "late result from the superseded invocation id",
            "rejected or excluded from the active result set",
            "retain it in history with superseded status",
            "later complete active result set still passes",
            "duplicate result slots",
            "superseded result presented or used as active",
            "evidence-based failure",
            "draft section",
            "supporting evidence",
            "practical impact",
            "smallest exact proposed change",
            "preference alone is not a finding",
            "p0/p1",
            "approved acceptance clause",
            "reproducible failure",
            "lack of safety proof alone",
            "p2-or-lower",
            "declined, deferred, or otherwise resolved",
            "merge duplicate findings",
            "new evidence or a changed approved requirement",
            "changes the requested scope or crosses a seam",
            "requirements workflow",
            "invalid executions, not product findings",
            "new invocation id",
            "at most three attempts per assignment per round",
            "reconcile or cancel",
            "unresolved status leaves coverage incomplete",
            "at most three rounds per named cycle",
            "end a cycle early only",
            "explicit user authorization",
            "fresh three-round budget",
            "resumable cycle record",
            "round/attempt counts",
            "active and superseded invocation and host ids",
            "frozen draft and manifest hashes",
            "user decisions",
            "finding dispositions",
            "pending decisions or incomplete coverage block pass and publication",
            "valid partial review or abstention",
            "consumes its numbered round",
            "not an invalid-execution retry",
            "supplying missing evidence does not reopen that round",
            "new frozen manifest",
            "next numbered round on the unchanged draft",
            "fresh primary and every required adversarial invocation",
            "cycle-limit handoff",
            "three-round limit is reached",
            "current frozen draft and every unresolved finding",
            "incomplete lens or slot",
            "pending user decision",
            "unresolved execution reconciliation",
            "review has not passed",
            "another action",
            "not final approval or publication",
            "prior reports and findings as history",
            "append the new cycle",
            "do not reset or mutate prior cycle history",
            "re-review focuses on the approved edits and directly affected criteria",
            "expand scope only when new evidence implicates another approved requirement",
            "scope or crosses a seam",
            "requirements workflow",
            "one candidate batch with a stable batch id",
            "source path and frozen sha-256",
            "exact source span or insertion anchor",
            "exact replacement or insertion text",
            "affected section",
            "unique proposed destination",
            "original source is unchanged",
            "approve the exact batch and authorize its destination",
            "batch id, edit text, source version, and destination",
            "third round with a candidate batch ready",
            "applies nothing",
            "records `not_applied`",
            "revalidates the exact batch, source version, and unused authorized destination",
            "reviews the candidate as round 1",
            "preserves all prior reports and findings as history",
            "immutable byte snapshot",
            "derive the exact candidate bytes only from that snapshot and approved edits",
            "unique operation id",
            "exact expected bytes and hash",
            "`prepared` status",
            "writes for one source are serialized",
            "stable source lock where supported",
            "change the source before the pre-create hash check",
            "immediately after exclusive creation",
            "both files are preserved",
            "existing destination and a failed create-new operation",
            "reread the destination and compare its bytes and sha-256",
            "needs-reconcile",
            "operation id and exact expected bytes and hash match",
            "all approved destinations verify",
            "next numbered round in the same named cycle",
            "one fresh primary for all triggered non-adversarial lenses",
            "fresh invocations for every required adversarial slot",
            "seam confirmation alone grants no write permission",
            "explicit text approval",
            "path authorization",
            "candidate review completion remains separate from final specification approval and publication",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, manual)

def mentions_concepts(text, *concepts):
    return all(any(term in text for term in alternatives) for alternatives in concepts)


def sentence_with_concepts(text, *concepts):
    return next((sentence for sentence in re.split(r"(?<=[.!?])\s+", text) if mentions_concepts(
        sentence, *concepts,
    )), "")


def independent_work_continuation(text):
    sentence = sentence_with_concepts(
        text, ("independent", "unrelated"), ("phase", "group", "work"),
        ("continue", "continues", "continuing", "proceed", "proceeds", "proceeding",
         "remain eligible", "remain available", "keep running", "running"),
    )
    if re.search(
        r"\b(?:does not|doesn't|did not|didn't|cannot|can't|must not|mustn't|"
        r"may not|will not|won't|would not|wouldn't|should not|shouldn't|"
        r"is not|isn't|are not|aren't|was not|wasn't|were not|weren't|never|unable to)\s+"
        r"(?:(?:be\s+)?(?:able|allowed|permitted|authorized|expected|guaranteed)\s+to\s+)?"
        r"(?:continue|proceed|remain|run)\b",
        sentence,
    ) or re.search(
        r"\b(?:is|are|was|were|will be|may be)\s+"
        r"(?:blocked|prevented|barred|stopped|paused|prohibited|forbidden|unable)\s+"
        r"from\s+(?:continu\w*|proceed\w*|remain\w*|run\w*)\b",
        sentence,
    ):
        return ""
    return sentence


def clauses(text):
    return [clause.strip() for clause in re.split(
        r"\b(?:however|although|though|while|yet|except|unless|rather than)\b"
        r"|\bbut\b(?!\s+(?:only\s+)?(?:with|after|unless|when|if)\s+(?:a\s+)?"
        r"(?:separate|additional|own)(?:\s+user)?\s+approval)"
        r"|\band(?=\s+(?:does not|doesn't|cannot|can't|must not|never)\b)"
        r"|\band(?=\s+(?:commit(?:s)?|push(?:es)?)\b"
        r"(?:(?!\band\b)[^.!?])*\b(?:requir\w*|need\w*)\b"
        r"(?:(?!\band\b)[^.!?])*\b(?:separate|additional)\s+approval\b)"
        r"|\band(?=\s+(?:(?:a|the)\s+)?(?:separate\s+)?user(?:'s)?\s+"
        r"(?:(?:separate|own)\s+)?(?:approval|authorization)\b)"
        r"|\band(?=\s+(?:(?:a|the)\s+)?(?:(?:separate|own)\s+)?"
        r"(?:approval|authorization)\s+(?:from|by)\s+(?:the\s+)?user\b)"
        r"|\band(?=\s+(?:issue creation|comments?|label changes|sub-issue links?|"
        r"pull request actions?|pr creation|merges?)\b[^.!?]*\b(?:is|are)\s+"
        r"(?:separately\s+)?(?:authorized|approved|permitted|allowed)\s+by\s+(?:the\s+)?user\b)"
        r"|\band(?=\s+(?:these|those|they)\s+(?:still\s+)?(?:requir\w*|need\w*)\b"
        r"[^.!?]*\b(?:separate|additional)\s+approval\b)"
        r"|\band(?=\s+(?:(?:the|a)\s+)?(?:user|group\s+b|b\b))|[;.!?]",
        text,
    ) if clause.strip()]


def authorization_grant_clause(text, *concepts):
    parts = clauses(text)
    for index, clause in enumerate(parts):
        match = TASK_AUTHORIZATION_GRANT.search(clause)
        if (
            match
            and not TASK_AUTHORIZATION_DENIAL.search(clause)
            and mentions_concepts(clause[match.end():], *concepts)
            and not (
                index + 1 < len(parts)
                and ANAPHORIC_SEPARATE_APPROVAL.search(parts[index + 1])
            )
        ):
            return clause
    return ""


def permission_clause(text, *concepts):
    for clause in clauses(text):
        clause = re.sub(
            r"\b(?:not|never|without|rather than)\s+under a's (?:approval|authorization)\b",
            "",
            clause,
        )
        if (
            mentions_concepts(clause, *concepts)
            and re.search(
                r"\b(?:may|can|allowed|permitted|authorized|authorizes?|permits?|"
                r"allows?|grants?|covers?)\b",
                clause,
            )
            and not TASK_ACTION_DENIAL.search(clause)
        ):
            return clause
    return ""


def status_sync_grant_clause(text, *concepts):
    for clause in clauses(text):
        direct_scope = STATUS_SYNC_CONDITIONALLY_APPROVED_WRITE.sub("", clause)
        match = STATUS_SYNC_GRANT.search(direct_scope)
        if match and mentions_concepts(direct_scope[match.start():], *concepts):
            return clause
    return ""


AUTO_INSTALL_PROHIBITION = re.compile(
    r"\b(?:do not|does not|don't|never|must not)\s+(?:automatically\s+)?install\b"
)
TASK_AUTHORIZATION_GRANT = re.compile(
    r"\b(?:approval|authorization)\b.*\b"
    r"(?:grant(?:s|ed)?|authoriz(?:e|es|ed)|permit(?:s|ted)?|"
    r"allow(?:s|ed)?|cover(?:s|ed)?|enable(?:s|d)?)\b"
)
TASK_AUTHORIZATION_DENIAL = re.compile(
    r"\b(?:approval|authorization)\s+"
    r"(?:does not|doesn't|cannot|can't|must not|never)\s+"
    r"(?:grant|authorize|permit|allow|cover)\b"
    r"|\b(?:approval|authorization)\s+(?:(?:is\s+)?alone\s+)?(?:is\s+)?"
    r"(?:insufficient|inadequate|not sufficient|not enough)\s+to\s+"
    r"(?:grant|authorize|permit|allow|cover)\b"
)
TASK_ACTION_DENIAL = re.compile(
    r"\b(?:does not|doesn't|cannot|can't|must not|never)\s+"
    r"(?:grant|authorize|permit|allow|cover)\b"
    r"|\b(?:may not|cannot|can't|must not|should not)\s+(?:write|commit|push)\b"
    r"|\b(?:never|isn't|is not|aren't|are not|not)\s+(?:permitted|authorized|allowed)\b"
)
ANAPHORIC_SEPARATE_APPROVAL = re.compile(
    r"\b(?:these|those|they)\s+(?:still\s+)?(?:requir\w*|need\w*)\b"
    r"[^.!?]*\b(?:separate|additional)\s+approval\b"
)
TASK_AUTHORIZATION_LIMIT = re.compile(
    r"\b(?:does not|doesn't|cannot|can't|must not)\s+(?:carry|transfer|extend|apply)\b"
)
STATUS_SYNC_GRANT = re.compile(
    r"\b(?:status-sync authorization|status synchronization|status sync)\s+"
    r"(?:(?:itself|also|may|can|still)\s+)*(?:authoriz(?:es|e)|permit(?:s)?|"
    r"allow(?:s)?|cover(?:s)?|grant(?:s)?|enable(?:s)?|creat(?:e|es)|"
    r"writ(?:e|es)|post(?:s)?|link(?:s)?|label(?:s)?|chang(?:e|es)|updat(?:e|s)|"
    r"merg(?:e|es)|delet(?:e|es)|edit(?:s)?|comment(?:s)?|add(?:s)?|"
    r"remov(?:e|es)|open(?:s)?|clos(?:e|es)|perform(?:s)?|"
    r"execut(?:e|es)|issue(?:s)?)\b"
)
STATUS_SYNC_CONDITIONALLY_APPROVED_WRITE = re.compile(
    r"\b(?:allow(?:s|ed)?|authoriz(?:e|es|ed)|permit(?:s|ted)?|grant(?:s|ed)?|"
    r"cover(?:s|ed)?|enable(?:s|d)?)\s+"
    r"(?:the\s+)?(?:issue creation|create an issue|new issue|comments?|labels?|"
    r"label changes|sub-issue links?|pull request actions?|pr creation|merges?|"
    r"other github writes?)\s*,?\s*(?:but\s+)?(?:only\s+)?"
    r"(?:with|after|unless|when|if)\s+(?:a\s+)?"
    r"(?:separate|additional|own)(?:\s+user)?\s+approval\b"
)
NON_STATUS_WRITES = (
    "issue creation", "create an issue", "new issue", "comment", "label", "sub-issue",
    "pull request", "pr creation", "merge", "other github write",
)


class SkillScoutBehaviorTests(unittest.TestCase):
    def test_general_inventory_and_selected_catalog_flow(self):
        text = skill("skill-scout").lower().replace(chr(96), "")
        general = section(text, "## general-host discovery")
        fallback = " ".join(section(text, "## skillroute local-catalog fallback").split())
        local_reference = skill_reference("skill-scout", "skillroute-local-catalog.md").lower().replace(chr(96), "")
        dependencies = section(local_reference, "## dependencies")
        local = section(local_reference, "## skillroute local-catalog mode")
        explicit = section(text, "### resolve an explicitly named skill")
        report = section(text, "## report")
        self.assertLess(text.index("## general-host discovery"), text.index("## skillroute local-catalog fallback"))
        self.assertIn("only after general-host discovery cannot retrieve a result", fallback)
        self.assertIn("only when the user selects the local-catalog mode", fallback)
        self.assertIn("skillroute-local-catalog.md", fallback)
        self.assertNotIn("## skillroute local-catalog mode", text)
        self.assertIn("start with an installed-skill inventory exposed by the host or supplied by the caller", general)
        self.assertIn("treat an inventory as complete only when its source identifies it as covering all installed skills", general)
        self.assertIn("a partial inventory never proves a skill is absent", general)
        self.assertIn("request a complete inventory or the user's choice to use skillroute local-catalog mode", general)
        self.assertIn("return unavailable", general)
        self.assertIn("if any dependency is missing, report all missing dependencies", dependencies)
        self.assertIn("skillroute cli", dependencies)
        self.assertIn("optional local-catalog mode", local)
        self.assertIn("reads the local catalog only", local)
        self.assertIn("does not use a network backend", local)
        self.assertIn("run the cli and backend checks before routing", local)
        self.assertIn("if the cli, local backend, or catalog is unavailable, return unavailable", local)
        self.assertIn("do not present the result as evidence that a skill is absent", local)
        self.assertIn("temporary resolver or backend errors", local)
        self.assertIn("return an unresolved prerequisite result", local)
        self.assertIn("exact failed check and recovery condition", local)
        self.assertIn("and stop", local)
        self.assertIn("do not fall back to another discovery source", local)
        self.assertIn("if a complete inventory does not contain it, return missing prerequisite", explicit)
        self.assertIn("if the inventory is partial, return unavailable", explicit)
        self.assertIn("unresolved prerequisite", report)
        self.assertIn("unavailable", report)

    def test_ambiguous_explicit_name_requires_source_choice(self):
        text = skill("skill-scout").lower().replace(chr(96), "")
        explicit = section(text, "### resolve an explicitly named skill")
        self.assertIn("treat a supplied source as part of the identity", explicit)
        self.assertIn("a same-name entry from another source is not a match", explicit)
        self.assertIn("if multiple entries match, return user decision required", explicit)
        self.assertIn("show each candidate and its declared or undeclared source", explicit)
        self.assertIn("do not choose by inventory order or rank", explicit)


class PrAndMergeBehaviorTests(unittest.TestCase):
    def test_multi_pr_requests_route_before_discovery_and_preserve_single_pr_flow(self):
        text = skill("pr-and-merge").lower().replace(chr(96), "")
        routing_heading = "## multi-pr request routing"
        self.assertIn(routing_heading, text)
        self.assertLess(text.index(routing_heading), text.index("## dependencies"))

        routing = section(text, routing_heading)
        self.assertIn("before discovery", routing)
        self.assertIn("references/multi-pr-batch.md", routing)
        self.assertIn("exactly one operation is resolved", routing)
        self.assertIn("no other outcome needs a batch report", routing)
        self.assertNotIn("eligible operation", routing)
        self.assertIn("single-pr flow", routing)
        self.assertIn("## resolve the source and target", text)

    def test_multi_pr_reference_covers_scope_plan_ordering_and_refresh_gates(self):
        reference_path = ROOT / "skills" / "pr-and-merge" / "references" / "multi-pr-batch.md"
        self.assertTrue(reference_path.is_file(), "the routed multi-PR reference must exist")
        text = skill_reference("pr-and-merge", "multi-pr-batch.md").lower().replace(chr(96), "")

        selectors = section(text, "## discover and deduplicate selectors")
        self.assertIn("inclusive pr ranges", selectors)
        self.assertIn("selector aliases", selectors)
        self.assertIn("same exact pr", selectors)
        self.assertIn("different bases stay separate operations", selectors)
        self.assertIn("explicit stack relationship", selectors)

        scope = section(text, "## report the complete scope")
        self.assertIn("one row per deduplicated operation", scope)
        self.assertIn("unmatched", scope)
        self.assertIn("ambiguous", scope)
        self.assertIn("missing base", scope)
        self.assertIn("draft", scope)
        self.assertIn("already-blocked prs", scope)
        self.assertIn("prospective pr operation", scope)
        self.assertIn("report-only", scope)
        self.assertIn("initial scope report", scope)
        self.assertIn("no planned writes", scope)
        self.assertIn("final outcome summary", scope)
        self.assertIn("verified exact merged match", scope)
        self.assertIn("closed unmerged pr remains report-only", scope)

        plan = section(text, "## present the exact plan and authorize the batch")
        for detail in ("source head sha", "dependencies", "planned pushes", "blockers"):
            self.assertIn(detail, plan)
        self.assertIn("one explicit authorization", plan)
        self.assertIn("no writes", plan)
        self.assertIn("head and base names and oids", plan)
        self.assertIn("satisfies", plan)
        self.assertIn("per-pr merge approval", plan)
        self.assertIn("base oid advancement alone does not revoke batch authorization", plan)
        self.assertIn("approved source head is unchanged", plan)
        self.assertIn("no new conflict-resolution work is required", plan)

        execution = section(text, "## execute the approved batch")
        self.assertIn("then merge them in that same order", execution)
        self.assertIn("do not ask again for that unchanged merge", execution)
        self.assertIn("do not ask again solely because the base oid advanced", execution)
        self.assertIn("live per-pr merge checks", execution)

        batch = section(skill("pr-and-merge").lower(), "## process a batch")
        self.assertNotIn("present a separate approval snapshot for each pr", batch)
        self.assertNotIn("finish preparing every eligible pr before merging any", batch)
        self.assertIn("never stash or clean a supplied worktree", batch)
        self.assertIn("stage its conflict-resolution files only after explicit approval of the exact diff", batch)

        source_resolution = section(skill("pr-and-merge").lower(), "## resolve the source and target")
        self.assertIn("already dirty at this initial source-resolution check", source_resolution)
        self.assertIn("if conflict resolution later makes the worktree dirty", source_resolution)

        preparation = section(skill("pr-and-merge").lower(), "## reuse or prepare the pr")
        self.assertIn("for a single-pr request", preparation)
        self.assertIn("for a batch request", preparation)
        self.assertIn("do not pause again for a merge already listed in the authorized batch", preparation)

        ordering = section(text, "## order dependencies and conflict candidates")
        self.assertIn("read every selected diff before ordering", ordering)
        self.assertIn("hard constraints", ordering)
        self.assertIn("conflict-free", ordering)
        self.assertIn("only to break ties within either group", ordering)
        self.assertIn("complete order cannot bypass this preference", ordering)
        self.assertIn("same base", ordering)

        conflicts = section(text, "## gate conflict resolution")
        self.assertIn(".wt", conflicts)
        self.assertIn("dirty worktree", conflicts)
        self.assertIn("exact repository", conflicts)
        self.assertIn("exact source branch", conflicts)
        self.assertIn("owner/repo", conflicts)
        self.assertIn("git rev-parse --show-toplevel", conflicts)
        self.assertIn("git remote -v", conflicts)
        self.assertIn("git status --porcelain=v1 --untracked-files=all", conflicts)
        self.assertIn("never stage, commit, stash, discard, or push automatically", conflicts)
        self.assertIn("complete unstaged conflict-resolution diff", conflicts)
        self.assertIn("before staging or any other write", conflicts)
        self.assertIn("stage only the approved files", conflicts)
        self.assertIn("staged diff differs from the approved diff", conflicts)

        refresh = section(text, "## refresh after source or base changes")
        self.assertIn("head and base oids", refresh)
        self.assertIn("reviews", refresh)
        self.assertIn("checks", refresh)
        self.assertIn("base oid advancement alone does not revoke batch authorization", refresh)
        self.assertIn("commits between them", refresh)
        self.assertIn("current diff against the approved source snapshot", refresh)
        self.assertIn("unrelated operations continue", refresh)
        self.assertIn("../skill.md#process-a-batch", text)
        self.assertIn("../skill.md#merge-after-approval", text)

        merge = skill_reference("pr-and-merge", "merge-after-approval.md").lower()
        self.assertIn("multi-pr-batch.md#refresh-after-source-or-base-changes", merge)
        self.assertIn("retain the batch-plan order through merging", merge)
        self.assertIn("conflict-free entries before conflict candidates", merge)
        self.assertIn("only to break ties within either group", merge)
        self.assertIn("before staging or any other write", merge)
        self.assertIn("stage only the approved files", merge)
        self.assertIn("if it differs from the approved diff", merge)

    def test_multi_pr_post_merge_verification_uses_the_confirmed_single_base_result(self):
        text = skill_reference("pr-and-merge", "multi-pr-batch.md").lower().replace(chr(96), "")
        verification = section(text, "## verify the merged base")

        self.assertIn("single-base multi-pr batch", verification)
        self.assertIn("a merge pass is one execution of its authorized ordered merge sequence", verification)
        self.assertIn("until all eligible merges are handled or the workflow pauses or stops", verification)
        self.assertIn("at the end of each merge pass", verification)
        self.assertIn("at least one pr targeting the base is confirmed", verification)
        self.assertIn("even if other batch entries remain unresolved", verification)
        self.assertIn("fetch the resolved target base branch from its remote", verification)
        self.assertIn("git fetch remote base_branch", verification)
        self.assertIn("fetched oid from fetch_head", verification)
        self.assertIn("do not use a stale local base ref", verification)
        self.assertIn("mark verification coverage as partial", verification)
        self.assertIn("record the fetched oid from fetch_head", verification)
        self.assertIn("create a new worktree", verification)
        self.assertIn("at that exact oid", verification)
        self.assertIn("track completed results by base ref and commit oid", verification)
        self.assertIn("do not rerun a completed result for the same base ref and commit oid solely because the batch resumed", verification)
        self.assertIn("user's explicit request", verification)
        self.assertIn("previously blocked or interrupted attempt after its cause is resolved", verification)
        self.assertIn("when a resumed batch produces a new resulting base commit", verification)
        self.assertIn("retain", verification)
        self.assertIn("only the test commands specified for the batch", verification)
        self.assertIn("base", verification)
        self.assertIn("tested commit", verification)
        self.assertIn("worktree path", verification)
        self.assertIn("exact command", verification)
        self.assertIn("exit status", verification)
        self.assertIn("separately from pr merge status", verification)
        self.assertIn("single-pr flow", verification)

    def test_multi_pr_post_merge_verification_tracks_each_confirmed_base_separately(self):
        text = skill_reference("pr-and-merge", "multi-pr-batch.md").lower().replace(chr(96), "")
        verification = section(text, "## verify the merged base")

        for requirement in (
            "when a batch targets multiple base refs",
            "group entries by their exact resolved target base ref",
            "each distinct base with at least one confirmed merged pr",
            "create a separate new retained worktree for each resulting base commit",
            "run the batch's confirmed test set separately in each eligible base worktree",
            "if a command's applicability to a base is unclear, ask the user before running it for that base",
            "report that base's verification as incomplete until applicability is resolved",
            "report the base ref, tested commit oid, retained worktree path, and each test outcome",
            "mark overall coverage as partial",
            "identify every unresolved entry",
        ):
            self.assertIn(requirement, verification)

    def test_multi_pr_multi_base_verification_resumes_only_new_or_retryable_results(self):
        text = skill_reference("pr-and-merge", "multi-pr-batch.md").lower().replace(chr(96), "")
        verification = section(text, "## verify the merged base")

        self.assertIn("record completed multi-base validation results by base ref, commit oid, and test command", verification)
        self.assertIn("when a resumed batch adds a confirmed merge", verification)
        self.assertIn("verify the new resulting base oid in a separate retained worktree", verification)
        self.assertIn("do not rerun a completed validation for the same base ref and commit oid solely because the batch resumed", verification)
        self.assertIn("retry a blocked or interrupted attempt only after its cause is resolved", verification)

    def test_manual_multi_base_verification_covers_partial_progress_and_resume(self):
        manual = (ROOT / "tests" / "manual" / "pr-and-merge.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## multi-pr batch: multiple target bases")

        for requirement in (
            "disposable repository",
            "two distinct target bases",
            "at least two prs for each of two distinct target bases",
            "separate retained worktree for each base",
            "mark overall coverage as partial",
            "asks before running a test command when its applicability to a base is unclear",
            "exact command and observed exit status",
            "failed command includes a concise relevant output excerpt when available",
            "reason for every test not run",
            "passed only after observing a successful exit status",
            "resume the batch",
            "new resulting base commit",
            "completed same-base and same-oid validation is not rerun",
        ):
            self.assertIn(requirement, scenario)

    def test_multi_pr_post_merge_verification_asks_before_running_without_test_commands(self):
        text = skill_reference("pr-and-merge", "multi-pr-batch.md").lower().replace(chr(96), "")
        verification = section(text, "## verify the merged base")

        self.assertIn("if no test commands are specified", verification)
        self.assertIn("ask before running any test command", verification)
        self.assertIn("do not infer a default test suite", verification)

        manual = (ROOT / "tests" / "manual" / "pr-and-merge.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## multi-pr batch: post-merge verification")
        self.assertIn("one pull request is confirmed as merged", scenario)
        self.assertIn("another remains pending or blocked", scenario)
        self.assertIn("at the end of that pass", scenario)
        self.assertIn("fetch the target branch from its remote", scenario)
        self.assertIn("fetched base oid", scenario)
        self.assertIn("label coverage as partial", scenario)
        self.assertIn("resume the batch without another merge", scenario)
        self.assertIn("completed result for that base ref and oid is not rerun", scenario)
        self.assertIn("new resulting base commit is fetched and verified separately", scenario)
        self.assertIn("specified test command", scenario)
        self.assertIn("no test commands", scenario)
        self.assertIn("asks before running any test command", scenario)

    def test_multi_pr_post_merge_verification_reports_failed_output_and_unrun_reasons(self):
        text = skill_reference("pr-and-merge", "multi-pr-batch.md").lower().replace(chr(96), "")
        verification = section(text, "## verify the merged base")

        self.assertIn("failed test command", verification)
        self.assertIn("concise relevant output excerpt", verification)
        self.assertIn("when available", verification)
        self.assertIn("reason for every test not run", verification)

        manual = (ROOT / "tests" / "manual" / "pr-and-merge.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## multi-pr batch: post-merge verification")
        self.assertIn("failed commands", scenario)
        self.assertIn("relevant output excerpt", scenario)
        self.assertIn("reason for every test not run", scenario)

    def test_multi_pr_post_merge_verification_only_reports_passed_after_success(self):
        text = skill_reference("pr-and-merge", "multi-pr-batch.md").lower().replace(chr(96), "")
        verification = section(text, "## verify the merged base")

        self.assertIn("do not report verification as passed unless a successful exit status was observed", verification)

        manual = (ROOT / "tests" / "manual" / "pr-and-merge.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## multi-pr batch: post-merge verification")
        self.assertIn("passed only after observing a successful exit status", scenario)

    def test_multi_pr_post_merge_verification_isolates_failures_by_scope(self):
        text = skill_reference("pr-and-merge", "multi-pr-batch.md").lower().replace(chr(96), "")
        isolation = section(text, "### isolate post-merge validation failures")

        for requirement in (
            "ordinary test failure",
            "continue with every remaining confirmed test command for that base",
            "every other independent base eligible for validation",
            "if verification worktree creation or test preparation fails",
            "confirms the cause is local to one base",
            "validation_blocked",
            "tests_not_run",
            "when evidence confirms a shared failure",
            "stop starting validations on all bases",
            "already-running commands finish or time out",
            "when the failure scope is unknown",
            "pause all new validations",
            "evidence needed to classify it",
            "commands still running",
            "confirmed tests not started",
            "start no validation until an operator classifies the failure",
            "if it is local to one base, continue unaffected bases and retry that base only after its cause is resolved",
            "if it is shared, wait until the failure is cleared",
            "keep validation outcomes separate from every pr's merge outcome",
        ):
            self.assertIn(requirement, isolation)

        manual = (ROOT / "tests" / "manual" / "pr-and-merge.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## multi-pr batch: post-merge validation failure isolation")
        for requirement in (
            "disposable repository",
            "ordinary test failure",
            "remaining confirmed command for that base",
            "independent base",
            "worktree creation to fail locally",
            "validation_blocked",
            "tests_not_run",
            "test-preparation failure",
            "shared runner or setup failure",
            "already-running commands finish or time out",
            "unknown-scope",
            "evidence needed to classify",
            "commands still running",
            "confirmed tests not started",
            "operator classifies",
            "classified as local to one base",
            "resume validation on unaffected bases",
            "retry that base only after its cause is resolved",
            "wait until the shared failure is cleared",
            "merge outcomes",
        ):
            self.assertIn(requirement, scenario)

        glossary = (ROOT / "GLOSSARY.md").read_text(encoding="utf-8").lower()
        self.assertIn("**validation-blocked base**", glossary)
        self.assertIn("confirmed local to that base", glossary)

    def test_pr_text_gate_follows_push_classification_and_precedes_writes(self):
        text = skill("pr-and-merge").lower().replace(chr(96), "")
        reuse = section(text, "## reuse or prepare the pr")
        prepare_heading = "### prepare or reuse pr text"
        preflight_heading = "### pr-text preflight before the first source push"
        prepare_start = reuse.index(prepare_heading)
        preflight_start = reuse.index(preflight_heading)
        first_fetch = reuse.index("git fetch remote head_branch")
        second_fetch = reuse.index("git fetch remote head_branch", first_fetch + 1)
        third_fetch = reuse.index("git fetch remote head_branch", second_fetch + 1)
        branch_check = reuse.index("git branch --show-current", preflight_start)
        head_check = reuse.index("git rev-parse head", preflight_start)
        push = reuse.index("git push remote head:refs/heads/head_branch")
        create_pr = reuse.index("gh pr create")
        edit_pr = reuse.index("gh pr edit")

        self.assertLess(first_fetch, prepare_start)
        self.assertLess(prepare_start, preflight_start)
        self.assertLess(preflight_start, branch_check)
        self.assertLess(preflight_start, head_check)
        self.assertLess(branch_check, second_fetch)
        self.assertLess(head_check, second_fetch)
        self.assertLess(second_fetch, push)
        self.assertLess(push, third_fetch)
        self.assertLess(third_fetch, create_pr)
        self.assertLess(third_fetch, edit_pr)
        self.assertLess(prepare_start, create_pr)
        self.assertLess(prepare_start, edit_pr)

    def test_github_scope_and_subskill_steps_remain_explicit(self):
        text = skill("pr-and-merge").lower().replace(chr(96), "")
        activation = section(text, "## activation criteria & objective")
        reuse = section(text, "## reuse or prepare the pr")
        merge_route = section(text, "## merge after approval")
        merge = skill_reference("pr-and-merge", "merge-after-approval.md").lower().replace(chr(96), "")
        self.assertIn("it handles github only", activation)
        drafting_rule = sentence_with_concepts(
            reuse, ("before drafting",), ("materially updating",), ("pr title",), ("body",),
            ("language rule",), ("root agents.md",), ("conventional-git-messages",),
        )
        self.assertTrue(drafting_rule)
        self.assertRegex(drafting_rule, r"\b(?:pass|read|follow|apply|use|provide)\b")
        self.assertNotRegex(
            drafting_rule,
            r"\b(?:do not|don't|does not|doesn't|never|must not|mustn't|"
            r"may not|will not|won't|would not|wouldn't|should not|shouldn't|"
            r"cannot|can't|is not|isn't|are not|aren't)\s+"
            r"(?:pass|read|follow|apply|use|provide)\b",
        )
        self.assertIn("delegate the title and body or only the necessary correction to /conventional-git-messages", reuse)
        self.assertIn("only when the user requests a merge", merge_route)
        self.assertIn("explicitly approves that exact pr", merge_route)
        self.assertIn("references/merge-after-approval.md", merge_route)
        self.assertIn("merge each pr only after the user explicitly approves that exact pr", merge)
        self.assertIn("immediately before each merge, recheck that pr's head and base", merge)
        self.assertIn("when an approved merge encounters a conflict, use /resolving-merge-conflicts", merge)


class PruneWorktreesBehaviorTests(unittest.TestCase):
    def test_unavailable_evidence_never_produces_safe_to_clean(self):
        text = skill("prune-worktrees-and-branches").lower().replace("*", "")
        self.assertIn("if a required github check is unavailable, do not mark the affected branch safe to clean", text)
        self.assertIn("unknown, failed, incomplete, or out-of-date evidence must never produce safe to clean", text)

    def test_cleanup_references_follow_their_separate_approval_gates(self):
        text = skill("prune-worktrees-and-branches").lower().replace("*", "")
        local_gate = section(text, "## apply approved local cleanup")
        remote_gate = section(text, "## apply separately approved remote cleanup")
        local = skill_reference("prune-worktrees-and-branches", "approved-local-cleanup.md").lower().replace("*", "").replace(chr(96), "")
        remote = skill_reference("prune-worktrees-and-branches", "approved-remote-branch-deletion.md").lower().replace("*", "").replace(chr(96), "")
        self.assertIn("ask for explicit approval of that local set", local_gate)
        self.assertIn("after approval of the exact local cleanup set", local_gate)
        self.assertIn("references/approved-local-cleanup.md", local_gate)
        self.assertIn("require an explicit pass for every item", remote_gate)
        self.assertIn("ask for explicit remote-deletion approval in a separate question", remote_gate)
        self.assertIn("after approval for exactly the reviewed remote, branch names, and oids", remote_gate)
        self.assertIn("references/approved-remote-branch-deletion.md", remote_gate)
        self.assertIn("git worktree remove <path>", local)
        self.assertIn("git branch -d -- <branch>", local)
        self.assertIn("git push <remote> --delete refs/heads/<branch>", remote)
        self.assertIn("never use --force", remote)


class GrillDuoBehaviorTests(unittest.TestCase):
    def test_summary_fields_and_reviewer_fallback_remain(self):
        text = skill("grill-duo").lower()
        self.assertIn("summarize the goal, confirmed decisions, constraints, and material risks", text)
        roles = section(text, "## roles and continuity")
        self.assertIn("only reviewer unavailability uses solo mode", roles)


class GrillDuoWithDocsBehaviorTests(unittest.TestCase):
    def test_delegates_protocol_and_keeps_host_as_document_writer(self):
        text = skill("grill-duo-with-docs").lower().replace(chr(96), "")
        activation = section(text, "## activation criteria & objective")
        self.assertIn("use /grill-duo for the grilling protocol", activation)
        self.assertIn("use /domain-modeling for glossary and decision discipline", activation)
        self.assertIn("do not copy either skill's body into this entrypoint", activation)


class SkillRoutePrerequisiteTests(unittest.TestCase):
    def test_cli_identity_and_callability_are_clear_across_affected_skills(self):
        for name in (
            "grill-duo",
            "grill-duo-with-docs",
            "pr-and-merge",
            "requirements-to-spec-tickets",
            "review-duo",
        ):
            with self.subTest(skill=name):
                dependencies = section(
                    skill(name).lower().replace(chr(96), ""), "## dependencies"
                )
                self.assertIn("skillroute cli executable (skillroute)", dependencies)
                self.assertIn("before starting the workflow", dependencies)
                self.assertIn("callable", dependencies)
                self.assertIn("https://github.com/erichare/skillroute", dependencies)


class RequirementsToSpecTicketsBehaviorTests(unittest.TestCase):
    def test_child_prompt_template_is_referenced_and_contains_the_handoff_contract(self):
        parent = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        filename = "child-session-initial-prompt.md"
        reference = f"references/{filename}"
        self.assertIn(reference, parent)

        template = skill_reference("requirements-to-spec-tickets", filename).lower().replace(chr(96), "")
        fill_instructions = section(template, "## fill instructions")
        copy_ready = template[template.index("# copy-ready prompt (below):"):]
        group = section(template, "## approved group")
        startup = section(template, "## first response and grilling gate")
        workflow = section(template, "## workflow gates")
        linking = section(template, "### native ticket linking")
        boundaries = section(template, "## boundaries and completion")

        for placeholder in (
            "[group title]", "[approved outcome]", "[approved scope]", "[non-goals]",
            "[acceptance intent]", "[target repository]", "[workspace path and branch]",
            "[required dependencies]", "[known group dependencies]",
            "[target repository root agents.md language rule]",
            "[shared workspace and write-authorization rules]",
        ):
            with self.subTest(placeholder=placeholder):
                self.assertIn(placeholder, group)

        self.assertTrue(sentence_with_concepts(
            fill_instructions, ("placeholder",), ("fill", "replace"), ("before",), ("handoff", "start"),
        ))
        self.assertTrue(sentence_with_concepts(
            fill_instructions, ("confirmed information", "confirmed facts"), ("do not", "never"), ("invent",),
        ))
        self.assertTrue(sentence_with_concepts(
            fill_instructions, ("sibling requirements",), ("exclude", "omit", "leave out"),
        ))
        self.assertTrue(sentence_with_concepts(
            fill_instructions, ("unrelated parent history",), ("exclude", "omit", "leave out"),
        ))
        self.assertNotIn("example", copy_ready)

        self.assertTrue(sentence_with_concepts(
            startup, ("first response",), ("restate",), ("outcome",), ("scope",), ("non-goals",),
            ("workflow constraints",),
        ))
        self.assertTrue(sentence_with_concepts(
            startup, ("complete-grouping approval",), ("already",), ("authorizes",),
            ("workflow",), ("do not", "don't", "never"), ("opt-in",),
        ))
        self.assertTrue(sentence_with_concepts(
            startup, ("grill-duo-with-docs",), ("answerable frontier",), ("wait",), ("user",),
        ))
        self.assertTrue(sentence_with_concepts(
            startup, ("no answerable questions", "frontier is empty"), ("shared-understanding summary",),
            ("wait",), ("confirmation",),
        ))

        phases = ("/grill-duo-with-docs", "/to-spec", "/spec-review", "/to-tickets")
        for phase in phases:
            self.assertIn(phase, workflow)
        self.assertLess(workflow.index(phases[0]), workflow.index(phases[1]))
        self.assertLess(workflow.index(phases[1]), workflow.index(phases[2]))
        self.assertLess(workflow.index(phases[2]), workflow.index(phases[3]))
        self.assertTrue(sentence_with_concepts(
            workflow, ("re-read", "reread"), ("source",), ("each phase",), ("before",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("phase source",), ("unavailable",), ("report",), ("pause",), ("phase",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("phase source",), ("independent",), ("eligible",), ("in-scope work",),
            ("continue",), ("phase order",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("global prerequisite",), ("missing",), ("report",), ("all",),
            ("dependencies",), ("tell the user",), ("install them",), ("stop",),
            ("entire workflow",), ("automatically",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("grill-duo-with-docs",), ("confirmation",),
            ("shared project-document changes",), ("before",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("to-spec",), ("seam",), ("confirmation", "gate"),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("spec-review",), ("staged",), ("before",), ("issue publication",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("to-tickets",), ("ticket-granularity", "granularity"),
            ("blocking-edge", "blocking edge"), ("publication",), ("gate", "confirmation"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("after all planned tickets exist",), ("publication gates",), ("pass",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("required permissions are unavailable",), ("report the blocker",), ("stop",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("before each write", "before each link"), ("ticket exists",),
            ("current parent", "parent endpoint"), ("fully paginate",), ("spec",), ("sub-issues",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("already complete", "already linked"), ("both reads", "both endpoints"),
            ("same spec",), ("skip",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("404",), ("ticket exists",), ("spec",), ("sub-issues read succeeds",),
            ("must not contain", "does not contain"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("different parent",), ("disagree", "cannot establish"), ("pause",),
            ("never reparent",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("failed or ambiguous",), ("re-read", "reread"), ("both relationships",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("clearly transient",), ("three total", "at most three"),
            ("write attempts",), ("per link",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("record", "count"), ("attempt",), ("before each write", "before every retry"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("preserve",), ("ticket and spec issue titles",), ("bodies",), ("labels",),
            ("states",), ("blocker edges", "blocking edges"), ("record",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("before linking, record",), ("after linking, verify",),
            ("ticket and spec issue titles",), ("bodies",), ("labels",), ("states",),
            ("blocker edges", "blocking edges"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("verify",), ("native parent relationship",),
            ("re-read", "reread"), ("spec sub-issues list", "spec's sub-issues list"),
            ("paginate", "paginating"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("report links",), ("succeeded",), ("remain pending",),
        ))
        language_rule = sentence_with_concepts(
            workflow, ("target repository",), ("root agents.md",), ("language rule",), ("pass",),
        )
        self.assertTrue(language_rule)
        for phase in (*phases, "/conventional-git-messages"):
            self.assertIn(phase, language_rule)
        self.assertTrue(sentence_with_concepts(
            workflow, ("shared workspace",), ("write-authorization rules", "write authorization rules"),
            ("preserve", "follow", "carry"),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("conventional-git-messages",), ("re-read", "reread"), ("original",), ("before",),
        ))

        self.assertTrue(sentence_with_concepts(
            boundaries, ("user-facing questions",), ("must not", "do not", "never"),
            ("answer",), ("user",),
        ))
        self.assertTrue(sentence_with_concepts(
            boundaries, ("parent",), ("readiness",), ("handoff",), ("retry",), ("resumption",),
        ))
        self.assertTrue(sentence_with_concepts(
            boundaries, ("prompt", "child-session identifier"), ("alone",), ("readiness",),
            ("does not establish", "not evidence", "does not prove"),
        ))
        self.assertTrue(sentence_with_concepts(
            boundaries, ("completion report",), ("actual status",), ("completed phases",),
            ("artifacts", "outputs"), ("blockers",),
        ))

    def test_local_artifact_document_integration_handoff_is_scoped(self):
        workflow = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        prompt = skill_reference(
            "requirements-to-spec-tickets", "child-session-initial-prompt.md",
        ).lower().replace(chr(96), "")
        manual = (
            ROOT / "tests" / "manual" / "requirements-to-spec-tickets.md"
        ).read_text(encoding="utf-8").lower()
        workflow_handoff = section(workflow, "### optional document integration follow-up")
        prompt_handoff = section(prompt, "### optional document integration follow-up")
        scenario = section(manual, "## optional post-workflow document integration")
        overwrite_guard = (("do not overwrite", "never overwrite"), ("destination work",))
        push_guard = (
            ("still requires",),
            ("separate explicit confirmation",),
            ("grilling confirmation", "existing grilling step"),
        )

        for handoff in (workflow_handoff, prompt_handoff):
            self.assertTrue(sentence_with_concepts(
                handoff, ("summary",), ("task branch",), ("exact document paths",),
                ("proposed destination branch",), ("before",), ("ask", "asking"),
            ))
            self.assertTrue(sentence_with_concepts(
                handoff, ("approved generated document set",), ("only",),
            ))
            self.assertTrue(sentence_with_concepts(
                handoff, ("affirmative",), ("authorizes",), ("only",),
                ("listed documents",), ("named destination branch",),
                ("focused local commit",), ("does not extend", "doesn't extend"),
                ("task-branch grant",),
            ))
            self.assertTrue(sentence_with_concepts(
                handoff, ("declining", "decline"), ("no clear authorization",),
                ("destination unchanged",), ("task branch",),
            ))
            self.assertTrue(sentence_with_concepts(
                handoff, ("same host agent",), ("same conversation",),
                ("do not", "never"), ("new conversation",), ("subagent",),
            ))
            self.assertTrue(sentence_with_concepts(
                handoff, ("destination is unclear",), ("unrelated changes",),
                ("conflicts",), ("stop",), ("overwrite",),
            ))
            self.assertTrue(sentence_with_concepts(handoff, *overwrite_guard))
            self.assertTrue(sentence_with_concepts(
                handoff, ("destination push", "pushing the destination branch"), ("separate",),
                ("explicit",), ("grilling confirmation", "confirmation from the existing grilling step"),
            ))
            self.assertTrue(sentence_with_concepts(handoff, *push_guard))

        self.assertFalse(sentence_with_concepts("do overwrite destination work", *overwrite_guard))
        self.assertFalse(sentence_with_concepts(
            "the integration authorization does not authorize pushing the destination branch; pushing it does not require the separate explicit confirmation from the existing grilling step",
            *push_guard,
        ))
        self.assertTrue(sentence_with_concepts(
            workflow_handoff, ("does not authorize pushing the destination branch",),
        ))

        self.assertTrue(sentence_with_concepts(
            workflow_handoff, ("issue-only",), ("application-code branch policy",),
            ("unchanged",),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("disposable repository",), ("authorized",), ("declined",),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("commit",), ("dev",), ("only the listed documents",),
            ("task branch",), ("sentinel",),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("issue-only",), ("application-code branch policy",), ("unchanged",),
        ))
        self.assertTrue(mentions_concepts(
            scenario, ("unclear", "no uniquely identified destination"),
            ("unrelated changes",), ("conflicts",), ("stop",),
        ))

    def test_complete_group_approval_starts_documentation_phase(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        grouping = section(text, "## 2. turn the request into groups")
        protocol = section(text, "## 4. child-session protocol")
        git = section(text, "## 5. task branches and git publication")
        documents = section(text, "## 6. shared workspace and document writes")
        self.assertTrue(sentence_with_concepts(
            grouping, ("complete", "entire", "whole"), ("grouping", "groups"),
            ("approval", "approved"), ("wait", "pause"),
        ))
        self.assertTrue(sentence_with_concepts(
            grouping, ("approval",), ("group",), ("start", "begin"), ("grill-duo-with-docs",),
        ))
        self.assertTrue(sentence_with_concepts(
            grouping, ("group", "grouping"), ("no", "without", "not"), ("opt-in", "opt in"),
        ))
        self.assertTrue(sentence_with_concepts(
            protocol, ("group",), ("grill-duo-with-docs",), ("invoke", "run"),
        ))
        self.assertTrue(sentence_with_concepts(
            protocol, ("frontier",), ("empty", "no answerable questions"),
            ("shared-understanding", "summary"), ("wait", "pause"), ("confirmation", "confirm"),
        ))
        sequence = sentence_with_concepts(
            protocol, ("grill-duo-with-docs",), ("to-spec",), ("spec-review",), ("to-tickets",),
            ("first", "before", "prior"), ("then", "next", "order"),
        )
        self.assertTrue(sequence)
        self.assertLess(sequence.index("grill-duo-with-docs"), sequence.index("to-spec"))
        self.assertLess(sequence.index("to-spec"), sequence.index("spec-review"))
        self.assertLess(sequence.index("spec-review"), sequence.index("to-tickets"))
        self.assertLess(sequence.index("to-spec"), sequence.index("to-tickets"))
        self.assertTrue(sentence_with_concepts(git, ("approval", "authorize"), ("group",), ("commit",)))
        self.assertTrue(sentence_with_concepts(documents, ("user-confirmed",), ("project documents",)))

    def test_phase_sources_and_global_prerequisites_have_distinct_failure_scopes(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        dependencies = section(text, "## dependencies")
        protocol = section(text, "## 4. child-session protocol")
        phase_rules = protocol.split("the first response must", 1)[0]

        self.assertTrue(mentions_concepts(dependencies, ("skill",), ("tool",)))
        self.assertTrue(sentence_with_concepts(
            dependencies, ("missing",), ("report",), ("stop", "halt"),
        ))
        no_auto_install = sentence_with_concepts(
            dependencies, ("install",), ("not", "never", "without"), ("automatic", "automatically"),
        )
        self.assertTrue(no_auto_install)
        self.assertRegex(no_auto_install, AUTO_INSTALL_PROHIBITION)
        self.assertTrue(sentence_with_concepts(
            phase_rules, ("source",), ("phase",), ("pause", "hold"),
        ))
        self.assertTrue(independent_work_continuation(phase_rules))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase and also pauses every independent eligible phase."
        ))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase and the independent eligible phase is not allowed to continue."
        ))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase, but the unrelated eligible phase will not proceed."
        ))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase, but the unrelated eligible phase is blocked from continuing."
        ))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase, but the unrelated eligible phase is unable to continue."
        ))
        self.assertTrue(sentence_with_concepts(
            phase_rules, ("source",), ("resume", "resuming"), ("re-read", "reread", "check again"),
        ))
        global_rule = sentence_with_concepts(
            phase_rules, ("global", "prerequisite"), ("stop", "halt"), ("install",),
            ("not", "never", "without"),
        )
        self.assertTrue(global_rule)
        self.assertRegex(global_rule, AUTO_INSTALL_PROHIBITION)

        manual = (ROOT / "tests" / "manual" / "requirements-to-spec-tickets.md").read_text(encoding="utf-8").lower()
        phase_scenario = section(manual, "## phase-scoped source failure")
        global_scenario = section(manual, "## missing global dependencies")
        self.assertTrue(sentence_with_concepts(
            phase_scenario, ("source",), ("phase",), ("pause", "hold"),
        ))
        self.assertTrue(independent_work_continuation(phase_scenario))
        self.assertTrue(sentence_with_concepts(
            phase_scenario, ("source",), ("resume", "resuming"), ("re-read", "reread", "check again"),
        ))
        phase_install_rule = sentence_with_concepts(
            phase_scenario, ("install",), ("automatic", "automatically"), ("not", "never", "without"),
        )
        self.assertTrue(phase_install_rule)
        self.assertRegex(phase_install_rule, AUTO_INSTALL_PROHIBITION)
        self.assertTrue(sentence_with_concepts(
            global_scenario, ("skill",), ("tool",), ("preflight",),
        ))
        global_install_rule = sentence_with_concepts(
            global_scenario, ("report", "identify"), ("stop", "halt"), ("install",),
            ("not", "never", "without"), ("automatic", "automatically"),
        )
        self.assertTrue(global_install_rule)
        self.assertRegex(global_install_rule, AUTO_INSTALL_PROHIBITION)

    def test_task_publication_authorization_is_scoped_and_preserves_other_gates(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        protocol = section(text, "## 4. child-session protocol")
        git = section(text, "## 5. task branches and git publication")
        target_policy = section(text, "## 3. create interactive child sessions")

        self.assertTrue(sentence_with_concepts(
            protocol, ("missing", "unavailable"), ("dependency", "prerequisite"),
            ("install",), ("stop", "halt"),
        ))
        self.assertTrue(sentence_with_concepts(
            target_policy, ("normative", "policy"), ("root",), ("agents.md",),
            ("repository",), ("receiving", "target"),
        ))
        self.assertTrue(sentence_with_concepts(
            target_policy, ("source", "installation"), ("agents.md",), ("substitute", "replace"),
        ))

        decision = (
            ROOT / "docs" / "adr" / "0003-task-scoped-write-authorization.md"
        ).read_text(encoding="utf-8").lower()
        self.assertTrue(sentence_with_concepts(
            decision, ("status",), ("root",), ("repository",), ("ticket",), ("checkpoint",),
        ))
        self.assertTrue(sentence_with_concepts(
            decision, ("every other",), ("git",), ("github",), ("write",),
            ("existing",), ("approval gate",),
        ))
        self.assertTrue(permission_clause(
            "Existing group authorization permits force-pushes to other branches.".lower(),
            ("existing",), ("group",), ("authorization",), ("force-push", "force push"),
            ("other branch",),
        ))
        self.assertFalse(permission_clause(
            "Force-pushes require separate approval, but a user may separately authorize them.".lower(),
            ("existing", "current"), ("group",), ("authorization",), ("force-push", "force push"),
            ("other branch",),
        ))

        allowed = authorization_grant_clause(
            git, ("group",), ("commit",), ("push",), ("branch",),
            ("ordinary", "normal", "non-force", "routine"),
            ("initial", "first"), ("remote ref", "remote branch"),
        )
        self.assertTrue(allowed)
        self.assertTrue(mentions_concepts(
            allowed, ("ordinary", "normal", "non-force", "routine"), ("initial", "first"),
            ("remote ref", "remote branch"),
        ))
        scope = sentence_with_concepts(
            git, ("authorization",), ("limited", "only", "restricted", "confined"),
            ("group",), ("branch",), ("unrelated", "other groups"), ("task",),
        )
        self.assertTrue(scope)
        self.assertTrue(mentions_concepts(
            scope, ("unrelated", "other groups"), ("task",),
        ))
        self.assertRegex(scope, TASK_AUTHORIZATION_LIMIT)

        denied = sentence_with_concepts(
            git, ("force-push", "force push"), ("remote-ref", "remote ref", "remote reference"),
            ("delete", "deletion", "remove"), ("other branch", "different branch"), ("pull request", "pull-request"),
            ("issue",), ("status",), ("sub-issue", "sub issue"), ("github",), ("write",),
            ("separate approval",), ("retain", "require", "need", "necessary", "must"),
        )
        self.assertTrue(denied)
        self.assertRegex(
            denied,
            (
                r"\b(?:retain(?:s)?|require(?:s)?|need(?:s)?|must have|must retain)\b"
                r".*\b(?:separate|additional|own)\s+approval\b"
            ),
        )
        self.assertFalse(permission_clause(
            denied, ("current", "same", "approved", "existing"),
            ("group", "task", "branch"), ("authorization", "approval"),
            ("force-push", "force push", "remote-ref deletion", "remote ref deletion",
             "other branch", "pull request", "issue creation", "status change", "comment",
             "label", "sub-issue", "github write"),
        ))

    def test_authorization_contract_accepts_paraphrases_and_rejects_broadening(self):
        grant = (
            "Full-group approval permits routine commits and normal pushes on the group's "
            "dedicated task branch, including the initial remote ref."
        )
        self.assertTrue(sentence_with_concepts(
            grant, ("approval", "authorization"), ("grant", "authorize", "permit", "allow"),
            ("group",), ("commit",), ("push",), ("task branch", "dedicated branch"),
            ("ordinary", "normal", "routine"), ("initial", "first"), ("remote ref", "remote branch"),
        ))
        self.assertTrue(authorization_grant_clause(
            grant, ("group",), ("commit",), ("push",), ("task branch", "dedicated branch"),
            ("ordinary", "normal", "routine"), ("initial", "first"), ("remote ref", "remote branch"),
        ))

        combined_boundary = (
            "Group approval permits routine commits and ordinary pushes on the dedicated task branch, "
            "but does not permit pushes to another branch."
        )
        self.assertTrue(authorization_grant_clause(
            combined_boundary, ("routine",), ("commit",), ("push",), ("task branch",),
        ))
        self.assertTrue(authorization_grant_clause(
            "Group approval permits routine commits and ordinary pushes on its task branch, "
            "and force-pushes require separate approval.",
            ("routine",), ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Group approval authorizes review, while commits and pushes on the task branch need separate approval.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Group approval authorizes review, and commits and pushes on the task branch require separate approval.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Group approval authorizes document work, with commits and pushes on its task branch "
            "requiring separate approval.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Group approval authorizes document work, with routine commits and pushes on its task branch, "
            "and these require separate approval.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Approval is insufficient to authorize focused group commits and normal pushes on the dedicated task branch, "
            "including the initial remote ref.",
            ("commit",), ("push",), ("task branch",), ("initial",), ("remote ref",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Approval alone is insufficient to authorize focused group commits and normal pushes on the dedicated task branch.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertTrue(authorization_grant_clause(
            "After group B receives its own approval, that approval permits B to write files, commit, "
            "and push only on B's dedicated task branch.".lower(),
            ("write",), ("commit",), ("push",),
            ("only",), ("dedicated task branch",),
        ))
        paraphrased_denial = (
            "Before separate approval, group B is never authorized to write files, commit, or push "
            "under A's approval."
        ).lower()
        self.assertTrue(sentence_with_concepts(
            paraphrased_denial, ("group b",), ("before",), ("separate approval",),
            ("write",), ("commit",), ("push",), ("under a's approval",),
        ))
        self.assertRegex(paraphrased_denial, TASK_ACTION_DENIAL)

        removed_branch = "Group approval permits routine commits and normal pushes, including the initial push."
        self.assertFalse(sentence_with_concepts(
            removed_branch, ("approval",), ("commit",), ("push",), ("task branch", "dedicated branch"),
        ))

        limited = (
            "Authorization is confined to this group's task branch and cannot transfer to other groups "
            "or later tasks."
        ).lower()
        self.assertTrue(sentence_with_concepts(
            limited, ("authorization",), ("limited", "restricted", "confined"),
            ("group",), ("branch",), ("other groups", "unrelated"), ("task",),
        ))
        self.assertRegex(limited, TASK_AUTHORIZATION_LIMIT)

        broadened = "Authorization extends to every group, task, and branch.".lower()
        self.assertFalse(sentence_with_concepts(
            broadened, ("limited", "restricted", "confined"), ("other groups", "unrelated"),
            ("task",),
        ))
        self.assertNotRegex(broadened, TASK_AUTHORIZATION_LIMIT)

    def test_manual_multiple_groups_covers_authorization_non_carryover(self):
        manual = (ROOT / "tests" / "manual" / "requirements-to-spec-tickets.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## multiple groups in a shared checkout")
        self.assertTrue(sentence_with_concepts(
            scenario, ("group a",), ("only",), ("a's task branch", "group a's branch"),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("group b",), ("only",), ("b's dedicated task branch", "group b's branch"),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("group b",), ("unapproved", "not approved", "without approval"),
        ))
        b_grant = authorization_grant_clause(
            scenario, ("write",), ("commit",), ("push",),
            ("b's dedicated task branch", "group b's branch"),
        )
        self.assertTrue(b_grant)
        self.assertTrue(mentions_concepts(
            b_grant, ("group b", "b's"), ("separate approval", "own approval"), ("only",),
        ))
        no_carry_rule = sentence_with_concepts(
            scenario, ("group b",), ("before", "until"), ("separate approval",),
            ("cannot", "can't", "must not", "may not", "prohibited", "never authorized",
             "isn't authorized", "is not authorized", "not permitted"),
            ("write", "writing", "files"),
            ("commit",), ("push",), ("under a's approval", "under a's authorization"),
            ("separate approval", "own approval"),
        )
        self.assertTrue(no_carry_rule)
        self.assertRegex(
            no_carry_rule,
            (
                r"\b(?:cannot|can't|must not|may not)\s+(?:write|writing|commit|push)\b"
                r"|\b(?:does not|doesn't|cannot|can't|must not)\s+(?:authorize|permit|allow|cover)\b"
                r"|\b(?:never|isn't|is not|aren't|are not|not)\s+"
                r"(?:authorized|permitted|allowed)\b"
            ),
        )
        self.assertNotRegex(
            no_carry_rule,
            r"\b(?:cannot|can't)\s+be\s+(?:blocked|prevented|stopped|prohibited|barred)\b",
        )
        self.assertFalse(permission_clause(
            scenario, ("group b",), ("under a's approval", "under a's authorization"),
            ("write", "writing", "commit", "push"),
        ))
        self.assertFalse(permission_clause(
            "Group B may write under its own approval, not under A's approval.".lower(),
            ("group b",), ("under a's approval",), ("write",),
        ))
        self.assertFalse(permission_clause(
            "Group B may not write under A's approval.".lower(),
            ("group b",), ("under a's approval",), ("write",),
        ))
        for denial in (
            "Group B is never authorized to write under A's approval.",
            "Group B isn't authorized to write under A's approval.",
        ):
            self.assertFalse(permission_clause(
                denial.lower(), ("group b",), ("under a's approval",), ("write",),
            ))
        self.assertTrue(permission_clause(
            "Group B may write under A's approval.".lower(),
            ("group b",), ("under a's approval",), ("write",),
        ))


    def test_spec_publication_stages_reviews_and_binds_both_approvals_to_exact_tuple(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        dependencies = section(text, "## dependencies")
        protocol = section(text, "## 4. child-session protocol")
        workflow = protocol

        self.assertIn("| /spec-review | skill |", dependencies)
        self.assertIn("if /to-spec can reliably stop before creating or publishing an issue", workflow)
        self.assertIn("if it cannot reliably stop, use its seam-confirmation criteria and draft template without invoking its publishing step", workflow)
        self.assertIn("exact draft text and a unique temporary path", workflow)
        self.assertIn("approval of that text and authorization for that path", workflow)
        self.assertIn("stage it with create-new semantics", workflow)
        self.assertLess(workflow.index("after seam confirmation"), workflow.index("run /spec-review"))
        self.assertLess(workflow.index("run /spec-review"), workflow.index("before publication"))
        self.assertIn("run /spec-review on the staged bytes before any issue publication", workflow)
        self.assertIn("a candidate is applied only after approval of the exact batch, source version, and unique destination", workflow)
        self.assertIn("run fresh review in the same named cycle", workflow)
        self.assertIn("at most three numbered rounds", workflow)
        self.assertIn("review pass, candidate approval, and staging approval do not approve the final spec", workflow)
        self.assertIn("the issue body must be byte-identical to the frozen draft", workflow)
        self.assertIn("obtain final specification approval and publication authorization as separate user decisions", workflow)
        self.assertIn("publish only after both approval records are present and still match that tuple", workflow)
        for tuple_field in ("title", "draft sha-256", "canonical owner/repository", "required labels"):
            with self.subTest(tuple_field=tuple_field):
                self.assertIn(tuple_field, workflow)
        self.assertIn("any body-byte change requires a fresh review round and new approvals", workflow)
        self.assertIn("any title, target, or required-label change invalidates both approvals", workflow)
        self.assertIn("do not invoke /to-tickets until review coverage passed, both exact final approvals were recorded, and spec publication succeeded", workflow)

    def test_issue_and_label_publication_requires_writer_claim_and_terminal_reconciliation(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        protocol = section(text, "## 4. child-session protocol")
        claims = section(protocol, "### exclusive github writer claim and publication recovery")

        for write in ("issue create/edit", "repository-label create", "issue-label change", "ticket-link write"):
            with self.subTest(write=write):
                self.assertIn(write, claims)
        for claim_fact in (
            "atomic exclusive writer claim", "canonical owner/repository", "exact approved spec-publication tuple",
            "exact ticket payload", "exact ticket relationship graph", "claim owner's host/session id",
            "unique operation id", "task progress summary before the external write",
            "no second session may write", "active or unresolved", "release a claim only after terminal read-back reconciliation",
            "takeover only after the prior owner has stopped", "every operation it owns has been reconciled",
        ):
            with self.subTest(claim_fact=claim_fact):
                self.assertIn(claim_fact, claims)
        self.assertIn("summary is a record, not a substitute for an atomic claim", claims)
        self.assertIn("verify the canonical target immediately before writing", claims)
        self.assertIn("fully paginate issues across all states, exclude pull requests", claims)
        self.assertIn("accept only one unique issue whose target, title, and body bytes match", claims)
        self.assertIn("retry only a confirmed transient failure after a complete listing proves no issue was created", claims)
        self.assertIn("at most three total attempts across resumes", claims)
        self.assertIn("keep at most one unresolved issue-create operation per canonical target and approved tuple", claims)
        self.assertIn("after issue read-back, create and verify required repository labels", claims)
        self.assertIn("with ready-for-agent last", claims)
        self.assertIn("track a unique operation id and cumulative attempt state for each label operation", claims)
        self.assertIn("reconcile ambiguous label results by reading the label and issue back", claims)
        self.assertIn("spec publication is successful only after the exact issue and all required labels are verified by read-back", claims)

    def test_ticket_reconciliation_binds_exact_payload_graph_and_stops_on_drift(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        protocol = section(text, "## 4. child-session protocol")
        reconciliation = section(protocol, "### ticket reconciliation and native links")
        template = skill_reference(
            "requirements-to-spec-tickets", "child-session-initial-prompt.md",
        ).lower().replace(chr(96), "")
        linking = section(template, "### native ticket linking")

        self.assertIn("obtain the user's explicit authorization for ticket reconciliation", reconciliation)
        self.assertIn("do not invoke /to-tickets until review coverage passed, both exact final approvals were recorded, and spec publication succeeded", reconciliation)
        self.assertIn("reconcile existing spec-review tickets by exact known issue ids", reconciliation)
        for field in ("title", "body", "state", "labels", "parent", "blocking edges"):
            with self.subTest(field=field):
                self.assertIn(field, reconciliation)
        for disposition in ("unchanged", "revised", "superseded", "new"):
            with self.subTest(disposition=disposition):
                self.assertIn(disposition, reconciliation)
        self.assertIn("obtain separate approval for each later ticket-payload or graph/link delta", reconciliation)
        for bound_value in ("parent spec issue id", "exact approved body sha-256", "canonical owner/repository", "exact ticket payload", "graph/link delta"):
            with self.subTest(bound_value=bound_value):
                self.assertIn(bound_value, reconciliation)
        self.assertIn("bind both records to the parent spec issue id", reconciliation)
        self.assertIn("bound to the same parent issue id, body hash, and canonical target", reconciliation)
        self.assertIn("ticket-set approval alone authorizes no write", reconciliation)
        self.assertIn("ticket-set approval alone authorizes no write: create only after the separate issue-creation authorization", reconciliation)
        self.assertIn("on the safe /to-tickets path, its publication confirmation serves as the separate issue-creation authorization", reconciliation)
        self.assertIn("in the template fallback, obtain this explicit authorization directly", reconciliation)
        self.assertIn("before any native link write, present the exact proposed edges and canonical target", reconciliation)
        self.assertIn("obtain separate explicit link authorization, distinct from both ticket-set approval and issue-creation authorization", reconciliation)
        self.assertIn("bind it to the parent spec issue id, exact approved body sha-256, canonical target, and exact graph", reconciliation)
        self.assertIn("issue-creation authorization never permits links; if only it exists, do not link", reconciliation)
        self.assertIn("every affected ticket-payload or graph/link-delta approval, and any independent link-write authorization", reconciliation)
        self.assertIn("re-preview the exact publication tuple, affected ticket proposal, and exact edges plus canonical target", reconciliation)
        self.assertIn("explicit link authorization bound to the parent issue id, body hash, canonical target, and exact graph as applicable", reconciliation)
        self.assertIn("each write also requires its own writer claim and applicable publication or relationship gate", reconciliation)
        self.assertIn("create only tickets confirmed missing by exact-id reconciliation and covered by the exact ticket-set approval and separate issue-creation authorization", reconciliation)
        self.assertIn("start native sub-issue linking only after every planned ticket exists", reconciliation)
        self.assertIn("before every ticket create, edit, label change, or link write, re-read the parent spec issue", reconciliation)
        self.assertIn("re-read the parent spec issue using its exact approved issue id", reconciliation)
        self.assertIn("if any differs, stop and invalidate both final spec approvals", reconciliation)
        self.assertIn("require that round to pass before re-previewing or requesting, binding, or recording any replacement approval or write authorization", reconciliation)
        self.assertIn("read the ticket immediately before writing and compare its exact current state", reconciliation)
        self.assertIn("drift stops the write until the new exact delta is approved", reconciliation)
        self.assertIn("verify the repository of every involved issue", reconciliation)
        self.assertIn("immediately before each write", reconciliation)
        self.assertIn("immediately after each write", reconciliation)
        self.assertIn("read every involved issue back immediately after each write", reconciliation)
        self.assertIn("approval of a planned ticket set alone authorizes no issue creation, edit, label change, or link", linking)
        self.assertIn("issue-creation authorization alone never permits a link", linking)
        self.assertIn("any independent link-write authorization", template)
        self.assertIn("explicit link authorization bound to the parent issue id, body hash, canonical target, and exact graph as applicable", template)
        self.assertIn("atomic writer claim for the exact approved graph/link delta", linking)
        self.assertNotIn("approval of the planned ticket set authorizes only these routine associations", text + template)

        manual = " ".join(
            (ROOT / "tests" / "manual" / "requirements-to-spec-tickets.md")
            .read_text(encoding="utf-8").lower().split()
        )
        for heading in (
            "## staged spec review and final publication gates",
            "## publication recovery and exclusive writer claims",
            "## exact-id ticket reconciliation and link approvals",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, manual)
        for scenario in (
            "second session", "lost create response", "exact body bytes", "ticket-payload batch",
            "relationship graph", "approved body sha-256", "immediately before and after each write",
            "all required labels are confirmed by read-back", "separate explicit link authorization",
            "link authorization is bound to the parent spec issue id", "issue-creation authorization alone never permits links",
            "independent link-write authorization is invalidated", "re-present the exact edges and canonical target",
            "fresh link authorization bound to the parent issue id/hash/target/graph before any link",
        ):
            with self.subTest(scenario=scenario):
                self.assertIn(scenario, manual)


    def test_to_tickets_requires_safe_pause_or_nonpublishing_ticket_set_staging(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        protocol = section(text, "## 4. child-session protocol")
        reconciliation = section(protocol, "### ticket reconciliation and native links")
        template = skill_reference(
            "requirements-to-spec-tickets", "child-session-initial-prompt.md",
        ).lower().replace(chr(96), "")
        template_gates = section(template, "## workflow gates")
        manual = " ".join(
            (ROOT / "tests" / "manual" / "requirements-to-spec-tickets.md")
            .read_text(encoding="utf-8").lower().split()
        )

        self.assertIn("prove that the workflow can return its ticket plan and reliably stop before any issue create, edit, label, or link write", reconciliation)
        self.assertIn("if it cannot, do not invoke its publishing step", reconciliation)
        self.assertIn("use its existing ticket-granularity, blocking-edge criteria, and template", reconciliation)
        self.assertIn("freeze the same proposal in task progress without publishing", reconciliation)
        for proposal_field in ("each proposed title", "body", "canonical target", "required labels", "exact blocking edges"):
            with self.subTest(proposal_field=proposal_field):
                self.assertIn(proposal_field, reconciliation)
        self.assertIn("obtain exact ticket-set approval, then separately obtain explicit issue-creation authorization", reconciliation)
        for bound_value in ("parent spec issue id", "exact approved body sha-256", "canonical owner/repository target", "exact ticket payload plus graph"):
            with self.subTest(bound_value=bound_value):
                self.assertIn(bound_value, reconciliation)
        self.assertIn("prove it can return the ticket plan and reliably stop before any issue write", template_gates)
        self.assertIn("if it cannot, do not invoke its publishing step", template_gates)
        self.assertIn("use its existing criteria and template to prepare and freeze the exact ticket set", template_gates)
        self.assertIn("exact ticket-set approval, then separately obtain explicit issue-creation authorization", template)
        self.assertIn("bind both records to the parent spec issue id", template)
        for manual_fact in (
            "prove it can stop before any issue write", "stage the exact ticket set in task progress",
            "separately obtain explicit issue-creation authorization", "ticket-payload batch plus relationship graph",
        ):
            with self.subTest(manual_fact=manual_fact):
                self.assertIn(manual_fact, manual)

    def test_parent_drift_invalidates_ticket_gates_and_field_edge_writes_are_reconciled(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        protocol = section(text, "## 4. child-session protocol")
        reconciliation = section(protocol, "### ticket reconciliation and native links")
        template = skill_reference(
            "requirements-to-spec-tickets", "child-session-initial-prompt.md",
        ).lower().replace(chr(96), "")
        workflow = section(template, "## workflow gates")
        manual = " ".join(
            (ROOT / "tests" / "manual" / "requirements-to-spec-tickets.md")
            .read_text(encoding="utf-8").lower().split()
        )

        for invalidated in (
            "both final spec approvals", "ticket-set approval", "separate issue-creation authorization",
            "every affected ticket-payload or graph/link-delta approval", "any independent link-write authorization",
        ):
            with self.subTest(invalidated=invalidated):
                self.assertIn(invalidated, reconciliation)
        self.assertIn("re-preview the exact publication tuple, affected ticket proposal, and exact edges plus canonical target", reconciliation)
        self.assertIn("explicit link authorization bound to the parent issue id, body hash, canonical target, and exact graph as applicable", reconciliation)
        self.assertIn("verify the returned id, approved title, canonical owner/repository, exact approved body bytes and their sha-256, that every approved required label is present, and that the current required-label tuple matches the approved tuple", reconciliation)
        body_drift = reconciliation.index("if the exact body bytes are not byte-identical or the sha-256 differs")
        review_pass = reconciliation.index("require that round to pass before re-previewing or requesting")
        repreview = reconciliation.index("only after the new review passes, re-preview")
        replacement_approvals = reconciliation.index("obtain fresh applicable final spec approvals")
        self.assertLess(body_drift, review_pass)
        self.assertLess(review_pass, repreview)
        self.assertLess(repreview, replacement_approvals)
        self.assertIn("no replacement approval or write authorization may exist before that pass", reconciliation)
        metadata_drift = reconciliation.index("if body bytes and sha-256 remain identical but only the parent issue id, title, canonical owner/repository, or required-label presence/tuple differs")
        metadata_preview = reconciliation.index("re-preview the exact affected publication tuple", metadata_drift)
        metadata_approvals = reconciliation.index("re-obtain every invalidated applicable approval and authorization", metadata_drift)
        publication_confirm = reconciliation.index("restore or reconfirm successful publication against that tuple", metadata_drift)
        self.assertLess(metadata_drift, metadata_preview)
        self.assertLess(metadata_preview, metadata_approvals)
        self.assertLess(metadata_approvals, publication_confirm)
        metadata_recovery = reconciliation[metadata_drift:]
        for replacement_gate in (
            "final specification approval", "publication authorization", "ticket-set approval",
            "separate issue-creation authorization", "affected ticket-payload or graph/link-delta approval",
            "any applicable independent write authorization", "explicit link-write authorization for affected graph changes",
        ):
            with self.subTest(replacement_gate=replacement_gate):
                self.assertIn(replacement_gate, metadata_recovery)
        self.assertIn("metadata-only drift does not require or imply a new /spec-review round solely because of that drift", reconciliation)
        self.assertIn("no ticket write may proceed until applicable approvals are fresh and successful publication is reconfirmed", reconciliation)
        self.assertIn("for each existing-ticket field or edge change, issue one field or edge write at a time", reconciliation)
        self.assertIn("record a unique operation id and cumulative attempt state for that individual write", reconciliation)
        self.assertIn("compare its exact current state with the approved baseline or last verified state and the exact expected pre-write state", reconciliation)
        self.assertIn("reconcile it before advancing", reconciliation)
        self.assertIn("for an ambiguous response, read back and reconcile before any retry", reconciliation)
        self.assertIn("retry only when a clearly transient failure is confirmed and read-back proves that exact operation is missing", reconciliation)
        self.assertIn("at most three attempts per write across resumes", reconciliation)
        self.assertIn("missing or conflicting operation history stops the workflow without retry", reconciliation)
        metadata_manual = manual[
            manual.index("if body bytes and hash remain identical but only"):
            manual.index("for title-only drift")
        ]
        for replacement_authorization in (
            "final spec approval", "publication authorization", "ticket-set approval",
            "separate issue-creation authorization", "affected payload/graph approvals",
            "independent link-write authorization",
        ):
            with self.subTest(replacement_authorization=replacement_authorization):
                self.assertIn(replacement_authorization, metadata_manual)
        self.assertIn(
            "bind renewed records to the updated parent tuple and exact payload/graph delta",
            metadata_manual,
        )
        publication_restore = metadata_manual.index("restore or reconfirm successful publication")
        labels_verified = metadata_manual.index("verify all required labels by read-back")
        ticket_writes_resume = metadata_manual.index("before resuming ticket writes")
        self.assertLess(publication_restore, labels_verified)
        self.assertLess(labels_verified, ticket_writes_resume)
        self.assertIn("verify all required labels by read-back before resuming ticket writes", metadata_manual)
        for template_fact in (
            "both final spec approvals", "ticket-set approval", "separate issue-creation authorization",
            "any independent link-write authorization", "exact edges plus canonical target",
            "explicit link authorization bound to the parent issue id, body hash, canonical target, and exact graph as applicable",
            "approved title", "exact approved body bytes", "every approved required label is present",
            "current required-label tuple matches the approved tuple",
            "one field or edge write at a time", "compare the immediate pre-read state",
            "at most three attempts per write across resumes", "missing or conflicting history stops without retry",
            "require that round to pass before re-previewing or requesting",
            "no replacement approval or write authorization may exist before that pass",
            "only after the new review passes, re-preview",
            "body bytes and sha-256 remain identical but only the parent issue id, title, canonical owner/repository, or required-label presence/tuple differs",
            "re-obtain every invalidated applicable approval and authorization",
            "final specification approval, publication authorization, ticket-set approval",
            "separate issue-creation authorization", "affected ticket-payload or graph/link-delta approval",
            "any applicable independent write authorization", "explicit link-write authorization for affected graph changes",
            "metadata-only drift does not require or imply a new /spec-review round solely because of that drift",
            "restore or reconfirm successful publication against that tuple",
        ):
            with self.subTest(template_fact=template_fact):
                self.assertIn(template_fact, workflow)

        for manual_fact in (
            "both final spec approvals", "affected ticket approvals",
            "independent link-write authorization is invalidated", "re-present the exact edges and canonical target",
            "fresh link authorization bound to the parent issue id/hash/target/graph before any link",
            "require the fresh review to pass before re-previewing or requesting, binding, or recording replacement approvals",
            "no replacement approval or write authorization exists while the fresh review is pending or failed",
            "for title-only drift, hold body bytes/hash, target, and labels constant",
            "attempt a ticket write and confirm it is refused before reapproval",
            "repeat separately for label-only drift with the title and body unchanged",
            "neither metadata-only case starts a fresh body review",
            "pending or failed review leaves all ticket writes blocked",
            "one write at a time", "exact approved baseline", "ambiguous response and reconcile it before retrying",
            "at most three attempts per write across resumes", "missing or conflicting operation history stops",
        ):
            with self.subTest(manual_fact=manual_fact):
                self.assertIn(manual_fact, manual)


class SpecImplementLoopBehaviorTests(unittest.TestCase):
    def test_target_language_rule_is_passed_to_documentation_skills(self):
        text = skill("spec-implement-loop").replace(chr(96), "")
        self.assertIn("Pass the target rule to /grill-duo-with-docs", text)
        self.assertNotIn("/grill-with-docs", text)

    def test_multi_root_reference_is_selected_only_after_read_only_deduplication(self):
        intake = section(skill("spec-implement-loop").lower(), "## intake and frontier")

        self.assertIn("after read-only intake and deduplication", intake)
        self.assertIn("if more than one distinct root remains", intake)
        self.assertIn(
            "follow the [multi-root coordination reference](references/multi-root-coordination.md)",
            intake,
        )
        self.assertIn("with one root, continue the single-root workflow below", intake)
        self.assertIn("this skill remains authoritative for procedures shared by both paths", intake)
        self.assertIn("prioritizing dependency order and then root order or issue number", intake)

    def test_multi_root_scope_is_mapped_and_validated_before_selection(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower()
        listing = section(reference, "## 1. list and validate roots")
        selection = section(reference, "## 2. select and freeze the batch")

        self.assertIn(
            "proposed root-to-ticket mapping with root entries in issue-number order",
            listing,
        )
        self.assertIn(
            "within each root, list explicitly referenced child tickets in issue-number order",
            listing,
        )
        self.assertIn("show blocker edges separately", listing)
        steps = [
            listing.index("detect child tickets listed under multiple roots"),
            listing.index("do not link an overlapping ticket until ownership or decomposition is resolved"),
            listing.index("mark each ticket described as a child task"),
            listing.index("ask once whether to link all missing cases in the validated roots"),
            listing.index("create only approved links"),
            listing.index("verify the resulting native links"),
            listing.index("return to the complete root-to-ticket listing"),
        ]
        self.assertEqual(steps, sorted(steps))
        self.assertIn("choose one owning root or decompose the ticket", listing)
        self.assertIn("pause only affected roots", listing)
        self.assertIn("unaffected roots may continue under their existing authorizations", listing)
        self.assertIn("if a link points to another root", listing)
        self.assertIn("ask for explicit approval for that exact relationship change", listing)
        self.assertIn("approval for missing links does not authorize moving or removing an existing link", listing)
        self.assertIn("if supported github tooling cannot apply and verify the exact change", listing)
        self.assertIn("do not substitute another operation", listing)
        self.assertIn("resume only after a read-only authoritative check confirms the chosen parent", listing)
        self.assertIn("if it cannot be verified, keep the affected roots paused", listing)
        self.assertIn("complete, validated listing", selection)
        self.assertIn("single-root flow", selection)

    def test_multi_root_batch_scope_stays_frozen_through_root_completion(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower().replace(chr(96), "")
        listing = section(reference, "## 1. list and validate roots")
        selection = section(reference, "## 2. select and freeze the batch")
        tracking = section(reference, "## 5. track acceptance, closure, and rework")
        completion = section(reference, "## 6. complete the batch")

        self.assertIn("if the documents or skill instructions conflict, explain the conflict to the user and pause only affected roots", reference)
        self.assertIn("the caller must not edit skill documents during the run", reference)
        self.assertIn("freeze the selected set for task-start authorization", selection)
        self.assertIn("a newly discovered root stays out of the batch until the user approves the scope change and renewed task-start authorization", selection)
        self.assertIn("pause the affected root with the evidence and resume condition", listing)
        self.assertIn("continue safe independent roots", listing)
        self.assertIn("in-scope acceptance rework returns to the current batch and the same parallel limit", tracking)
        self.assertIn("pause out-of-scope rework and scope expansion; present the proposed scope change to the user and resume only after renewed scope and task-start authorization are approved", tracking)
        self.assertIn("if a newly found root blocks only some selected roots, pause those roots and continue unaffected roots", tracking)
        self.assertIn("the batch stays open until every selected root has reached its completion checkpoint and root close", completion)

    def test_multi_root_task_start_authorization_scopes_cross_root_operations(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower()
        preparation = section(reference, "## 3. prepare and authorize the batch")
        adr_text = " ".join((
            ROOT / "docs" / "adr" / "0003-task-scoped-write-authorization.md"
        ).read_text(encoding="utf-8").lower().split())

        self.assertTrue(sentence_with_concepts(
            preparation, ("cross-root dependency",),
            ("source-root-to-dependent-root", "source root to dependent root"),
        ))
        operation = sentence_with_concepts(
            preparation, ("source root", "source-root"),
            ("dependent root", "dependent-root"), ("destination",),
            ("creates", "merges"),
        )
        self.assertTrue(operation)
        self.assertTrue(mentions_concepts(
            operation, ("branch",), ("worktree", "branch"),
            ("ticket branch", "integration branch"),
        ))
        self.assertTrue(sentence_with_concepts(
            preparation, ("ambiguous",), ("ask", "clarify"),
            ("pause",), ("dependent root",),
        ))

        worktree_prep = sentence_with_concepts(
            preparation, ("worktrees",), ("cross-root operations",),
        )
        authorization = sentence_with_concepts(
            preparation, ("single", "one"), ("task-start authorization",),
            ("frozen batch",),
        )
        authorized_operations = sentence_with_concepts(
            preparation, ("after approval",), ("only",), ("listed",),
            ("cross-root operations",),
        )
        dispatch = sentence_with_concepts(
            preparation, ("dispatch",), ("limit",), ("operations",),
            ("succeeded", "success"),
        )
        self.assertTrue(worktree_prep)
        self.assertTrue(authorization)
        self.assertTrue(authorized_operations)
        self.assertTrue(dispatch)
        self.assertLess(preparation.index(worktree_prep), preparation.index(authorization))
        self.assertLess(preparation.index(authorization), preparation.index(authorized_operations))
        self.assertLess(preparation.index(authorization), preparation.index(dispatch))
        self.assertTrue(sentence_with_concepts(
            preparation, ("per-root",), ("do not", "not request"),
            ("authorization", "grant"),
        ))

        batch_grant = sentence_with_concepts(
            adr_text, ("grant",), ("only",), ("listed resources", "listed"),
            ("categories", "actions"), ("batch",),
        )
        cross_root_scope = sentence_with_concepts(
            adr_text, ("cross-root",), ("source root",), ("dependent root",),
            ("destination",), ("operation", "branch"),
        )
        self.assertTrue(batch_grant)
        self.assertTrue(cross_root_scope)
        self.assertTrue(sentence_with_concepts(
            adr_text, ("authorization",), ("only",),
            ("listed cross-root operations",), ("batch",),
        ))
        self.assertTrue(sentence_with_concepts(
            adr_text, ("per-root",), ("replaces", "one"),
            ("authorization",), ("batch",),
        ))

    def test_task_start_authorization_covers_frozen_scope_before_dispatch(self):
        plan = section(skill("spec-implement-loop").lower(), "## plan the graph and reusable worktree pool")
        task_start = next(line for line in plan.splitlines() if line.strip().startswith("7."))

        self.assertTrue(mentions_concepts(
            task_start, ("freeze", "frozen"), ("batch",), ("authorization",),
            ("before",), ("dispatch",),
        ))
        self.assertTrue(mentions_concepts(
            task_start, ("root",), ("repository",), ("integration branch",),
            ("worktree",), ("ticket assignment",), ("action categories",),
            ("issue targets",), ("cross-root operation",),
        ))
        gate = sentence_with_concepts(
            task_start, ("grant",), ("required scope",), ("dispatch",),
        )
        self.assertTrue(gate)
        self.assertRegex(gate, r"\b(?:until|only after|after)\b")
        self.assertTrue(sentence_with_concepts(
            task_start, ("pending",), ("declined",), ("incomplete",),
            ("dispatch",), ("implementation conversation",),
        ))
        self.assertTrue(sentence_with_concepts(
            task_start, ("worker",), ("only",), ("grant", "authorization"),
            ("ticket",), ("resources",), ("actions", "categories"),
        ))
        self.assertTrue(sentence_with_concepts(
            task_start, ("worker",), ("another ticket", "sibling ticket"),
            ("authorization", "grant"), ("must not", "cannot"),
        ))
        self.assertTrue(sentence_with_concepts(
            task_start, ("unlisted",), ("gated", "blocked"),
            ("actions", "resources"),
        ))

    def test_multi_root_scheduler_shares_limit_and_releases_safe_slots(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower().replace(chr(96), "")
        preparation = section(reference, "## 3. prepare and authorize the batch")
        scheduling = section(reference, "## 4. schedule queues and gate prerequisites")
        acceptance = section(reference, "## 5. track acceptance, closure, and rework")

        self.assertIn("before the first implementation conversation, ask once for a single batch-wide parallel limit", preparation)
        self.assertIn("apply that cap across roots to every dispatch and refill throughout the batch", preparation)
        self.assertIn("unlimited still cannot exceed the clean, available worker slots", preparation)
        self.assertTrue(sentence_with_concepts(
            scheduling, ("worker",), ("only",), ("grant", "authorization"),
            ("ticket",),
        ))
        self.assertTrue(sentence_with_concepts(
            scheduling, ("worker",), ("another ticket", "sibling ticket"),
            ("authorization", "grant"), ("must not", "cannot"),
        ))
        self.assertLess(
            preparation.index("before the first implementation conversation"),
            preparation.index("dispatch planned work only after this limit is set"),
        )
        self.assertIn("count active implementation conversations across all selected roots against the same limit", scheduling)
        self.assertIn("refill capacity as work completes without exceeding the shared limit or available slots", scheduling)
        self.assertIn("check for newly eligible work on the agreed 15-minute cadence", scheduling)
        self.assertIn("stop checking once every selected root has an implementation conversation", scheduling)
        self.assertIn("do not interrupt an active worker when newly eligible work changes queue order", scheduling)
        self.assertIn("reuse an idle slot only when it is safe and its workspace is clean", scheduling)
        self.assertIn("release its worker slot at root_checkpoint", acceptance)
        self.assertIn("lightweight wait for final user acceptance or closure does not consume an implementation slot", acceptance)

    def test_manual_authorization_acceptance_covers_worker_scope_and_dispatch_gates(self):
        manual = (ROOT / "tests" / "manual" / "spec-implement-loop.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## graph planning and reusable worktree pool")

        self.assertTrue(sentence_with_concepts(
            scenario, ("ticket a",), ("ticket b",), ("worker",), ("only",),
            ("grant", "authorization"), ("resources",), ("actions",),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("another ticket", "sibling ticket"), ("resources",),
            ("actions",), ("blocked",),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("pending",), ("declined",), ("incomplete",),
            ("no worker", "no implementation conversation"), ("starts", "dispatch"),
        ))

    def test_cross_root_prerequisites_are_resolved_and_integrated_before_dispatch(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower().replace(chr(96), "")
        preparation = section(reference, "## 3. prepare and authorize the batch")
        scheduling = section(reference, "## 4. schedule queues and gate prerequisites")

        self.assertIn("if the required base or source branch is ambiguous, ask which existing branch to use or which source branch to merge", preparation)
        self.assertIn("pause only the affected dependent root until resolved", preparation)
        self.assertIn("do not infer a branch or merge operation", preparation)
        self.assertIn("the plan and task-start authorization must explicitly name the source root branch and its merge into the dependent integration branch", preparation)
        self.assertIn("creating a dependent ticket branch from the source does not substitute for or authorize that merge", preparation)
        self.assertIn("merge that branch into the dependent root as authorized; dispatch the dependent ticket only after the merge succeeds", scheduling)
        self.assertIn("do not wait for the source root's full queue or final acceptance", scheduling)
        self.assertIn("a blocked prerequisite or merge conflict pauses only the affected dependent root", scheduling)
        self.assertIn("continue other roots with ready tickets", scheduling)
        self.assertLess(
            preparation.index("if the required base or source branch is ambiguous"),
            preparation.index("request the single task-start authorization defined by the main skill"),
        )

    def test_remediation_routes_only_when_final_review_finds_issues(self):
        text = skill("spec-implement-loop").lower()
        final_review = section(text, "## final review")
        remediation = skill_reference("spec-implement-loop", "final-review-remediation.md").lower().replace(chr(96), "")
        self.assertIn("when no non-deferred ready ticket remains, review the complete target diff", final_review)
        self.assertIn("if the reports contain no findings", final_review)
        self.assertIn("if findings exist", final_review)
        self.assertIn("references/final-review-remediation.md", final_review)
        self.assertNotIn("## final review and remediation", text)
        self.assertIn("preserve its seam-confirmation gate before publication", remediation)
        self.assertIn("preserve its granularity, blocking-edge, and publication approval gates", remediation)
        self.assertIn("**deferred:** yes", remediation)
        self.assertIn("show the complete p0/p1 batch and ask the user for approval", remediation)
        self.assertIn("allow at most three rounds", remediation)

    def test_status_sync_authorization_is_repository_and_checkpoint_scoped(self):
        text = skill("spec-implement-loop").lower().replace(chr(96), "")
        authorization = section(text, "## plan the graph and reusable worktree pool")
        lifecycle = section(text, "## root-run lifecycle")
        issue_loop = section(text, "## issue loop")
        status_retry_rule = next(
            line for line in text.splitlines() if line.startswith("ticket and root status-sync writes")
        )

        for detail in (
            "reconcile an uncertain outcome before retrying",
            "retry only transient failures up to three total attempts",
            "do not retry permanent failures",
            "preserve confirmed independent status updates if a later status sync fails",
        ):
            self.assertIn(detail, status_retry_rule)

        self.assertFalse("issue #143" in text, "Issue #143 cannot provide reusable status authorization.")
        self.assertTrue(sentence_with_concepts(
            authorization, ("root",), ("repository", "repo"), ("ticket",), ("status",),
            ("limited", "only", "scoped"),
        ))
        self.assertTrue(sentence_with_concepts(
            authorization, ("status",), ("only", "limited"), ("ticket",), ("root",), ("checkpoint",),
        ))
        denied = sentence_with_concepts(
            authorization, ("status-sync authorization", "status synchronization"),
            ("not", "cannot", "prohibited", "outside"),
            ("issue",), ("comment",), ("label",), ("sub-issue", "sub issue"),
            ("pull request", "pull-request"), ("merge",), ("github",), ("write",),
            ("authorize", "permit"),
        )
        self.assertTrue(denied, "The status-sync scope must distinguish status changes from other writes.")
        self.assertRegex(
            denied,
            r"\b(?:does not|doesn't|cannot|can't|must not|never)\s+(?:authorize|permit|allow|cover)\b",
        )
        self.assertFalse(status_sync_grant_clause(
            authorization, NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization is status-only, but a separate user approval authorizes a comment.".lower(),
            ("comment",),
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes, and the user separately authorizes issue creation.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes, and a separate approval from the user "
            "authorizes a comment.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes, and a separate approval by the user "
            "authorizes a comment.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes, and issue creation is separately "
            "authorized by the user.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync permits status changes and allows comments only with separate user approval.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync allows issue creation only after separate user approval.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync may allow issue creation, but only after a separate approval.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync may allow issue creation, but only if separate approval is granted.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync may allow issue creation, but only when a separate approval is in place.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes on the supplied root issue.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertTrue(status_sync_grant_clause(
            "Status sync can create an issue.".lower(), NON_STATUS_WRITES,
        ))
        self.assertTrue(status_sync_grant_clause(
            "Status sync may label an issue.".lower(), NON_STATUS_WRITES,
        ))
        self.assertTrue(status_sync_grant_clause(
            "Status-sync authorization only permits status changes. Status-sync authorization also permits issue creation.".lower(),
            ("issue creation",),
        ))

        ticket_checkpoint = lifecycle.index("| ticket_checkpoint")
        ticket_sync = lifecycle.index("| status_sync")
        root_sync = lifecycle.index("| root_status_sync")
        root_checkpoint = lifecycle.index("| root_checkpoint")
        self.assertLess(ticket_checkpoint, ticket_sync)
        self.assertLess(ticket_sync, root_sync)
        self.assertLess(root_sync, root_checkpoint)
        ticket_checkpoint_rule = next(
            line for line in lifecycle.splitlines() if "| ticket_checkpoint |" in line
        )
        self.assertTrue(mentions_concepts(
            ticket_checkpoint_rule, ("review",), ("internally",), ("does not wait for human approval",), ("status_sync",),
        ))
        root_status_rule = next(line for line in lifecycle.splitlines() if "| root_status_sync |" in line)
        self.assertTrue(mentions_concepts(
            root_status_rule, ("final verification",), ("review",), ("completed",),
            ("without a separate approval", "approval pause"),
        ))
        root_checkpoint_rule = next(line for line in lifecycle.splitlines() if "| root_checkpoint |" in line)
        self.assertTrue(mentions_concepts(
            root_checkpoint_rule, ("explicit approval", "approval"), ("complete",),
        ))
        self.assertTrue(sentence_with_concepts(
            lifecycle, ("status synchronization", "status_sync"), ("never", "does not"),
            ("approval",), ("root",), ("complete",),
        ))

        ticket_sync_rule = next(line for line in issue_loop.splitlines() if line.lstrip().startswith("6."))
        self.assertTrue(mentions_concepts(
            ticket_sync_rule, ("internal ticket review", "review checkpoint"),
            ("confirmed authorized push", "confirmed push"), ("ticket's status", "ticket status"),
            ("task-start grant", "batch grant"), ("does not wait for human approval",),
        ))
        self.assertIn("apply the shared bounded retry rules to status sync", ticket_sync_rule)
        root_sync_rule = next(line for line in issue_loop.splitlines() if line.lstrip().startswith("7."))
        self.assertTrue(mentions_concepts(
            root_sync_rule, ("final verification",), ("root status",), ("before",),
            ("root completion checkpoint", "completion checkpoint"),
        ))

        interruption = sentence_with_concepts(
            lifecycle, ("restart", "interruption", "resume"), ("reconcile", "re-read"),
            ("root",), ("ticket",), ("repository",), ("status",), ("write",),
        )
        self.assertTrue(interruption)

    def test_manual_status_scenario_covers_repository_and_operation_boundaries(self):
        manual = (ROOT / "tests" / "manual" / "spec-implement-loop.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## task-scoped commits and pushes")
        status_scenario = sentence_with_concepts(
            scenario, ("repository a", "repo a"), ("repository b", "repo b"),
            ("root",), ("ticket",), ("status",), ("checkpoint",),
            ("unchanged", "unmodified"),
        )
        self.assertTrue(status_scenario)
        self.assertTrue(sentence_with_concepts(
            scenario, ("repository a", "repo a"), ("in-repository ticket",),
            ("cross-repository ticket",), ("repository b", "repo b"),
        ))
        self.assertFalse("issue #143" in status_scenario, "Manual scenario must not rely on Issue #143.")

        denial = sentence_with_concepts(
            scenario, ("status-sync authorization", "status sync authorization"),
            ("not", "cannot", "outside", "prohibited"),
            ("issue",), ("comment",), ("label",), ("sub-issue", "sub issue"),
            ("pr", "pull request"), ("merge",), ("github",), ("write",),
        )
        self.assertTrue(denial)
        self.assertRegex(
            denial,
            r"\b(?:does not|doesn't|cannot|can't|must not|never)\s+(?:authorize|permit|allow|cover)\b",
        )
        self.assertFalse(status_sync_grant_clause(
            scenario, NON_STATUS_WRITES + ("pr action",),
        ))


class ConventionalGitMessagesBehaviorTests(unittest.TestCase):
    def test_each_output_type_routes_to_an_existing_reference(self):
        text = skill("conventional-git-messages").lower()
        routes = section(text, "## guidance routes")
        self.assertIn("follow its links only for rules", routes)
        self.assertIn("it reuses.", routes)
        references = (
            ("commit message", "commit-messages.md", ("## commit subject", "## commit body")),
            (
                "pull request title, description, or comment",
                "pull-request-text.md",
                (
                    "## pull request titles",
                    "## pull request descriptions",
                    "## pull request comments",
                    "## optional diagrams",
                ),
            ),
            (
                "issue title, description, or comment",
                "issue-text.md",
                ("## issue titles", "## issue descriptions", "## issue comments"),
            ),
        )
        for trigger, filename, headings in references:
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, routes)
                self.assertIn(f"(references/{filename})", routes)
                reference_path = (
                    ROOT / "skills" / "conventional-git-messages" / "references" / filename
                )
                self.assertTrue(reference_path.is_file())
                reference_text = reference_path.read_text(encoding="utf-8").lower()
                for heading in headings:
                    self.assertIn(heading, reference_text)

    def test_shared_operation_boundary_stays_in_the_entrypoint(self):
        text = skill("conventional-git-messages").lower().replace(chr(96), "")
        activation = section(text, "## activation criteria & objective")
        self.assertIn("never perform a git operation", activation)
        self.assertIn("create or modify an issue", activation)
        self.assertIn("open or edit a pull request", activation)
        self.assertIn("post a comment", activation)

    def test_optional_diagrams_use_user_selected_skill_scout_flow(self):
        text = skill_reference("conventional-git-messages", "pull-request-text.md").lower().replace(chr(96), "")
        diagrams = section(text, "## optional diagrams")
        self.assertIn("follow /skill-scout's general-host flow", diagrams)
        self.assertIn("use its skillroute local-catalog mode only when the user selects it", diagrams)
        self.assertIn("do not install, index, copy, or silently substitute a skill", diagrams)


class ReadmeBehaviorTests(unittest.TestCase):
    def test_generic_skill_install_command_remains(self):
        self.assertIn("npx skills@latest add EltonZhang777/AggregateSkills", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_spec_review_is_in_the_skill_catalog(self):
        self.assertIn("- [spec-review](skills/spec-review/SKILL.md)", (ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
