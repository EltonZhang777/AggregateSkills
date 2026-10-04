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
