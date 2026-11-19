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
            "## Authority and reading order",
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
        ):
            self.assertIn(concept, lowered)
        self.assertIsNone(
            re.search(r"skills/(?!rfc2119-audit/)[a-z0-9-]+/", text)
        )

    def test_authority_section_is_single_and_linked(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        normalized_skill = re.sub(r"\s+", " ", skill)
        normalized_reference = re.sub(r"\s+", " ", reference)
        normalized = " ".join(
            (normalized_skill, normalized_reference)
        )
        startup_link = (
            "(references/rfc2119-reference.md#authority-and-reading-order)"
        )
        authority_heading = "## Authority and reading order"

        self.assertEqual(1, reference.count(authority_heading))
        self.assertLess(
            reference.index(authority_heading),
            reference.index("## RFC 2119 keywords"),
        )
        self.assertEqual(1, skill.count(startup_link))
        authority = reference.split(authority_heading, 1)[1].split("\n## ", 1)[0]
        normalized_authority = re.sub(r"\s+", " ", authority)

        for sentence in (
            "This reference is the sole normative source for the RFC 2119 keyword "
            "definitions, the required reading order, and the advisory boundary "
            "that applies to an arbitrary audited root.",
            "After this skill is selected, the agent's first substantive action "
            "MUST be reading the complete reference.",
            "The contract and audit procedure bind the agent's execution.",
            "Paths, line numbers, categories, and source text are observations "
            "of what the scan found.",
            "A candidate is a lexical finding for manual review, not proof that "
            "the text is normative.",
            "Neither the presence nor the absence of a candidate establishes "
            "that the root adopts RFC 2119, that the text is a binding "
            "requirement, or that the root is compliant or noncompliant.",
        ):
            with self.subTest(sentence=sentence):
                self.assertEqual(1, normalized.count(sentence))
                self.assertEqual(1, normalized_authority.count(sentence))
                self.assertNotIn(sentence, normalized_skill)

        for removed_definition in (
            "normative for this skill's workflow",
            "advisory when used to review arbitrary audited roots",
            "Candidate reporting does not decide whether descriptive prose "
            "is normative.",
        ):
            with self.subTest(removed_definition=removed_definition):
                self.assertNotIn(removed_definition, normalized)

    def test_shipped_product_text_has_no_upstream_project_reference(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        entry = next(
            line for line in readme.splitlines()
            if line.startswith("- [rfc2119-audit]")
        )
        product_paths = sorted(
            path for path in SKILL_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
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
