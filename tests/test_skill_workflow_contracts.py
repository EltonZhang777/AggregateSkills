"""Focused behavior contracts retained from the retired prerequisite checks."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def skill(name):
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


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
        local = section(text, "## skillroute local-catalog mode")
        explicit = section(text, "### resolve an explicitly named skill")
        report = section(text, "## report")
        self.assertIn("start with an installed-skill inventory exposed by the host or supplied by the caller", general)
        self.assertIn("treat an inventory as complete only when its source identifies it as covering all installed skills", general)
        self.assertIn("a partial inventory never proves a skill is absent", general)
        self.assertIn("return unavailable", general)
        self.assertIn("optional local-catalog mode", local)
        self.assertIn("if the cli, local backend, or catalog is unavailable, return unavailable", local)
        self.assertIn("do not present the result as evidence that a skill is absent", local)
        self.assertIn("temporary resolver or backend errors", local)
        self.assertIn("return an unresolved prerequisite result", local)
        self.assertIn("exact failed check and recovery condition", local)
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
        merge = section(text, "## merge after approval")
        self.assertIn("it handles github only", activation)
        self.assertIn("immediately before drafting or materially updating a pr title or body, read and follow /conventional-git-messages", reuse)
        self.assertIn("when an approved merge encounters a conflict, use /resolving-merge-conflicts", merge)


class PruneWorktreesBehaviorTests(unittest.TestCase):
    def test_unavailable_evidence_never_produces_safe_to_clean(self):
        text = skill("prune-worktrees-and-branches").lower().replace("*", "")
        self.assertIn("if a required github check is unavailable, do not mark the affected branch safe to clean", text)
        self.assertIn("unknown, failed, incomplete, or out-of-date evidence must never produce safe to clean", text)


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


class ConventionalGitMessagesBehaviorTests(unittest.TestCase):
    def test_optional_diagrams_use_user_selected_skill_scout_flow(self):
        text = skill("conventional-git-messages").lower().replace(chr(96), "")
        diagrams = section(text, "## optional diagrams")
        self.assertIn("follow /skill-scout's general-host flow", diagrams)
        self.assertIn("use its skillroute local-catalog mode only when the user selects it", diagrams)


class ReadmeBehaviorTests(unittest.TestCase):
    def test_generic_skill_install_command_remains(self):
        self.assertIn("npx skills@latest add EltonZhang777/AggregateSkills", (ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
