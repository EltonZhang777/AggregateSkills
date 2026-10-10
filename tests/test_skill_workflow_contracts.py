"""Focused behavior contracts retained from the retired prerequisite checks."""

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
    def test_github_scope_and_subskill_steps_remain_explicit(self):
        text = skill("pr-and-merge").lower().replace(chr(96), "")
        activation = section(text, "## activation criteria & objective")
        reuse = section(text, "## reuse or prepare the pr")
        merge_route = section(text, "## merge after approval")
        merge = skill_reference("pr-and-merge", "merge-after-approval.md").lower().replace(chr(96), "")
        self.assertIn("it handles github only", activation)
        self.assertIn("before drafting new pr title or body text", reuse)
        self.assertIn("pass the durable-project-text language rule", reuse)
        self.assertIn("to /conventional-git-messages", reuse)
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
    def test_complete_group_approval_starts_documentation_phase(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        grouping = section(text, "## 2. turn the request into groups")
        protocol = section(text, "## 4. child-session protocol")
        git = section(text, "## 5. task branches and git publication")
        documents = section(text, "## 6. shared workspace and document writes")
        self.assertIn("wait for explicit approval of that complete grouping", grouping)
        self.assertIn("approval starts every approved group in the /grill-duo-with-docs", grouping)
        self.assertNotIn("explicit opt-in", grouping)
        self.assertIn("for every approved group, invoke /grill-duo-with-docs", protocol)
        self.assertIn("if the frontier is empty, use its shared-understanding summary and wait for confirmation", protocol)
        self.assertIn("for every approved group, run /grill-duo-with-docs first", protocol)
        self.assertIn("approval of the complete grouping grants the main agent standing authorization for routine, focused local commits", git)
        self.assertIn("group approval does not authorize pushes, issue creation, status changes, sub-issue links, or other github writes", git)
        self.assertIn("obtain explicit approval before a push or any other github write", git)
        self.assertIn("record only user-confirmed content in project documents", documents)


class SpecImplementLoopBehaviorTests(unittest.TestCase):
    def test_target_language_rule_is_passed_to_documentation_skills(self):
        text = skill("spec-implement-loop").replace(chr(96), "")
        self.assertIn("Pass the target rule to /grill-duo-with-docs", text)
        self.assertNotIn("/grill-with-docs", text)

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


if __name__ == "__main__":
    unittest.main()
