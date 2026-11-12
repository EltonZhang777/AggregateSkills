"""Public artifact contracts for the standalone RFC 2119 audit skill."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "rfc2119-audit"
REFERENCE = SKILL_ROOT / "references" / "rfc2119-reference.md"


class Rfc2119AuditArtifactTests(unittest.TestCase):
    def test_skill_is_standalone_and_declares_its_runtime(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1].lower()

        self.assertIn("name: rfc2119-audit", frontmatter)
        self.assertIn("read-only", frontmatter)
        self.assertIn("does not rewrite", frontmatter)
        self.assertIn("## Dependencies", text)
        self.assertIn("declares no skill prerequisite", text.lower())
        self.assertIn("python 3.9 or later", text.lower())
        self.assertLess(text.index("## Dependencies"), text.index("## Workflow"))

    def test_reference_preserves_the_complete_vocabulary(self):
        text = REFERENCE.read_text(encoding="utf-8")
        lowered = text.lower()

        for heading in (
            "## RFC 2119 keywords",
            "## Applying the vocabulary",
            "## Exception handling",
        ):
            self.assertIn(heading, text)
        for keyword in (
            "MUST",
            "REQUIRED",
            "SHALL",
            "MUST NOT",
            "SHALL NOT",
            "SHOULD",
            "RECOMMENDED",
            "SHOULD NOT",
            "NOT RECOMMENDED",
            "MAY",
            "OPTIONAL",
        ):
            self.assertIn(f"`{keyword}`", text)
        for concept in (
            "descriptive facts",
            "illustrative example prose",
            "external documentation",
            "verbatim quotations",
            "normative for this skill's workflow",
            "advisory when used to review arbitrary audited roots",
        ):
            self.assertIn(concept, lowered)
        self.assertIsNone(
            re.search(r"skills/(?!rfc2119-audit/)[a-z0-9-]+/", text)
        )

    def test_shipped_product_text_has_no_upstream_project_reference(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        entry = next(
            line for line in readme.splitlines()
            if line.startswith("- [rfc2119-audit]")
        )
        product_paths = sorted(
            path for path in SKILL_ROOT.rglob("*") if path.is_file()
        ) + sorted(ROOT.glob("tests/test_rfc2119*.py"))
        products = [path.read_text(encoding="utf-8") for path in product_paths]
        products.append(entry)
        forbidden_project = "blas" "phem" "ous"

        for text in products:
            self.assertNotIn(forbidden_project, text.lower())

    def test_readme_catalog_describes_the_read_only_audit(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        entry = next(
            line for line in readme.splitlines()
            if line.startswith("- [rfc2119-audit]")
        )

        self.assertIn("skills/rfc2119-audit/SKILL.md", entry)
        self.assertIn("read-only", entry.lower())
        self.assertIn("candidate", entry.lower())


if __name__ == "__main__":
    unittest.main()
