import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_TICK = chr(96)
START = "<!-- prerequisite-list:start -->"
END = "<!-- prerequisite-list:end -->"


def dependency_members(entry):
    return entry.get("one_of", []) if "one_of" in entry else [entry]


def prerequisite_identity(item):
    return item["name"], item["source"]


def dependency_condition(entry):
    when = entry.get("when", "Always")
    conditional_members = [
        member for member in dependency_members(entry) if "one_of" in entry and "when" in member
    ]
    if conditional_members:
        conditions = "; ".join(
            f"{MARKDOWN_TICK}/{member['name']}{MARKDOWN_TICK}: {member['when']}"
            for member in conditional_members
        )
        when += f"; option conditions: {conditions}"
    return when


def validate_dependency(category, item, path, allow_group=True):
    if not isinstance(item, dict):
        raise ValueError(f"Prerequisites must be objects in {path}")

    if "one_of" in item:
        if not allow_group or set(item) - {"one_of", "when"}:
            raise ValueError(f"Invalid one_of prerequisite in {path}")
        alternatives = item["one_of"]
        if not isinstance(alternatives, list) or len(alternatives) < 2:
            raise ValueError(f"one_of must contain at least two alternatives in {path}")
        if "when" in item and (not isinstance(item["when"], str) or not item["when"].strip()):
            raise ValueError(f"Invalid one_of condition in {path}")
        identities = set()
        for alternative in alternatives:
            validate_dependency(category, alternative, path, allow_group=False)
            identity = prerequisite_identity(alternative)
            if identity in identities:
                raise ValueError(f"Duplicate one_of alternative in {path}")
            identities.add(identity)
        return

    required = {"name", "source"}
    optional = {"when"}
    if category == "tools":
        required.update({"install", "setup"})
    elif category == "mcps":
        required.add("install")
    else:
        optional.add("install")
    if not required.issubset(item) or set(item) - required - optional:
        raise ValueError(f"Invalid {category} prerequisite fields in {path}")
    if not isinstance(item["name"], str) or not item["name"].strip():
        raise ValueError(f"Invalid {category} prerequisite name in {path}")
    source = item["source"]
    if source is not None:
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"Invalid {category} prerequisite source in {path}")
        if category == "skills":
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source):
                raise ValueError(f"Invalid {category} prerequisite source format in {path}")
        else:
            try:
                parsed_source = urlsplit(source)
                parsed_source.port
            except ValueError:
                parsed_source = None
            if (
                parsed_source is None
                or parsed_source.scheme not in {"http", "https"}
                or not parsed_source.hostname
                or re.search(r"\s", source)
            ):
                raise ValueError(f"Invalid {category} prerequisite source format in {path}")
    if source is None and (category != "skills" or not item.get("install")):
        raise ValueError(f"Missing source status for {category} prerequisite in {path}")
    if "when" in item and (not isinstance(item["when"], str) or not item["when"].strip()):
        raise ValueError(f"Invalid {category} prerequisite condition in {path}")
    for field in ("install", "setup"):
        if field in item and (not isinstance(item[field], str) or not item[field].strip()):
            raise ValueError(f"Invalid {field} instructions for {category} prerequisite in {path}")


def validate_prerequisite_entries(category, entries, skill_name, path):
    seen = set()
    for entry in entries:
        validate_dependency(category, entry, path)
        for member in dependency_members(entry):
            identity = prerequisite_identity(member)
            if identity in seen:
                raise ValueError(f"Duplicate {category} prerequisite {identity} in {skill_name}")
            seen.add(identity)


def read_prerequisites(path):
    text = path.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not frontmatter:
        raise ValueError(f"Missing skill frontmatter: {path}")

    name = re.search(r"^name: ([a-z0-9-]+)$", frontmatter[1], re.M)
    declaration = re.search(r"^  prerequisites: '(.+)'$", frontmatter[1], re.M)
    if not name or not declaration:
        raise ValueError(f"Missing name or machine-readable prerequisites: {path}")

    prerequisites = json.loads(declaration[1])
    if not isinstance(prerequisites, dict) or set(prerequisites) != {"skills", "mcps", "tools"}:
        raise ValueError(f"Unexpected prerequisite categories: {path}")
    if name[1] != path.parent.name:
        raise ValueError(f"Skill name does not match directory: {path}")
    for category, entries in prerequisites.items():
        if not isinstance(entries, list):
            raise ValueError(f"Prerequisite category must be a list: {path}")
        validate_prerequisite_entries(category, entries, name[1], path)
    return name[1], prerequisites


def source_cell(category, item):
    source = item["source"]
    if source is None:
        return "Publisher source not declared"
    url = source if "://" in source else f"https://github.com/{source}"
    label = source if category == "skills" else f"{item['name']} project"
    return f"[{label}]({url})"


def install_cell(category, item):
    if "install" in item:
        install = item["install"]
    else:
        install = f"npx skills@latest add {item['source']} --skill={item['name']}"
    if category == "tools":
        install += "; " + item["setup"]
    return install


def dependency_rows(category):
    dependencies = {}
    dependencies_by_identity = {}
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        skill_name, prerequisites = read_prerequisites(path)
        for entry in prerequisites[category]:
            when = dependency_condition(entry)
            members = dependency_members(entry)
            for member in members:
                details = (member["source"], install_cell(category, member), member.get("setup", ""))
                identity = prerequisite_identity(member)
                previous = dependencies_by_identity.setdefault(identity, details)
                if previous != details:
                    raise ValueError(f"Conflicting install details for {category} prerequisite {identity}")
            if "one_of" in entry:
                names = [f"{MARKDOWN_TICK}/{item['name']}{MARKDOWN_TICK}" for item in members]
                name = "One of: " + " or ".join(names)
                sources = [
                    f"{MARKDOWN_TICK}/{item['name']}{MARKDOWN_TICK}: {source_cell(category, item)}"
                    for item in members
                ]
                installs = [
                    f"{MARKDOWN_TICK}/{item['name']}{MARKDOWN_TICK}: {install_cell(category, item)}"
                    for item in members
                ]
                source = "; ".join(sources)
                install = "; ".join(installs)
            else:
                name = f"{MARKDOWN_TICK}/{entry['name']}{MARKDOWN_TICK}" if category == "skills" else entry["name"]
                source = source_cell(category, entry)
                install = install_cell(category, entry)
            key = (name, source, install, when)
            dependencies.setdefault(key, set()).add(skill_name)

    return [
        (*key, ", ".join(f"{MARKDOWN_TICK}/{skill_name}{MARKDOWN_TICK}" for skill_name in sorted(required_by)))
        for key, required_by in sorted(dependencies.items())
    ]


def render_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def render_prerequisite_list():
    skill_rows = dependency_rows("skills")
    mcp_rows = dependency_rows("mcps")
    tool_rows = dependency_rows("tools")
    skill_headers = ("Skill", "Source", "Install", "When", "Required by")
    mcp_headers = ("MCP", "Source", "Install", "When", "Required by")
    tool_headers = ("Tool", "Source", "Install / setup", "When", "Required by")
    return "\n\n".join(
        (
            "### Agent Skills\n\n" + (render_table(skill_headers, skill_rows) if skill_rows else "None currently."),
            "### MCPs\n\n" + (render_table(mcp_headers, mcp_rows) if mcp_rows else "None currently."),
            "### Other runtime tools\n\n" + (render_table(tool_headers, tool_rows) if tool_rows else "None currently."),
        )
    )

class PrerequisiteGuideTests(unittest.TestCase):
    maxDiff = None

    def test_one_of_guide_conditions_include_conditional_alternatives(self):
        entry = {
            "when": "When using an interactive editor.",
            "one_of": [
                {
                    "name": "show-me",
                    "source": None,
                    "install": "Publisher source is not declared.",
                    "when": "When a visual walkthrough is useful.",
                },
                {"name": "archify", "source": "author/archify"},
            ],
        }
        self.assertEqual(
            dependency_condition(entry),
            "When using an interactive editor.; option conditions: "
            + MARKDOWN_TICK + "/show-me" + MARKDOWN_TICK
            + ": When a visual walkthrough is useful.",
        )

    def test_duplicate_prerequisite_identity_includes_source(self):
        path = ROOT / "skills" / "identity-test" / "SKILL.md"
        alternatives = [
            {"name": "shared-skill", "source": "first/publisher"},
            {"name": "shared-skill", "source": "second/publisher"},
        ]
        validate_prerequisite_entries("skills", alternatives, "identity-test", path)
        with self.assertRaises(ValueError):
            validate_prerequisite_entries(
                "skills", [alternatives[0], dict(alternatives[0])], "identity-test", path
            )

    def test_guide_keeps_same_name_from_different_sources(self):
        with tempfile.TemporaryDirectory(prefix="prerequisite-guide-", dir=ROOT) as directory:
            temporary_root = Path(directory)
            for skill_name, source in (
                ("requires-first", "first/publisher"),
                ("requires-second", "second/publisher"),
            ):
                skill_path = temporary_root / "skills" / skill_name / "SKILL.md"
                skill_path.parent.mkdir(parents=True)
                prerequisites = {
                    "skills": [{"name": "shared-skill", "source": source}],
                    "mcps": [],
                    "tools": [],
                }
                skill_path.write_text(
                    f"---\nname: {skill_name}\nmetadata:\n  prerequisites: '{json.dumps(prerequisites)}'\n---\n",
                    encoding="utf-8",
                )
            with patch(__name__ + ".ROOT", temporary_root):
                rows = dependency_rows("skills")

        self.assertEqual(
            [row[1] for row in rows],
            [
                "[first/publisher](https://github.com/first/publisher)",
                "[second/publisher](https://github.com/second/publisher)",
            ],
        )

    def test_source_format_matches_prerequisite_category(self):
        path = ROOT / "skills" / "source-test" / "SKILL.md"
        with self.assertRaises(ValueError):
            validate_dependency("skills", {"name": "upstream", "source": "publisher"}, path)
        with self.assertRaises(ValueError):
            validate_dependency(
                "mcps", {"name": "MCP", "source": "publisher/project", "install": "Install it"}, path
            )
        with self.assertRaises(ValueError):
            validate_dependency(
                "tools", {"name": "Tool", "source": "javascript:alert(1)", "install": "Install it", "setup": "Set it up"}, path
            )

    def test_guide_explains_conditional_and_one_of_prerequisites(self):
        guide = (ROOT / "docs/prerequisites.md").read_text(encoding="utf-8")
        self.assertIn("| When |", guide)
        alternatives = "One of: " + MARKDOWN_TICK + "/show-me" + MARKDOWN_TICK + " or " + MARKDOWN_TICK + "/archify" + MARKDOWN_TICK
        self.assertIn(alternatives, guide)
        self.assertIn("When using GitHub issue tracking.", guide)
        self.assertIn("Publisher source not declared", guide)
        self.assertIn("Always | " + MARKDOWN_TICK + "/pr-and-merge" + MARKDOWN_TICK, guide)

    def test_installed_skills_do_not_reference_the_prerequisite_guide(self):
        references = [
            str(path.relative_to(ROOT))
            for path in sorted((ROOT / "skills").glob("*/SKILL.md"))
            if "docs/prerequisites.md" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(references, [])

    def test_skills_with_prerequisites_have_standard_sections(self):
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            name, prerequisites = read_prerequisites(path)
            if not any(prerequisites.values()):
                continue
            text = path.read_text(encoding="utf-8")
            headings = [line for line in text.splitlines() if line.startswith("## ")]
            with self.subTest(skill=name):
                activation = "## Activation Criteria & Objective"
                dependencies = "## Dependencies"
                self.assertIn(activation, headings)
                self.assertIn(dependencies, headings)
                self.assertLess(headings.index(activation), headings.index(dependencies))
                activation_start = text.index(activation) + len(activation)
                activation_end = text.find("\n## ", activation_start)
                activation_text = text[activation_start:] if activation_end == -1 else text[activation_start:activation_end]
                self.assertTrue(activation_text.strip())
                start = text.index(dependencies) + len(dependencies)
                end = text.find("\n## ", start)
                dependency_text = text[start:] if end == -1 else text[start:end]
                self.assertTrue(dependency_text.strip())
                if prerequisites["skills"]:
                    for phrase in (
                        "exact identity",
                        "source",
                        "original",
                        "invocation metadata",
                        "skillroute",
                        "available skill list",
                        "same-name candidate",
                        "missing, ambiguous, or mismatched source",
                        "inaccessible",
                        "unresolved",
                        "block only work that requires the affected source",
                        "continue only independent work",
                        "do not retry in a loop",
                        "retry only when the resolver, catalog, or source becomes available or new evidence changes the result",
                        "report the exact dependency, blocked step, and recovery condition",
                        "this pause does not classify the source as missing",
                        "stop the workflow only when",
                        "confirmed absent, invalid, or permission-denied",
                        "do not guess",
                        "stop",
                        "report",
                    ):
                        self.assertIn(phrase, dependency_text.lower())
                if any(item["name"] == "GitHub CLI (gh)" for item in prerequisites["tools"]):
                    with self.subTest(skill=name, tool="GitHub CLI (gh) approval"):
                        self.assertIn(
                            "ask the user for explicit approval before installing it or authenticating with `gh auth login`",
                            dependency_text.lower(),
                        )
                        self.assertIn("if approval is not given, do not install or authenticate", dependency_text.lower())
                        self.assertIn("pause only work that needs it", dependency_text.lower())
            if any("one_of" in entry for entry in prerequisites["skills"]):
                with self.subTest(skill=name, prerequisite="one_of"):
                    self.assertIn("`one_of` declaration", dependency_text.lower())
                    self.assertIn("exactly one selected alternative", dependency_text.lower())
                    self.assertIn("unselected alternatives are not required", dependency_text.lower())
                    self.assertIn("only on this installation", dependency_text.lower())

    def test_dependency_resolution_rules_keep_their_shared_meaning(self):
        shared_clauses = (
            "If SkillRoute CLI, its catalog, or a required lookup/read operation is unavailable, fails, or returns an unusable result, record the affected dependency as unresolved and report it; do not guess, substitute, or invoke it.",
            "Block only work that requires the affected source and continue only independent work.",
            "Do not retry in a loop; retry only when the resolver, catalog, or source becomes available or new evidence changes the result.",
            "If no independent work remains, pause and report the exact dependency, blocked step, and recovery condition; this pause does not classify the source as missing.",
        )
        terminal_reports = (
            "report its exact identity and source",
            "report its exact dependency identity and source status",
            "report the exact identity and source",
            "report the exact dependency identity and source",
        )
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            name, prerequisites = read_prerequisites(path)
            if not prerequisites["skills"]:
                continue
            text = path.read_text(encoding="utf-8").lower()
            dependency_start = text.index("## dependencies")
            dependency_end = text.find("\n## ", dependency_start + len("## dependencies"))
            dependency_text = text[dependency_start:] if dependency_end == -1 else text[dependency_start:dependency_end]
            with self.subTest(skill=name):
                for clause in shared_clauses:
                    self.assertIn(clause.lower(), dependency_text)
                stop_at = dependency_text.find("stop the workflow only when")
                confirmed_at = dependency_text.find("confirmed absent, invalid, or permission-denied", stop_at)
                self.assertGreaterEqual(stop_at, 0)
                self.assertGreater(confirmed_at, stop_at)
                self.assertTrue(
                    any(dependency_text.find(clause, confirmed_at) > confirmed_at for clause in terminal_reports)
                )

    def test_skill_scout_distinguishes_unresolved_from_missing_prerequisites(self):
        path = ROOT / "skills" / "skill-scout" / "SKILL.md"
        text = path.read_text(encoding="utf-8").lower()
        dependencies = text.split("## dependencies", 1)[1].split("\n## ", 1)[0]
        resolver = text.split("### 1. check the resolver", 1)[1].split("\n### ", 1)[0]
        report = text.split("### 4. report the result", 1)[1].split("\n## ", 1)[0]
        self.assertIn(
            "if a check fails without confirming one of those conditions, or its result is inconclusive, stop with an `unresolved prerequisite` result",
            dependencies,
        )
        self.assertIn("stop with an `unresolved prerequisite` result", dependencies)
        self.assertIn(
            "if the cli or catalog is confirmed absent, invalid, or permission-denied, report `missing prerequisite`",
            dependencies,
        )
        self.assertIn("do not install the cli or index roots automatically", dependencies)
        self.assertIn("for temporary resolver or backend errors", resolver)
        self.assertIn("other inconclusive results", resolver)
        self.assertIn("`unresolved prerequisite`", resolver)
        self.assertIn("exact failed check and recovery condition", resolver)
        self.assertIn("`unresolved prerequisite`", report)

    def test_prune_marks_unavailable_checks_unknown_and_never_safe_to_clean(self):
        path = ROOT / "skills" / "prune-worktrees-and-branches" / "SKILL.md"
        text = path.read_text(encoding="utf-8").lower()
        dependencies = text.split("## dependencies", 1)[1].split("\n## ", 1)[0]
        self.assertIn(
            "if the cli or any required check is unavailable, mark the affected state unknown",
            dependencies,
        )
        self.assertIn("do not classify the branch as safe to clean", dependencies)

    def test_source_null_skill_options_report_local_and_portable_status(self):
        path = ROOT / "skills" / "spec-implement-loop" / "SKILL.md"
        _, prerequisites = read_prerequisites(path)
        alternatives = next(entry["one_of"] for entry in prerequisites["skills"] if "one_of" in entry)
        self.assertTrue(all(item["source"] is None for item in alternatives))
        text = path.read_text(encoding="utf-8").lower()
        self.assertIn("skillroute to confirm the exact declared name, local skill path, and content hash", text)
        self.assertIn("record its publisher source as undeclared", text)
        self.assertIn("not a portable publisher identity", text)
        self.assertIn("remains unresolved until its publisher source is verified", text)
        self.assertIn("do not infer a publisher or install path", text)

    def test_preflight_distinguishes_transient_dependencies_from_terminal_gates(self):
        path = ROOT / "skills" / "spec-implement-loop" / "SKILL.md"
        text = path.read_text(encoding="utf-8").lower()
        preflight = text.split("## preflight", 1)[1].split("\n## ", 1)[0]
        self.assertIn("temporary prerequisite lookup/read failure", preflight)
        self.assertIn("blocks only work requiring it", preflight)
        self.assertIn("after all other preflight checks pass, continue independent work", preflight)
        self.assertIn("pause and report the exact dependency and recovery condition", preflight)
        self.assertIn(
            "retry only when the resolver, catalog, or source becomes available or new evidence changes the result",
            preflight,
        )
        self.assertIn(
            "stop the workflow only when the required source is confirmed absent, invalid, or permission-denied",
            preflight,
        )
        self.assertIn("stop for a failed repository, tracker, branch, or authorization gate", preflight)

    def test_skills_with_prerequisites_declare_conditional_skillroute(self):
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            name, prerequisites = read_prerequisites(path)
            if not prerequisites["skills"]:
                continue
            resolver = [
                item
                for item in prerequisites["tools"]
                if item["name"] == "SkillRoute CLI"
                and item.get("when") == "When a prerequisite skill is absent from the available skill list or its exact source cannot be verified."
            ]
            with self.subTest(skill=name):
                self.assertEqual(len(resolver), 1)

    def test_requirements_workflow_declares_only_direct_skills(self):
        path = ROOT / "skills" / "requirements-to-spec-tickets" / "SKILL.md"
        _, prerequisites = read_prerequisites(path)
        self.assertEqual(
            {item["name"] for item in prerequisites["skills"]},
            {"grill-with-docs", "to-spec", "to-tickets", "setup-matt-pocock-skills"},
        )

    def test_requirements_workflow_resolves_each_dependency_at_its_phase(self):
        path = ROOT / "skills" / "requirements-to-spec-tickets" / "SKILL.md"
        text = path.read_text(encoding="utf-8").lower()
        preflight = text.split("## 1. preflight", 1)[1].split("\n## 2.", 1)[0]
        child_protocol = text.split("## 4. child-session protocol", 1)[1].split("\n## 5.", 1)[0]
        self.assertIn("read each direct skill's current `skill.md` immediately before the phase that uses it", preflight)
        self.assertIn("sources needed for the first active phase", preflight)
        self.assertIn("temporary lookup/read failure blocks only the phase that needs that source", preflight)
        self.assertNotIn("every declared skill source is readable", preflight)
        self.assertIn("pause only the phase that needs it", child_protocol)
        self.assertIn("report it as missing only after confirming it is absent, invalid, or permission-denied", child_protocol)

    def test_readme_has_generic_install_command_and_guide_link(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("npx skills@latest add EltonZhang777/AggregateSkills", readme)
        self.assertIn("docs/prerequisites.md", readme)

    def test_guide_matches_every_skill_declaration(self):
        guide = (ROOT / "docs/prerequisites.md").read_text(encoding="utf-8")
        start = guide.index(START) + len(START)
        end = guide.index(END, start)
        self.assertEqual(render_prerequisite_list(), guide[start:end].strip())


if __name__ == "__main__":
    unittest.main()
