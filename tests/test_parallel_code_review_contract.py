import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "parallel-code-review"
SCRIPT = SKILL_ROOT / "scripts" / "review_contract.py"
UPSTREAM_SOURCE = SKILL_ROOT / "references" / "tracks" / "code-review.md"
ROUTING_MARKER = "<!-- parallel-code-review-routing-table -->"
METADATA_MARKER = "<!-- parallel-code-review-track-metadata -->"


def run_contract(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def result_json(completed):
    return json.loads(completed.stdout)


def git(repo, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def snapshot_tree(root):
    snapshot = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            snapshot[path.relative_to(root).as_posix()] = path.read_bytes()
    return snapshot


def write(repo, relative_path, content):
    path = Path(repo) / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def toggle_line_endings(path):
    data = path.read_bytes()
    if b"\r\n" in data:
        toggled = data.replace(b"\r\n", b"\n")
    elif b"\n" in data:
        toggled = data.replace(b"\n", b"\r\n")
    else:
        return False
    if toggled == data:
        return False
    path.write_bytes(toggled)
    return True


def freeze_acceptance_bundle(temp_dir):
    bundle = Path(temp_dir) / "bundle"
    completed = run_contract(
        "freeze",
        "--output",
        bundle,
        "--patch",
        SKILL_ROOT / "references" / "acceptance-fixture.patch",
        "--tree-root",
        SKILL_ROOT / "references" / "acceptance-tree",
        "--requirements",
        SKILL_ROOT / "references" / "acceptance-requirements.md",
        "--standards",
        SKILL_ROOT / "references" / "acceptance-standard.md",
        "--not-run",
        "repository tests=Synthetic patch is review-only.",
        "--contract-root",
        SKILL_ROOT,
        "--upstream",
        f"/code-review={UPSTREAM_SOURCE}",
    )
    return completed, bundle


def contract_args(skill_root=SKILL_ROOT, upstream=UPSTREAM_SOURCE):
    return [
        "--contract-root",
        str(skill_root),
        "--upstream",
        f"/code-review={upstream}",
    ]


def rewrite_manifest_with_attestation(bundle, manifest):
    manifest_bytes = json.dumps(
        manifest,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    (bundle / "manifest.json").write_bytes(manifest_bytes)
    attestation_path = bundle / "attestation.json"
    attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
    attestation["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    attestation_path.write_text(
        json.dumps(
            attestation,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def valid_code_review_envelope(attestation, checked_sha="e" * 64):
    return {
        "contract_version": 1,
        "track_id": "code-review",
        "invocation_id": "code-review-001",
        "launch_status": "launched",
        "attestation": {
            "manifest_sha256": attestation["manifest_sha256"],
            "patch_sha256": attestation["patch_sha256"],
            "patch_size_bytes": attestation["patch_size_bytes"],
            "included_paths": attestation["included_paths"],
        },
        "coverage": {
            "status": "complete",
            "checked": [
                {
                    "path": "src/discounts.py",
                    "sha256": checked_sha,
                }
            ],
            "unchecked": [
                {
                    "path": "repository tests",
                    "reason": "The synthetic patch is review-only.",
                }
            ],
            "checks": [
                {
                    "name": "repository tests",
                    "result": "not_run",
                    "reason": "The synthetic patch is review-only.",
                }
            ],
        },
        "native": {
            "title": "/code-review",
            "sections": [
                {"name": "Standards and Quality", "finding_ids": ["STD-01"]},
                {"name": "Spec Conformance", "finding_ids": ["SPEC-01"]},
            ],
        },
        "findings": [
            {
                "native_axis": "Standards and Quality",
                "native_id": "STD-01",
                "native_severity": "high",
                "severity": "P1",
                "severity_rationale": "Binary floating point can produce an incorrect monetary preview.",
                "title": "Preview converts Decimal money to float",
                "location": {"path": "src/discounts.py", "line": 9},
                "what_this_is": "The tax preview converts Decimal money to binary floating point.",
                "problem": "Float arithmetic can change the displayed amount.",
                "fix": "Keep Decimal arithmetic through the preview.",
                "if_we_skip_it": "Customers can receive a misleading price estimate.",
                "citations": [
                    {
                        "path": "src/discounts.py",
                        "line": 9,
                        "quote": "    return Decimal(str(float(amount) * 1.08))",
                    }
                ],
            },
            {
                "native_axis": "Spec Conformance",
                "native_id": "SPEC-01",
                "native_severity": "medium",
                "severity": "P1",
                "severity_rationale": "The explicit requirement to reject unknown coupons is not implemented.",
                "title": "Unknown coupon codes are accepted",
                "location": {"path": "src/discounts.py", "line": 6},
                "what_this_is": "Unknown coupon codes fall through as valid redemptions.",
                "problem": "The implementation returns the unchanged total instead of an invalid-coupon error.",
                "fix": "Reject every code other than SAVE10 with an explicit invalid-coupon error.",
                "if_we_skip_it": "An acceptance criterion remains unmet and callers cannot explain the ignored code.",
                "citations": [
                    {
                        "path": "src/discounts.py",
                        "line": 6,
                        "quote": "    return amount",
                    }
                ],
            },
        ],
    }


def metadata(track_name, source="https://example.com/skills", inputs=None, version=1):
    return {
        "contract_version": version,
        "upstream": {"name": track_name, "source": source},
        "required_inputs": inputs or ["patch"],
    }


def write_adapter(skill_root, filename, payload, extra=""):
    path = skill_root / "references" / "tracks" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(payload, str):
        payload = json.dumps(payload, indent=2)
    path.write_text(
        f"{METADATA_MARKER}\n\n```json\n{payload}\n```\n\n# Adapter\n{extra}",
        encoding="utf-8",
    )
    return path


def write_routing(skill_root, rows):
    path = skill_root / "references" / "routing-table.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Track Routing Table",
        "",
        ROUTING_MARKER,
        "",
        "| Track ID | Adapter document |",
        "| --- | --- |",
    ]
    lines.extend(f"| {track_id} | {adapter} |" for track_id, adapter in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class ParallelCodeReviewTestHelperTests(unittest.TestCase):
    def test_line_ending_toggle_changes_both_checkout_styles_and_preserves_static_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "text.md"
            path.write_bytes(b"line one\nline two\n")
            self.assertTrue(toggle_line_endings(path))
            self.assertEqual(b"line one\r\nline two\r\n", path.read_bytes())
            self.assertTrue(toggle_line_endings(path))
            self.assertEqual(b"line one\nline two\n", path.read_bytes())

            path.write_bytes(b"no trailing newline")
            self.assertFalse(toggle_line_endings(path))
            self.assertEqual(b"no trailing newline", path.read_bytes())


class ParallelCodeReviewPreflightTests(unittest.TestCase):
    def test_shipped_routing_table_is_authoritative_and_code_review_dependencies_are_explicit(self):
        completed = run_contract(
            "preflight",
            "--skill-root",
            SKILL_ROOT,
            "--upstream",
            f"/code-review={UPSTREAM_SOURCE}",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = result_json(completed)
        self.assertEqual("ready", result["status"])
        self.assertEqual(["code-review"], [track["track_id"] for track in result["tracks"]])
        self.assertEqual(
            ["patch", "tree", "requirements", "standards", "checks", "exclusions"],
            result["tracks"][0]["required_inputs"],
        )
        self.assertEqual("/code-review", result["dependencies"][0]["name"])
        self.assertEqual("https://github.com/mattpocock/skills", result["dependencies"][0]["source"])
        self.assertEqual("local_file", result["dependencies"][0]["kind"])

    def test_routing_row_order_controls_dispatch_and_pin_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / "skill"
            write_adapter(skill_root, "second.md", metadata("/second"))
            write_adapter(skill_root, "first.md", metadata("/first"))
            write_routing(
                skill_root,
                [
                    ("second", "references/tracks/second.md"),
                    ("first", "references/tracks/first.md"),
                ],
            )

            completed = run_contract(
                "preflight",
                "--skill-root",
                skill_root,
                "--upstream",
                f"/second={UPSTREAM_SOURCE}",
                "--upstream",
                f"/first={UPSTREAM_SOURCE}",
            )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = result_json(completed)
        self.assertEqual(["second", "first"], [track["track_id"] for track in result["tracks"]])
        self.assertEqual(["second", "first"], [pin["track_id"] for pin in result["pins"]["adapters"]])

    def test_same_upstream_name_with_different_sources_fails_before_pins(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / "skill"
            write_adapter(
                skill_root,
                "second.md",
                metadata("/shared", source="https://example.com/source-one"),
            )
            write_adapter(
                skill_root,
                "first.md",
                metadata("/shared", source="https://example.com/source-two"),
            )
            write_routing(
                skill_root,
                [
                    ("second", "references/tracks/second.md"),
                    ("first", "references/tracks/first.md"),
                ],
            )
            blocked = run_contract(
                "preflight",
                "--skill-root",
                skill_root,
                "--upstream",
                f"/shared={UPSTREAM_SOURCE}",
            )

            write_adapter(
                skill_root,
                "first.md",
                metadata("/shared", source="https://example.com/source-one"),
            )
            shared = run_contract(
                "preflight",
                "--skill-root",
                skill_root,
                "--upstream",
                f"/shared={UPSTREAM_SOURCE}",
            )

        self.assertNotEqual(0, blocked.returncode)
        blocked_result = result_json(blocked)
        self.assertEqual("blocked", blocked_result["status"])
        self.assertIn(
            "upstream_identity_conflict",
            [error["code"] for error in blocked_result["errors"]],
        )
        self.assertNotIn("pins", blocked_result)

        self.assertEqual(shared.returncode, 0, shared.stderr or shared.stdout)
        shared_result = result_json(shared)
        self.assertEqual(["second", "first"], [track["track_id"] for track in shared_result["tracks"]])
        self.assertEqual(1, len(shared_result["pins"]["upstreams"]))
        upstream_pin = shared_result["pins"]["upstreams"][0]
        self.assertEqual("/shared", upstream_pin["name"])
        self.assertEqual("https://example.com/source-one", upstream_pin["source"])
        self.assertEqual(
            hashlib.sha256(UPSTREAM_SOURCE.read_bytes()).hexdigest(),
            upstream_pin["sha256"],
        )

    def test_invalid_routes_and_metadata_fail_before_dispatch(self):
        cases = {
            "missing routing table": (None, [], "routing_table_missing"),
            "empty routing table": ("empty", [], "routing_table_empty"),
            "duplicate track ID": (
                [
                    ("duplicate", "references/tracks/one.md"),
                    ("duplicate", "references/tracks/two.md"),
                ],
                {
                    "one.md": metadata("/one"),
                    "two.md": metadata("/two"),
                },
                "duplicate_track_id",
            ),
            "missing adapter": (
                [("missing", "references/tracks/missing.md")],
                {},
                "adapter_missing",
            ),
            "malformed metadata": (
                [("broken", "references/tracks/broken.md")],
                {"broken.md": "{not json"},
                "metadata_malformed",
            ),
            "version mismatch": (
                [("old", "references/tracks/old.md")],
                {"old.md": metadata("/old", version=2)},
                "metadata_version_mismatch",
            ),
            "orphan adapter": (
                [("routed", "references/tracks/routed.md")],
                {
                    "routed.md": metadata("/routed"),
                    "orphan.md": metadata("/orphan"),
                },
                "orphan_adapter",
            ),
            "duplicate metadata block": (
                [("twice", "references/tracks/twice.md")],
                {
                    "twice.md": (
                        f"{METADATA_MARKER}\n```json\n{json.dumps(metadata('/twice'))}\n```\n"
                        f"{METADATA_MARKER}\n```json\n{json.dumps(metadata('/twice'))}\n```"
                    )
                },
                "metadata_duplicate",
            ),
            "unknown metadata field": (
                [("extra", "references/tracks/extra.md")],
                {"extra.md": {**metadata("/extra"), "native_sections": []}},
                "metadata_unknown_field",
            ),
            "unknown required input": (
                [("input", "references/tracks/input.md")],
                {"input.md": metadata("/input", inputs=["patch", "native_report"])},
                "metadata_unknown_input",
            ),
        }

        for label, (routing, adapters, expected_code) in cases.items():
            with self.subTest(label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    skill_root = Path(temp_dir) / "skill"
                    if routing not in (None, "empty"):
                        for filename, payload in adapters.items():
                            write_adapter(skill_root, filename, payload)
                    if routing is not None:
                        write_routing(skill_root, [] if routing == "empty" else routing)
                    completed = run_contract("preflight", "--skill-root", skill_root)

                self.assertNotEqual(0, completed.returncode)
                result = result_json(completed)
                self.assertEqual("blocked", result["status"])
                self.assertIn(expected_code, [error["code"] for error in result["errors"]])

    def test_unreadable_adapter_and_invalid_metadata_shape_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / "skill"
            unreadable = skill_root / "references" / "tracks" / "unreadable.md"
            unreadable.mkdir(parents=True)
            write_routing(skill_root, [("unreadable", "references/tracks/unreadable.md")])
            completed = run_contract("preflight", "--skill-root", skill_root)

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("adapter_unreadable", [error["code"] for error in result_json(completed)["errors"]])

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / "skill"
            invalid = metadata("/invalid")
            del invalid["upstream"]["source"]
            write_adapter(skill_root, "invalid.md", invalid)
            write_routing(skill_root, [("invalid", "references/tracks/invalid.md")])
            completed = run_contract("preflight", "--skill-root", skill_root)

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("metadata_invalid", [error["code"] for error in result_json(completed)["errors"]])

    def test_missing_adapter_metadata_fails_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / "skill"
            adapter = skill_root / "references" / "tracks" / "missing.md"
            adapter.parent.mkdir(parents=True)
            adapter.write_text("# Adapter without metadata\n", encoding="utf-8")
            write_routing(skill_root, [("missing", "references/tracks/missing.md")])
            completed = run_contract("preflight", "--skill-root", skill_root)

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("metadata_missing", [error["code"] for error in result_json(completed)["errors"]])

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / "skill"
            adapter = skill_root / "references" / "tracks" / "late.md"
            adapter.parent.mkdir(parents=True)
            adapter.write_text(
                f"# Adapter\n\n{METADATA_MARKER}\n\n```json\n"
                f"{json.dumps(metadata('/late'))}\n```\n",
                encoding="utf-8",
            )
            write_routing(skill_root, [("late", "references/tracks/late.md")])
            completed = run_contract("preflight", "--skill-root", skill_root)

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("metadata_malformed", [error["code"] for error in result_json(completed)["errors"]])

    def test_preflight_requires_a_resolved_upstream_text_pin(self):
        completed = run_contract("preflight", "--skill-root", SKILL_ROOT)

        self.assertNotEqual(0, completed.returncode)
        result = result_json(completed)
        self.assertEqual("blocked", result["status"])
        self.assertIn("upstream_unresolved", [error["code"] for error in result["errors"]])

    def test_preflight_rejects_unreadable_empty_and_hash_mismatched_upstreams(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            empty = write(temp_dir, "empty-skill.md", "")
            cases = {
                "unreadable": (
                    [
                        "--upstream",
                        "/code-review=/does/not/exist/SKILL.md",
                    ],
                    "upstream_unreadable",
                ),
                "empty": (
                    [
                        "--upstream",
                        f"/code-review={empty}",
                    ],
                    "upstream_empty",
                ),
                "hash mismatch": (
                    [
                        "--upstream",
                        f"/code-review={UPSTREAM_SOURCE}",
                        "--upstream-sha",
                        f"/code-review={'0' * 64}",
                    ],
                    "upstream_hash_mismatch",
                ),
            }
            for label, (extra_args, expected_code) in cases.items():
                with self.subTest(label):
                    completed = run_contract(
                        "preflight",
                        "--skill-root",
                        SKILL_ROOT,
                        *extra_args,
                    )
                    self.assertNotEqual(0, completed.returncode)
                    self.assertIn(
                        expected_code,
                        [error["code"] for error in result_json(completed)["errors"]],
                    )

    def test_preflight_requires_exact_remote_identity_and_accepts_a_complete_host_pin(self):
        source_bytes = UPSTREAM_SOURCE.read_bytes()
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        normalized_hash = hashlib.sha256(
            source_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        ).hexdigest()
        common = [
            "--skill-root",
            SKILL_ROOT,
            "--upstream",
            "/code-review=https://example.com/code-review/SKILL.md",
        ]
        missing_size = run_contract(
            "preflight",
            *common,
            "--upstream-exact-sha",
            f"/code-review={source_hash}",
        )
        completed = run_contract(
            "preflight",
            *common,
            "--upstream-exact-sha",
            f"/code-review={source_hash}",
            "--upstream-size",
            f"/code-review={len(source_bytes)}",
            "--upstream-sha",
            f"/code-review={normalized_hash}",
        )

        self.assertNotEqual(0, missing_size.returncode)
        self.assertIn(
            "upstream_unresolved",
            [error["code"] for error in result_json(missing_size)["errors"]],
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = result_json(completed)
        self.assertEqual(
            "https://example.com/code-review/SKILL.md",
            result["dependencies"][0]["resolved_uri"],
        )
        self.assertEqual(source_hash, result["dependencies"][0]["source_sha256"])
        self.assertEqual(len(source_bytes), result["dependencies"][0]["size_bytes"])
        self.assertEqual("remote_uri", result["dependencies"][0]["kind"])
        self.assertEqual(
            normalized_hash,
            result["dependencies"][0]["normalized_sha256"],
        )
        upstream_pin = result["pins"]["upstreams"][0]
        self.assertEqual("/code-review", upstream_pin["name"])
        self.assertEqual("https://github.com/mattpocock/skills", upstream_pin["source"])
        self.assertEqual("remote_uri", upstream_pin["kind"])
        self.assertEqual(source_hash, upstream_pin["sha256"])
        self.assertEqual(len(source_bytes), upstream_pin["size_bytes"])


class ParallelCodeReviewFreezeTests(unittest.TestCase):
    def make_repo(self, temp_dir):
        repo = Path(temp_dir) / "repo"
        repo.mkdir()
        git(repo, "init")
        git(repo, "config", "user.name", "Review Test")
        git(repo, "config", "user.email", "review@example.com")
        write(repo, "src/example.py", "value = 1\n")
        write(repo, "README.md", "Example\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "initial")
        return repo

    def test_git_range_produces_frozen_tree_manifest_and_attestation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            write(repo, "vendor/generated.py", "generated = True\n")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "vendor baseline")
            base = git(repo, "rev-parse", "HEAD")
            write(repo, "src/example.py", "value = 2\n")
            write(repo, "tests/test_example.py", "def test_value():\n    assert True\n")
            requirements = write(temp_dir, "requirements.md", "Value must be 2.\n")
            standards = write(temp_dir, "standards.md", "Use tests.\n")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "change")
            head = git(repo, "rev-parse", "HEAD")
            bundle = Path(temp_dir) / "bundle"
            before = snapshot_tree(repo)

            completed = run_contract(
                "freeze",
                "--repo",
                repo,
                "--output",
                bundle,
                "--range",
                f"{base}...{head}",
                "--requirements",
                requirements,
                "--standards",
                standards,
                "--check",
                "unit tests=passed",
                "--not-run",
                "manual review=No host capability",
                "--exclude",
                "vendor/=third-party source",
                *contract_args(),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertEqual(before, snapshot_tree(repo))
            result = result_json(completed)
            manifest_bytes = (bundle / "manifest.json").read_bytes()
            manifest = json.loads(manifest_bytes)
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            patch = (bundle / "scope" / "patch.diff").read_bytes()
            tree_file = bundle / "tree" / "src" / "example.py"

            self.assertEqual("frozen", result["status"])
            self.assertEqual(
                hashlib.sha256(manifest_bytes).hexdigest(),
                attestation["manifest_sha256"],
            )
            self.assertEqual(hashlib.sha256(patch).hexdigest(), attestation["patch_sha256"])
            self.assertEqual(len(patch), attestation["patch_size_bytes"])
            self.assertEqual(
                ["README.md", "src/example.py", "tests/test_example.py"],
                manifest["scope"]["included_paths"],
            )
            self.assertEqual("git_range", manifest["scope"]["kind"])
            self.assertEqual(base, manifest["scope"]["base"])
            self.assertEqual(head, manifest["scope"]["head"])
            self.assertEqual("value = 2\n", tree_file.read_text(encoding="utf-8"))
            self.assertFalse((bundle / "tree" / "vendor" / "generated.py").exists())
            self.assertNotIn("vendor/generated.py", manifest["scope"]["included_paths"])
            self.assertEqual("passed", manifest["checks"][0]["result"])
            self.assertEqual("not_run", manifest["checks"][1]["result"])
            self.assertEqual("third-party source", manifest["exclusions"][0]["reason"])
            self.assertEqual(
                ["checks", "exclusions", "patch", "requirements", "standards", "tree"],
                sorted(manifest["input_status"]),
            )
            self.assertEqual("included", manifest["input_status"]["requirements"])
            self.assertEqual("included", manifest["input_status"]["standards"])
            self.assertEqual(
                ["code-review"],
                [track["track_id"] for track in manifest["contract"]["tracks"]],
            )
            bundle_before = snapshot_tree(bundle)

            verified = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--repo",
                repo,
                *contract_args(),
            )
            self.assertEqual(bundle_before, snapshot_tree(bundle))

        self.assertEqual(verified.returncode, 0, verified.stderr or verified.stdout)
        self.assertEqual("current", result_json(verified)["status"])

    def test_explicit_patch_and_supplied_tree_are_immutable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            patch_path = write(
                temp_dir,
                "change.patch",
                "diff --git a/src/example.py b/src/example.py\n"
                "--- a/src/example.py\n"
                "+++ b/src/example.py\n"
                "@@ -1 +1 @@\n"
                "-value = 1\n"
                "+value = 2\n",
            )
            tree_root = Path(temp_dir) / "tree-source"
            write(tree_root, "src/example.py", "value = 2\n")
            bundle = Path(temp_dir) / "bundle"

            completed = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                patch_path,
                "--tree-root",
                tree_root,
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("explicit_patch", manifest["scope"]["kind"])
            self.assertEqual(["src/example.py"], manifest["scope"]["included_paths"])
            self.assertEqual(
                patch_path.read_bytes(),
                (bundle / "scope" / "patch.diff").read_bytes(),
            )
            self.assertEqual(
                "value = 2\n",
                (bundle / "tree" / "src" / "example.py").read_text(encoding="utf-8"),
            )

            patch_path.write_text(patch_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            verified = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--patch",
                patch_path,
                *contract_args(),
            )

        self.assertNotEqual(0, verified.returncode)
        self.assertEqual("stale", result_json(verified)["status"])

    def test_frozen_uncommitted_work_includes_untracked_files_and_detects_staleness(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            write(repo, "src/example.py", "value = 2\n")
            write(repo, "src/new.py", "created = True\n")
            bundle = Path(temp_dir) / "bundle"
            before = snapshot_tree(repo)

            completed = run_contract(
                "freeze",
                "--repo",
                repo,
                "--output",
                bundle,
                "--uncommitted",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertEqual(before, snapshot_tree(repo))
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            patch = (bundle / "scope" / "patch.diff").read_text(encoding="utf-8")
            self.assertEqual("frozen_uncommitted", manifest["scope"]["kind"])
            self.assertEqual(
                ["README.md", "src/example.py", "src/new.py"],
                manifest["scope"]["included_paths"],
            )
            self.assertIn("b/src/example.py", patch)
            self.assertIn("b/src/new.py", patch)
            self.assertEqual(
                "created = True\n",
                (bundle / "tree" / "src" / "new.py").read_text(encoding="utf-8"),
            )
            bundle_before = snapshot_tree(bundle)

            current = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--repo",
                repo,
                *contract_args(),
            )
            self.assertEqual(current.returncode, 0, current.stderr or current.stdout)
            self.assertEqual("current", result_json(current)["status"])
            self.assertEqual(bundle_before, snapshot_tree(bundle))

            write(repo, "src/new.py", "created = False\n")
            stale = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--repo",
                repo,
                *contract_args(),
            )

        self.assertNotEqual(0, stale.returncode)
        self.assertEqual("stale", result_json(stale)["status"])

    def test_freeze_refuses_output_inside_reviewed_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            write(repo, "src/example.py", "value = 2\n")
            before = snapshot_tree(repo)

            completed = run_contract(
                "freeze",
                "--repo",
                repo,
                "--output",
                repo / ".review",
                "--uncommitted",
                *contract_args(),
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertEqual("output_inside_repository", result_json(completed)["errors"][0]["code"])
            self.assertEqual(before, snapshot_tree(repo))

    def test_freeze_refuses_output_inside_tree_before_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tree_root = Path(temp_dir) / "tree"
            write(tree_root, "src/example.py", "value = 2\n")
            bundle = tree_root / "review-bundle"

            completed = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                tree_root,
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        self.assertEqual("output_inside_source", result_json(completed)["errors"][0]["code"])
        self.assertFalse(bundle.exists())

    def test_explicit_patch_with_parent_path_is_rejected_before_bundle_creation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            patch_path = write(
                temp_dir,
                "unsafe.patch",
                "diff --git a/../../outside.py b/../../outside.py\n"
                "--- a/../../outside.py\n"
                "+++ b/../../outside.py\n"
                "@@ -1 +1 @@\n"
                "-value = 1\n"
                "+value = 2\n",
            )
            tree_root = Path(temp_dir) / "tree"
            write(tree_root, "src/example.py", "value = 2\n")
            bundle = Path(temp_dir) / "bundle"
            completed = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                patch_path,
                "--tree-root",
                tree_root,
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        self.assertEqual("path_unsafe", result_json(completed)["errors"][0]["code"])
        self.assertFalse(bundle.exists())

    def test_required_inputs_fail_before_bundle_creation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            completed = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                SKILL_ROOT / "references" / "acceptance-tree",
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        result = result_json(completed)
        self.assertEqual("manifest_input_missing", result["errors"][0]["code"])
        self.assertIn("requirements", result["errors"][0]["message"])
        self.assertIn("standards", result["errors"][0]["message"])
        self.assertFalse(bundle.exists())

    def test_freeze_requires_a_recorded_check_with_reason(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_bundle = Path(temp_dir) / "missing-checks"
            missing = run_contract(
                "freeze",
                "--output",
                missing_bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                SKILL_ROOT / "references" / "acceptance-tree",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                *contract_args(),
            )

            empty_reason_bundle = Path(temp_dir) / "empty-reason"
            empty_reason = run_contract(
                "freeze",
                "--output",
                empty_reason_bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                SKILL_ROOT / "references" / "acceptance-tree",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--check",
                "repository tests=not_run",
                *contract_args(),
            )

            unknown_result_bundle = Path(temp_dir) / "unknown-result"
            unknown_result = run_contract(
                "freeze",
                "--output",
                unknown_result_bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                SKILL_ROOT / "references" / "acceptance-tree",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--check",
                "repository tests=unknown",
                *contract_args(),
            )

        self.assertNotEqual(0, missing.returncode)
        self.assertIn("checks", result_json(missing)["errors"][0]["message"])
        self.assertFalse(missing_bundle.exists())
        self.assertNotEqual(0, empty_reason.returncode)
        self.assertIn("check_invalid", [error["code"] for error in result_json(empty_reason)["errors"]])
        self.assertFalse(empty_reason_bundle.exists())
        self.assertNotEqual(0, unknown_result.returncode)
        self.assertIn("check_invalid", [error["code"] for error in result_json(unknown_result)["errors"]])
        self.assertFalse(unknown_result_bundle.exists())

    def test_explicit_patch_requires_each_non_deleted_changed_tree_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tree_root = Path(temp_dir) / "tree"
            write(tree_root, "README.md", "Unrelated tree\n")
            bundle = Path(temp_dir) / "bundle"
            completed = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                tree_root,
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        self.assertEqual("tree_incomplete", result_json(completed)["errors"][0]["code"])
        self.assertFalse(bundle.exists())

    def test_quoted_and_renamed_patch_paths_cannot_bypass_exclusions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            quoted_path = "src/café.py"
            write(repo, quoted_path, "value = 1\n")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "add quoted path")
            write(repo, quoted_path, "value = 2\n")
            quoted_patch = Path(temp_dir) / "quoted.patch"
            quoted_patch.write_bytes(
                subprocess.run(
                    ["git", "diff", "--binary", "--no-ext-diff", "HEAD", "--"],
                    cwd=repo,
                    capture_output=True,
                    check=True,
                ).stdout
            )
            quoted_tree = Path(temp_dir) / "quoted-tree"
            write(quoted_tree, quoted_path, "value = 2\n")
            quoted_bundle = Path(temp_dir) / "quoted-bundle"
            quoted = run_contract(
                "freeze",
                "--output",
                quoted_bundle,
                "--patch",
                quoted_patch,
                "--tree-root",
                quoted_tree,
                "--exclude",
                f"{quoted_path}=review exclusion",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertNotEqual(0, quoted.returncode)
            self.assertIn(
                "excluded_path_in_patch",
                [error["code"] for error in result_json(quoted)["errors"]],
            )
            self.assertFalse(quoted_bundle.exists())

            old_path = "src/old name.py"
            new_path = "src/new name.py"
            write(repo, old_path, "value = 3\n")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "add rename source")
            git(repo, "mv", old_path, new_path)
            rename_patch = Path(temp_dir) / "rename.patch"
            rename_patch.write_bytes(
                subprocess.run(
                    ["git", "diff", "--cached", "--binary", "--no-ext-diff", "-M"],
                    cwd=repo,
                    capture_output=True,
                    check=True,
                ).stdout
            )
            rename_tree = Path(temp_dir) / "rename-tree"
            write(rename_tree, new_path, "value = 3\n")
            rename_bundle = Path(temp_dir) / "rename-bundle"
            renamed = run_contract(
                "freeze",
                "--output",
                rename_bundle,
                "--patch",
                rename_patch,
                "--tree-root",
                rename_tree,
                "--exclude",
                f"{old_path}=review exclusion",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

        self.assertNotEqual(0, renamed.returncode)
        self.assertIn(
            "excluded_path_in_patch",
            [error["code"] for error in result_json(renamed)["errors"]],
        )
        self.assertFalse(rename_bundle.exists())

    def test_malformed_patch_is_rejected_without_creating_a_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            patch_path = write(temp_dir, "malformed.patch", "not a git patch\n")
            tree_root = Path(temp_dir) / "tree"
            write(tree_root, "src/example.py", "value = 2\n")
            bundle = Path(temp_dir) / "bundle"
            completed = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                patch_path,
                "--tree-root",
                tree_root,
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        self.assertEqual("patch_parse_failed", result_json(completed)["errors"][0]["code"])
        self.assertFalse(bundle.exists())

    def test_explicit_tree_bundle_cannot_be_written_inside_its_git_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            git(repo, "init")
            git(repo, "config", "user.name", "Review Test")
            git(repo, "config", "user.email", "review@example.com")
            tree_root = repo / "frozen"
            write(tree_root, "src/discounts.py", "value = 2\n")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "frozen tree")
            bundle = repo / "review-bundle"

            completed = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                tree_root,
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        self.assertEqual(
            "output_inside_repository",
            result_json(completed)["errors"][0]["code"],
        )
        self.assertFalse(bundle.exists())

    def test_output_rejects_repo_subdirectory_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            src_dir = repo / "src"
            write(src_dir, "example.py", "value = 2\n")
            outside_tree = Path(temp_dir) / "outside-tree"
            write(outside_tree, "src/discounts.py", "value = 2\n")
            bundle = repo / ".review"

            explicit = run_contract(
                "freeze",
                "--repo",
                src_dir,
                "--output",
                bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                outside_tree,
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertNotEqual(0, explicit.returncode)
            self.assertEqual(
                "output_inside_repository",
                result_json(explicit)["errors"][0]["code"],
            )
            self.assertFalse(bundle.exists())

            uncommitted_bundle = repo / ".review-uncommitted"
            uncommitted = run_contract(
                "freeze",
                "--repo",
                src_dir,
                "--output",
                uncommitted_bundle,
                "--uncommitted",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

        self.assertNotEqual(0, uncommitted.returncode)
        self.assertEqual(
            "output_inside_repository",
            result_json(uncommitted)["errors"][0]["code"],
        )
        self.assertFalse(uncommitted_bundle.exists())


class ParallelCodeReviewEnvelopeTests(unittest.TestCase):
    def test_code_review_envelope_preserves_axes_order_and_normalized_presentation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            envelope = valid_code_review_envelope(attestation, checked_sha)
            envelope_path = write(temp_dir, "envelope.json", json.dumps(envelope))

            completed = run_contract(
                "validate-envelope",
                "--bundle",
                bundle,
                "--envelope",
                envelope_path,
                *contract_args(),
            )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = result_json(completed)
        self.assertEqual("valid", result["status"])
        self.assertEqual(
            ["STD-01", "SPEC-01"],
            [finding["native_id"] for finding in result["findings"]],
        )
        rendered = result["rendered"]
        self.assertLess(rendered.index("## Native report"), rendered.index("## Findings"))
        self.assertLess(rendered.index("### 1. Preview converts"), rendered.index("### 2. Unknown coupon"))
        self.assertIn("Severity: P1 — Binary floating point", rendered)
        self.assertIn("What this is:", rendered)
        self.assertIn("Problem:", rendered)
        self.assertIn("Fix:", rendered)
        self.assertIn("If we skip it:", rendered)
        self.assertIn("Native severity: high", rendered)
        self.assertIn("`src/discounts.py:9`", rendered)

    def test_envelope_validation_rejects_schema_attestation_and_track_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            baseline = valid_code_review_envelope(attestation, checked_sha)
            cases = {}

            bad = copy.deepcopy(baseline)
            bad["findings"][0]["severity"] = "P3"
            cases["invalid severity"] = (bad, "envelope_invalid")

            bad = copy.deepcopy(baseline)
            del bad["findings"][0]["fix"]
            cases["missing common field"] = (bad, "envelope_invalid")

            bad = copy.deepcopy(baseline)
            bad["findings"][0]["citations"] = []
            cases["missing citation"] = (bad, "envelope_invalid")

            bad = copy.deepcopy(baseline)
            bad["findings"][0]["citations"][0]["quote"] = "invented source text"
            cases["citation mismatch"] = (bad, "citation_mismatch")

            bad = copy.deepcopy(baseline)
            bad["attestation"]["patch_sha256"] = "0" * 64
            cases["attestation mismatch"] = (bad, "attestation_mismatch")

            bad = copy.deepcopy(baseline)
            bad["track_id"] = "not-routed"
            cases["unrouted track"] = (bad, "track_not_routed")

            bad = copy.deepcopy(baseline)
            bad["extra"] = True
            cases["unknown field"] = (bad, "envelope_unknown_field")

            bad = copy.deepcopy(baseline)
            bad["contract_version"] = 2
            cases["version mismatch"] = (bad, "envelope_version_mismatch")

            for label, (payload, expected_code) in cases.items():
                with self.subTest(label):
                    envelope_path = write(temp_dir, f"{label.replace(' ', '-')}.json", json.dumps(payload))
                    completed = run_contract(
                        "validate-envelope",
                        "--bundle",
                        bundle,
                        "--envelope",
                        envelope_path,
                        *contract_args(),
                    )
                    self.assertNotEqual(0, completed.returncode)
                    result = result_json(completed)
                    self.assertEqual("blocked", result["status"])
                    self.assertIn(expected_code, [error["code"] for error in result["errors"]])

    def test_envelope_rejects_unfrozen_coverage_locations_and_invalid_types(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            baseline = valid_code_review_envelope(attestation, checked_sha)

            valid_path = write(temp_dir, "valid.json", json.dumps(baseline))
            valid = run_contract(
                "validate-envelope",
                "--bundle",
                bundle,
                "--envelope",
                valid_path,
                *contract_args(),
            )
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)
            rendered = result_json(valid)["rendered"]
            self.assertIn("Launch status: `launched`", rendered)
            self.assertIn("## Unchecked", rendered)
            self.assertIn("## Checks", rendered)

            cases = {}
            bad = copy.deepcopy(baseline)
            bad["coverage"]["checked"] = []
            cases["empty checked"] = (bad, "envelope_invalid")

            bad = copy.deepcopy(baseline)
            bad["coverage"]["checked"][0]["sha256"] = "0" * 64
            cases["wrong checked hash"] = (bad, "coverage_hash_mismatch")

            bad = copy.deepcopy(baseline)
            bad["findings"][0]["location"]["path"] = "src/missing.py"
            cases["missing location"] = (bad, "location_source_missing")

            bad = copy.deepcopy(baseline)
            bad["findings"][0]["location"]["line"] = 999
            cases["location out of bounds"] = (bad, "location_mismatch")

            bad = copy.deepcopy(baseline)
            bad["findings"][0]["severity"] = []
            cases["severity type"] = (bad, "envelope_invalid")

            bad = copy.deepcopy(baseline)
            bad["coverage"]["status"] = []
            cases["coverage status type"] = (bad, "envelope_invalid")

            bad = copy.deepcopy(baseline)
            bad["coverage"]["checks"][0]["result"] = []
            cases["check result type"] = (bad, "envelope_invalid")

            bad = copy.deepcopy(baseline)
            bad["coverage"]["checks"][0]["reason"] = ""
            cases["not run reason"] = (bad, "envelope_invalid")

            for label, (payload, expected_code) in cases.items():
                with self.subTest(label):
                    envelope_path = write(
                        temp_dir,
                        f"invalid-{label.replace(' ', '-')}.json",
                        json.dumps(payload),
                    )
                    completed = run_contract(
                        "validate-envelope",
                        "--bundle",
                        bundle,
                        "--envelope",
                        envelope_path,
                        *contract_args(),
                    )
                    self.assertNotEqual(0, completed.returncode)
                    self.assertEqual("blocked", result_json(completed)["status"])
                    self.assertIn(
                        expected_code,
                        [error["code"] for error in result_json(completed)["errors"]],
                    )

    def test_envelope_preserves_received_finding_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            envelope = valid_code_review_envelope(attestation, checked_sha)
            envelope["findings"].reverse()
            envelope_path = write(temp_dir, "reversed.json", json.dumps(envelope))
            completed = run_contract(
                "validate-envelope",
                "--bundle",
                bundle,
                "--envelope",
                envelope_path,
                *contract_args(),
            )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = result_json(completed)
        self.assertEqual(
            ["SPEC-01", "STD-01"],
            [finding["native_id"] for finding in result["findings"]],
        )
        self.assertLess(
            result["rendered"].index("### 1. Unknown coupon"),
            result["rendered"].index("### 2. Preview converts"),
        )


class ParallelCodeReviewPackageTests(unittest.TestCase):
    def test_model_facing_description_has_narrow_parallel_triggers_and_explicit_invocation(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1].lower()
        description = frontmatter.split("description:", 1)[1].lower()

        for concept in (
            "parallel",
            "combined review tracks",
            "independent reviewers",
            "one frozen scope",
            "/spec-implement-loop",
            "final review",
            "/parallel-code-review",
            "generic single-path review",
        ):
            self.assertIn(concept, description)
        self.assertNotIn("disable-model-invocation", frontmatter)

        policy = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: true", policy)

    def test_skill_keeps_dispatch_frozen_scope_envelope_and_read_only_boundaries(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").lower().replace("`", "")
        self.assertIn("references/routing-table.md", text)
        self.assertIn("row order", text)
        self.assertIn("before dispatch", text)
        self.assertIn("missing, duplicate, unreadable, malformed, version-mismatched, or orphan", text)
        self.assertIn("git range", text)
        self.assertIn("explicit patch", text)
        self.assertIn("uncommitted", text)
        self.assertIn("manifest digest", text)
        self.assertIn("included sources", text)
        self.assertIn("checks", text)
        self.assertIn("exclusions", text)
        self.assertIn("stale", text)
        self.assertIn("its own independent sub-agent", text)
        self.assertIn("read the original upstream /code-review skill", text)
        self.assertIn("standards and spec", text)
        self.assertIn("original order", text)
        self.assertIn("validate but do not reclassify or reorder", text)
        self.assertIn("not run", text)
        self.assertIn("do not write to the reviewed repository", text)
        self.assertIn("--upstream", text)
        self.assertIn("contract-root", text)
        self.assertIn("hash-mismatched", text)
        self.assertIn("synthetic envelope", text)
        self.assertIn("not evidence", text)

    def test_acceptance_package_is_review_only_and_renders_the_expected_code_review_result(self):
        patch = SKILL_ROOT / "references" / "acceptance-fixture.patch"
        scenario = (SKILL_ROOT / "references" / "acceptance-scenario.md").read_text(encoding="utf-8").lower()
        self.assertIn("do not apply", scenario)
        self.assertIn("not run", scenario)
        self.assertIn("model discovery", scenario)
        self.assertIn("explicit invocation", scenario)
        self.assertIn("single `/code-review` track", scenario)
        self.assertIn("no repository writes", scenario)
        self.assertIn("static envelope", scenario)
        self.assertIn("must not be reported as a live", scenario)

        before = snapshot_tree(ROOT)
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            envelope = valid_code_review_envelope(attestation, checked_sha)
            envelope_path = write(temp_dir, "envelope.json", json.dumps(envelope))
            validated = run_contract(
                "validate-envelope",
                "--bundle",
                bundle,
                "--envelope",
                envelope_path,
                *contract_args(),
            )
            self.assertEqual(validated.returncode, 0, validated.stderr or validated.stdout)

        self.assertEqual(before, snapshot_tree(ROOT))
        self.assertFalse((ROOT / "src" / "discounts.py").exists())
        self.assertIn(b"src/discounts.py", patch.read_bytes())

    def test_readme_lists_the_new_skill(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "[parallel-code-review](skills/parallel-code-review/SKILL.md)",
            readme,
        )
        self.assertIn(
            "skills/parallel-code-review/references/acceptance-fixture.patch -text",
            (ROOT / ".gitattributes").read_text(encoding="utf-8"),
        )

    def test_contract_pin_change_makes_a_frozen_bundle_stale(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_copy = Path(temp_dir) / "skill"
            shutil.copytree(SKILL_ROOT, skill_copy)
            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                skill_copy / "references" / "acceptance-fixture.patch",
                "--tree-root",
                skill_copy / "references" / "acceptance-tree",
                "--requirements",
                skill_copy / "references" / "acceptance-requirements.md",
                "--standards",
                skill_copy / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(skill_copy),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            current = run_contract(
                "verify",
                "--bundle",
                bundle,
                *contract_args(skill_copy),
            )
            self.assertEqual(current.returncode, 0, current.stderr or current.stdout)
            self.assertEqual("current", result_json(current)["status"])

            adapter = skill_copy / "references" / "tracks" / "code-review.md"
            adapter.write_text(
                adapter.read_text(encoding="utf-8") + "\nChanged.\n",
                encoding="utf-8",
            )
            verified = run_contract(
                "verify",
                "--bundle",
                bundle,
                *contract_args(skill_copy),
            )

        self.assertNotEqual(0, verified.returncode)
        self.assertEqual("stale", result_json(verified)["status"])

    def test_routing_adapter_and_upstream_pins_detect_line_ending_changes(self):
        cases = {
            "routing": "references/routing-table.md",
            "adapter": "references/tracks/code-review.md",
            "upstream": None,
        }
        for label, relative_path in cases.items():
            with self.subTest(label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    skill_copy = Path(temp_dir) / "skill"
                    shutil.copytree(SKILL_ROOT, skill_copy)
                    upstream_copy = Path(temp_dir) / "upstream-SKILL.md"
                    shutil.copyfile(UPSTREAM_SOURCE, upstream_copy)
                    bundle = Path(temp_dir) / "bundle"
                    frozen = run_contract(
                        "freeze",
                        "--output",
                        bundle,
                        "--patch",
                        skill_copy / "references" / "acceptance-fixture.patch",
                        "--tree-root",
                        skill_copy / "references" / "acceptance-tree",
                        "--requirements",
                        skill_copy / "references" / "acceptance-requirements.md",
                        "--standards",
                        skill_copy / "references" / "acceptance-standard.md",
                        "--not-run",
                        "repository tests=Synthetic patch is review-only.",
                        *contract_args(skill_copy, upstream_copy),
                    )
                    self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
                    target = upstream_copy if relative_path is None else skill_copy / relative_path
                    self.assertTrue(
                        toggle_line_endings(target),
                        f"{label} fixture should change line-ending bytes.",
                    )
                    verified = run_contract(
                        "verify",
                        "--bundle",
                        bundle,
                        *contract_args(skill_copy, upstream_copy),
                    )

                self.assertNotEqual(0, verified.returncode)
                self.assertEqual("stale", result_json(verified)["status"])

    def test_verify_and_envelope_validation_require_the_frozen_upstream_pin(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_copy = Path(temp_dir) / "skill"
            shutil.copytree(SKILL_ROOT, skill_copy)
            upstream_copy = Path(temp_dir) / "upstream-SKILL.md"
            shutil.copyfile(UPSTREAM_SOURCE, upstream_copy)
            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                skill_copy / "references" / "acceptance-fixture.patch",
                "--tree-root",
                skill_copy / "references" / "acceptance-tree",
                "--requirements",
                skill_copy / "references" / "acceptance-requirements.md",
                "--standards",
                skill_copy / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(skill_copy, upstream_copy),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            upstream_copy.write_bytes(upstream_copy.read_bytes() + b"\n")
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            envelope = valid_code_review_envelope(attestation, checked_sha)
            envelope_path = write(temp_dir, "envelope.json", json.dumps(envelope))

            verify = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--contract-root",
                skill_copy,
            )
            validate = run_contract(
                "validate-envelope",
                "--bundle",
                bundle,
                "--envelope",
                envelope_path,
                "--contract-root",
                skill_copy,
            )

        self.assertNotEqual(0, verify.returncode)
        self.assertEqual("blocked", result_json(verify)["status"])
        self.assertIn("upstream_unresolved", [error["code"] for error in result_json(verify)["errors"]])
        self.assertNotEqual(0, validate.returncode)
        self.assertEqual("blocked", result_json(validate)["status"])
        self.assertIn("upstream_unresolved", [error["code"] for error in result_json(validate)["errors"]])

    def test_bundle_rejects_nonobject_json_and_boolean_versions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest_path = bundle / "manifest.json"
            attestation_path = bundle / "attestation.json"
            original_manifest = manifest_path.read_bytes()
            original_attestation = attestation_path.read_bytes()

            for payload in ("[]", '{"contract_version":true}'):
                with self.subTest(payload=payload):
                    manifest_path.write_text(payload, encoding="utf-8")
                    verified = run_contract("verify", "--bundle", bundle, *contract_args())
                    self.assertNotEqual(0, verified.returncode)
                    self.assertEqual("blocked", result_json(verified)["status"])

            manifest_path.write_bytes(original_manifest)
            manifest = json.loads(original_manifest)
            manifest["scope"] = []
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                encoding="utf-8",
            )
            verified = run_contract("verify", "--bundle", bundle, *contract_args())
            self.assertNotEqual(0, verified.returncode)
            self.assertEqual("blocked", result_json(verified)["status"])

            manifest_path.write_bytes(original_manifest)
            attestation_path.write_text("[]", encoding="utf-8")
            verified = run_contract("verify", "--bundle", bundle, *contract_args())

            self.assertNotEqual(0, verified.returncode)
            self.assertEqual("blocked", result_json(verified)["status"])
            manifest_path.write_bytes(original_manifest)
            attestation_path.write_bytes(original_attestation)

    def test_verify_requires_contract_pins_and_detects_input_byte_drift(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            missing_pins = run_contract("verify", "--bundle", bundle)
            self.assertNotEqual(0, missing_pins.returncode)
            self.assertEqual("blocked", result_json(missing_pins)["status"])
            self.assertIn(
                "contract_root_required",
                [error["code"] for error in result_json(missing_pins)["errors"]],
            )

            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            input_entry = manifest["inputs"][0]
            input_snapshot = bundle / input_entry["snapshot_path"]
            original = input_snapshot.read_bytes()
            input_snapshot.write_bytes(original.replace(b"\n", b"\r\n"))
            stale = run_contract(
                "verify",
                "--bundle",
                bundle,
                *contract_args(),
            )

        self.assertNotEqual(0, stale.returncode)
        self.assertEqual("stale", result_json(stale)["status"])

    def test_verify_detects_same_length_line_ending_drift(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            requirements = Path(temp_dir) / "requirements.md"
            requirements.write_bytes(b"line\n")
            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                SKILL_ROOT / "references" / "acceptance-tree",
                "--requirements",
                requirements,
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            entry = next(item for item in manifest["inputs"] if item["role"] == "requirements")
            snapshot = bundle / entry["snapshot_path"]
            self.assertEqual(b"line\n", snapshot.read_bytes())
            snapshot.write_bytes(b"line\r")
            verified = run_contract(
                "verify",
                "--bundle",
                bundle,
                *contract_args(),
            )

        self.assertNotEqual(0, verified.returncode)
        self.assertEqual("stale", result_json(verified)["status"])

    def test_malformed_scope_manifest_returns_structured_blocked_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            git(repo, "init")
            git(repo, "config", "user.name", "Review Test")
            git(repo, "config", "user.email", "review@example.com")
            write(repo, "README.md", "Repo\n")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "initial")
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest_path = bundle / "manifest.json"
            attestation_path = bundle / "attestation.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["scope"]["kind"] = "git_range"
            for field in ("base", "head", "merge_base"):
                manifest["scope"].pop(field, None)
            manifest_bytes = json.dumps(
                manifest,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            manifest_path.write_bytes(manifest_bytes)
            attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
            attestation["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
            attestation_path.write_text(
                json.dumps(attestation, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                encoding="utf-8",
            )
            completed = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--repo",
                repo,
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        self.assertEqual("blocked", result_json(completed)["status"])
        self.assertIn("bundle_invalid", [error["code"] for error in result_json(completed)["errors"]])

    def test_manifest_rejects_empty_required_checks_after_reattestation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            manifest["checks"] = []
            rewrite_manifest_with_attestation(bundle, manifest)
            completed = run_contract(
                "verify",
                "--bundle",
                bundle,
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        result = result_json(completed)
        self.assertEqual("blocked", result["status"])
        self.assertIn("bundle_invalid", [error["code"] for error in result["errors"]])

    def test_manifest_rejects_included_input_status_without_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            manifest["inputs"] = []
            rewrite_manifest_with_attestation(bundle, manifest)
            completed = run_contract(
                "verify",
                "--bundle",
                bundle,
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        result = result_json(completed)
        self.assertEqual("blocked", result["status"])
        self.assertIn("bundle_invalid", [error["code"] for error in result["errors"]])


if __name__ == "__main__":
    unittest.main()
