import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
START = "<!-- prerequisite-list:start -->"
END = "<!-- prerequisite-list:end -->"


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
    if any(not isinstance(entries, list) for entries in prerequisites.values()):
        raise ValueError(f"Prerequisite categories must be lists: {path}")
    if name[1] != path.parent.name:
        raise ValueError(f"Skill name does not match directory: {path}")
    return name[1], prerequisites


def dependency_rows(category):
    dependencies = {}
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        skill_name, prerequisites = read_prerequisites(path)
        for item in prerequisites[category]:
            expected_length = 2 if category == "skills" else (4 if category == "tools" else 3)
            if not isinstance(item, list) or len(item) != expected_length or not all(isinstance(value, str) and value for value in item):
                raise ValueError(f"Invalid {category} prerequisite in {path}")
            name, source = item[:2]
            install = item[2] if category != "skills" else f"npx skills@latest add {source} --skill={name}"
            setup = item[3] if category == "tools" else ""
            existing = dependencies.setdefault(
                name,
                {"source": source, "install": install, "setup": setup, "required_by": set()},
            )
            if (existing["source"], existing["install"], existing["setup"]) != (source, install, setup):
                raise ValueError(f"Conflicting install details for {category} prerequisite {name}")
            if skill_name in existing["required_by"]:
                raise ValueError(f"Duplicate {category} prerequisite {name} in {skill_name}")
            existing["required_by"].add(skill_name)

    rows = []
    for name in sorted(dependencies):
        dependency = dependencies[name]
        source = dependency["source"]
        source_url = f"https://github.com/{source}" if category == "skills" else source
        source_label = source if category == "skills" else f"{name} project"
        rows.append(
            (
                name,
                f"[{source_label}]({source_url})",
                dependency["install"] + ("; " + dependency["setup"] if dependency["setup"] else ""),
                ", ".join(sorted(dependency["required_by"])),
            )
        )
    return rows


def render_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def render_prerequisite_list():
    skill_rows = dependency_rows("skills")
    mcp_rows = dependency_rows("mcps")
    tool_rows = dependency_rows("tools")
    skills = render_table(
        ("Skill", "Source", "Install", "Required by"),
        skill_rows,
    )
    return "\n\n".join(
        (
            "### Agent Skills\n\n" + (skills if skill_rows else "None currently."),
            "### MCPs\n\n" + (render_table(("MCP", "Source", "Install", "Required by"), mcp_rows) if mcp_rows else "None currently."),
            "### Other runtime tools\n\n" + (render_table(("Tool", "Source", "Install", "Required by"), tool_rows) if tool_rows else "None currently."),
        )
    )


class PrerequisiteGuideTests(unittest.TestCase):
    maxDiff = None

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
