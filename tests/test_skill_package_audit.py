import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests" / "agent-acceptance" / "audit_skill_packages.py"
FIXTURE_ID = "generic-agent-skills-host-v1"
CRITERIA_BY_ROLE = {
    "completeness": (
        "entrypoint_and_format",
        "resource_closure",
        "references_and_cycles",
        "all_files_classified",
    ),
    "workflow_portability": (
        "generic_workflow_primary",
        "harness_independence",
        "capabilities_and_unavailable_behavior",
        "external_requirements",
    ),
}


class SkillPackageAuditCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "tests")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skills = self.base / "skills"
        self.skills.mkdir()

    def make_package(self, name, files):
        package = self.skills / name
        package.mkdir(parents=True)
        for relative, contents in files.items():
            destination = package / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(contents, bytes):
                destination.write_bytes(contents)
            else:
                destination.write_text(contents, encoding="utf-8", newline="")
        return package

    def run_cli(self, *arguments):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, arguments)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertTrue(completed.stdout, completed.stderr)
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            self.fail(f"CLI did not return JSON: {error}\n{completed.stdout}\n{completed.stderr}")
        return completed, payload

    def inventory(self):
        completed, payload = self.run_cli("inventory", "--skills-root", self.skills)
        self.assertEqual(completed.returncode, 0, payload)
        return payload

    def make_results(self, inventory, status_by_role=None):
        status_by_role = status_by_role or {}
        reports = []
        for package in inventory["packages"]:
            name = package["name"]
            for role, criteria_ids in CRITERIA_BY_ROLE.items():
                status = status_by_role.get((name, role), "pass")
                excerpt = f"# {name}"
                evidence = [{
                    "path": "SKILL.md",
                    "start_line": 1,
                    "end_line": 1,
                    "excerpt": excerpt,
                }]
                criteria = [
                    {
                        "id": criterion_id,
                        "status": status,
                        "evidence": evidence,
                        "findings": ([{"summary": f"Status {status} was reported.", "impact": "The stated criterion does not pass."}] if status != "pass" else []),
                    }
                    for criterion_id in criteria_ids
                ]
                file_coverage = []
                for file in package["files"]:
                    coverage = {
                        "path": file["path"],
                        "classification": "entrypoint" if file["path"] == "SKILL.md" else "supporting",
                        "disposition": "reviewed",
                        "evidence": [],
                    }
                    if file["path"] == "SKILL.md":
                        coverage["evidence"] = evidence
                    file_coverage.append(coverage)
                reports.append({
                    "schema_version": 1,
                    "skill_name": name,
                    "reviewer_id": f"{name}-{role}",
                    "reviewer_role": role,
                    "fixture_id": FIXTURE_ID,
                    "inventory_sha256": inventory["inventory_sha256"],
                    "overall_status": status,
                    "criteria": criteria,
                    "required_capabilities": [],
                    "file_coverage": file_coverage,
                })
        return {
            "schema_version": 1,
            "fixture_id": FIXTURE_ID,
            "inventory_sha256": inventory["inventory_sha256"],
            "reviews": reports,
        }

    def run_check(self, inventory, results, output=None):
        inventory_path = self.base / "inventory.json"
        results_path = self.base / "reviews.json"
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
        results_path.write_text(json.dumps(results), encoding="utf-8")
        arguments = [
            "check",
            "--skills-root",
            self.skills,
            "--inventory",
            inventory_path,
            "--results",
            results_path,
        ]
        if output is not None:
            arguments.extend(["--output", output])
        return self.run_cli(*arguments)

    def test_inventory_includes_generated_unused_and_hidden_files_in_stable_order(self):
        self.make_package("zeta", {
            "SKILL.md": "# zeta\n",
            ".generated/cache.json": '{"unused": true}\n',
        })
        self.make_package("alpha", {
            "SKILL.md": "# alpha\nsecond line\n",
            "references/unused.txt": "not referenced\n",
            ".hidden/config": "hidden resource\n",
        })

        first = self.inventory()
        second = self.inventory()

        self.assertEqual([item["name"] for item in first["packages"]], ["alpha", "zeta"])
        alpha_files = first["packages"][0]["files"]
        self.assertEqual(
            [item["path"] for item in alpha_files],
            [".hidden/config", "SKILL.md", "references/unused.txt"],
        )
        self.assertEqual(alpha_files[1]["line_count"], 2)
        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], 1)
        self.assertRegex(first["inventory_sha256"], r"^[0-9a-f]{64}$")

    def test_inventory_hashes_exact_bytes_and_includes_directories_without_entrypoints(self):
        self.make_package("broken-package", {"assets/payload.bin": b"\x00\x01\xff"})
        inventory = self.inventory()
        package = inventory["packages"][0]
        payload = package["files"][0]

        self.assertFalse(package["entrypoint_present"])
        self.assertIsNone(payload["line_count"])
        self.assertEqual(payload["sha256"], hashlib.sha256(b"\x00\x01\xff").hexdigest())
        self.assertEqual(payload["size_bytes"], 3)

    def test_inventory_writes_utf8_json_outside_skill_packages(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        destination = self.base / "audit" / "inventory.json"
        destination.parent.mkdir()

        completed, payload = self.run_cli(
            "inventory", "--skills-root", self.skills, "--output", destination
        )

        self.assertEqual(completed.returncode, 0, payload)
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), payload)
        self.assertFalse(destination.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_inventory_refuses_output_inside_skills_root(self):
        package = self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        destination = package / "inventory.json"

        completed, payload = self.run_cli(
            "inventory", "--skills-root", self.skills, "--output", destination
        )

        self.assertEqual(completed.returncode, 2)
        self.assertFalse(destination.exists())
        self.assertEqual(payload["overall_status"], "not_run")

    def test_check_accepts_complete_two_role_coverage_and_emits_review_evidence(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n", "unused.txt": "unused\n"})
        self.make_package("beta", {"SKILL.md": "# beta\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)

        completed, report = self.run_check(inventory, results)

        self.assertEqual(completed.returncode, 0, report)
        self.assertEqual(report["overall_status"], "pass")
        self.assertEqual(len(report["packages"]), 2)
        alpha = report["packages"][0]
        self.assertEqual(alpha["skill_name"], "alpha")
        self.assertEqual(alpha["status"], "pass")
        self.assertEqual(len(alpha["reviews"]), 2)
        self.assertEqual(
            {review["reviewer_role"] for review in alpha["reviews"]},
            set(CRITERIA_BY_ROLE),
        )
        self.assertTrue(alpha["reviews"][0]["criteria"][0]["evidence"])

    def test_check_writes_utf8_report_outside_skill_packages(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        destination = self.base / "audit" / "report.json"
        destination.parent.mkdir()

        completed, report = self.run_check(inventory, results, destination)

        self.assertEqual(completed.returncode, 0, report)
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), report)
        self.assertFalse(destination.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_check_refuses_report_output_inside_skills_root(self):
        package = self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()

        completed, report = self.run_check(
            inventory, self.make_results(inventory), package / "report.json"
        )

        self.assertEqual(completed.returncode, 2)
        self.assertFalse((package / "report.json").exists())
        self.assertIn("output_failed", {error["code"] for error in report["errors"]})

    def test_check_rejects_missing_and_duplicate_skill_review_coverage(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        results["reviews"].pop()

        completed, report = self.run_check(inventory, results)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("missing_reviewer", {error["code"] for error in report["errors"]})
        self.assertNotEqual(report["overall_status"], "pass")

        results = self.make_results(inventory)
        results["reviews"].append(dict(results["reviews"][0]))
        completed, report = self.run_check(inventory, results)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("duplicate_reviewer", {error["code"] for error in report["errors"]})

    def test_check_rejects_missing_duplicate_or_unsupported_file_coverage(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n", "extra.txt": "extra\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        results["reviews"][0]["file_coverage"].pop()

        completed, report = self.run_check(inventory, results)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("missing_file_coverage", {error["code"] for error in report["errors"]})

        results = self.make_results(inventory)
        results["reviews"][0]["file_coverage"].append(
            dict(results["reviews"][0]["file_coverage"][0])
        )
        completed, report = self.run_check(inventory, results)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("duplicate_file_coverage", {error["code"] for error in report["errors"]})

        results = self.make_results(inventory)
        results["reviews"][0]["file_coverage"][0]["path"] = "../outside.md"
        completed, report = self.run_check(inventory, results)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unsupported_file_coverage", {error["code"] for error in report["errors"]})

    def test_check_rejects_invalid_schema_and_manual_status_promotion(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        results["reviews"][0]["criteria"][0]["status"] = "fail"
        results["reviews"][0]["overall_status"] = "pass"

        completed, report = self.run_check(inventory, results)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("overall_status_mismatch", {error["code"] for error in report["errors"]})
        self.assertNotEqual(report["overall_status"], "pass")

        results = self.make_results(inventory)
        results["manual_status"] = "pass"
        completed, report = self.run_check(inventory, results)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("invalid_results_schema", {error["code"] for error in report["errors"]})

    def test_check_rejects_evidence_outside_inventory_or_source_lines(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\nsecond line\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        evidence = results["reviews"][0]["criteria"][0]["evidence"][0]
        evidence["path"] = "../../outside.md"

        completed, report = self.run_check(inventory, results)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unsupported_evidence", {error["code"] for error in report["errors"]})

    def test_check_rejects_criteria_without_evidence(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        results["reviews"][0]["criteria"][0]["evidence"] = []

        completed, report = self.run_check(inventory, results)

        self.assertEqual(completed.returncode, 2)
        self.assertIn("unsupported_evidence", {error["code"] for error in report["errors"]})

    def test_check_rejects_dot_as_evidence_path_without_crashing(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        results["reviews"][0]["criteria"][0]["evidence"][0]["path"] = "."

        completed, report = self.run_check(inventory, results)

        self.assertEqual(completed.returncode, 2)
        self.assertIn("unsupported_evidence", {error["code"] for error in report["errors"]})

    def test_check_rejects_required_capabilities_without_evidence(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        results["reviews"][0]["required_capabilities"] = [{
            "name": "Python",
            "scope": "core",
            "unavailable_behavior": "The workflow cannot run.",
            "evidence": [],
        }]

        completed, report = self.run_check(inventory, results)

        self.assertEqual(completed.returncode, 2)
        self.assertIn("unsupported_evidence", {error["code"] for error in report["errors"]})

        results = self.make_results(inventory)
        evidence = results["reviews"][0]["criteria"][0]["evidence"][0]
        evidence["start_line"] = 2
        evidence["end_line"] = 9
        evidence["excerpt"] = "not present"

        completed, report = self.run_check(inventory, results)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unsupported_evidence", {error["code"] for error in report["errors"]})

    def test_check_rejects_reviewer_disagreement_and_keeps_result_blocked(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()
        results = self.make_results(
            inventory,
            {("alpha", "workflow_portability"): "fail"},
        )

        completed, report = self.run_check(inventory, results)

        self.assertEqual(completed.returncode, 2)
        self.assertIn("reviewer_disagreement", {error["code"] for error in report["errors"]})
        self.assertEqual(report["overall_status"], "blocked")
        self.assertNotEqual(report["packages"][0]["status"], "pass")

    def test_check_rejects_unhashable_fields_and_boolean_schema_versions(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\\n"})
        inventory = self.inventory()

        malformed_reports = []
        results = self.make_results(inventory)
        results["reviews"][0]["reviewer_role"] = []
        malformed_reports.append(results)
        results = self.make_results(inventory)
        results["reviews"][0]["overall_status"] = []
        malformed_reports.append(results)
        results = self.make_results(inventory)
        results["schema_version"] = True
        malformed_reports.append(results)
        results = self.make_results(inventory)
        results["reviews"][0]["schema_version"] = True
        malformed_reports.append(results)

        for results in malformed_reports:
            completed, report = self.run_check(inventory, results)
            self.assertEqual(completed.returncode, 2, report)
            self.assertNotEqual(report["overall_status"], "pass")

    def test_check_rejects_duplicate_json_keys(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\\n"})
        inventory = self.inventory()
        inventory_path = self.base / "inventory.json"
        results_path = self.base / "reviews.json"
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
        results_path.write_text(
            '{"schema_version": 1, "schema_version": 1}',
            encoding="utf-8",
        )

        completed, report = self.run_cli(
            "check",
            "--skills-root",
            self.skills,
            "--inventory",
            inventory_path,
            "--results",
            results_path,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("input_failed", {error["code"] for error in report["errors"]})
        self.assertNotEqual(report["overall_status"], "pass")
    def test_check_preserves_blocked_and_not_run_statuses(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()

        for status in ("blocked", "not_run"):
            results = self.make_results(
                inventory,
                {("alpha", role): status for role in CRITERIA_BY_ROLE},
            )
            completed, report = self.run_check(inventory, results)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(report["overall_status"], status)

    def test_check_rejects_stale_inventory_after_package_change(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        (self.skills / "alpha" / "SKILL.md").write_text("# changed\n", encoding="utf-8")

        completed, report = self.run_check(inventory, results)

        self.assertEqual(completed.returncode, 2)
        self.assertIn("stale_inventory", {error["code"] for error in report["errors"]})

    def test_check_rejects_inventory_types_that_compare_equal_to_valid_values(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n"})
        inventory = self.inventory()
        inventory["packages"][0]["entrypoint_present"] = 1
        canonical = json.dumps(
            inventory["packages"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        inventory["inventory_sha256"] = hashlib.sha256(canonical).hexdigest()

        completed, report = self.run_check(inventory, self.make_results(inventory))

        self.assertEqual(completed.returncode, 2)
        self.assertIn("stale_inventory", {error["code"] for error in report["errors"]})

    def test_check_rejects_empty_skill_inventory(self):
        inventory = self.inventory()

        completed, report = self.run_check(inventory, self.make_results(inventory))

        self.assertEqual(completed.returncode, 2)
        self.assertNotEqual(report["overall_status"], "pass")
        self.assertIn("empty_inventory", {error["code"] for error in report["errors"]})

    def test_check_does_not_modify_any_skill_package_file(self):
        self.make_package("alpha", {"SKILL.md": "# alpha\n", "unused.txt": "data\n"})
        inventory = self.inventory()
        results = self.make_results(inventory)
        before = {
            path.relative_to(self.skills).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (self.skills / "alpha").rglob("*")
            if path.is_file()
        }

        completed, _ = self.run_check(inventory, results)

        after = {
            path.relative_to(self.skills).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (self.skills / "alpha").rglob("*")
            if path.is_file()
        }
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
