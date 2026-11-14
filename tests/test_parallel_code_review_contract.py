import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "parallel-code-review"
SCRIPT = SKILL_ROOT / "scripts" / "review_contract.py"
UPSTREAM_SOURCE = SKILL_ROOT / "references" / "tracks" / "code-review.md"
PONYTAIL_UPSTREAM_SOURCE = SKILL_ROOT / "references" / "tracks" / "ponytail-review.md"
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


def load_contract_module():
    spec = importlib.util.spec_from_file_location("review_contract_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def make_repo(temp_dir):
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


def make_directory_link(link, target):
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except (OSError, NotImplementedError) as exc:
        if os.name != "nt":
            raise
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise OSError(
                completed.stderr.strip() or completed.stdout.strip() or str(exc)
            ) from exc


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
        *contract_args(),
    )
    return completed, bundle


def upstream_args(
    skill_root=SKILL_ROOT,
    upstream=UPSTREAM_SOURCE,
    ponytail_upstream=None,
):
    if ponytail_upstream is None:
        ponytail_upstream = skill_root / "references" / "tracks" / "ponytail-review.md"
    return [
        "--upstream",
        f"/code-review={upstream}",
        "--upstream",
        f"/ponytail-review={ponytail_upstream}",
    ]


def contract_args(skill_root=SKILL_ROOT, upstream=UPSTREAM_SOURCE, ponytail_upstream=None):
    return [
        "--contract-root",
        str(skill_root),
        *upstream_args(skill_root, upstream, ponytail_upstream),
    ]


def explicit_patch_args(
    patch_path=SKILL_ROOT / "references" / "acceptance-fixture.patch",
):
    return ["--patch", str(patch_path)]


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


def valid_ponytail_review_envelope(attestation, checked_sha="e" * 64):
    return {
        "contract_version": 1,
        "track_id": "ponytail-review",
        "invocation_id": "ponytail-review-001",
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
                    "path": "runtime behavior",
                    "reason": "The synthetic fixture has no runnable application.",
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
            "what_this_change_does": (
                "The change adds coupon redemption and a tax preview for money values."
            ),
            "groups": [
                {"name": "Must fix", "finding_ids": ["1"]},
                {"name": "Should fix", "finding_ids": ["2", "3"]},
            ],
            "verdict": "Verdict: fix 1 first.",
            "lean": "Lean: -0 lines possible.",
            "not_checked": [
                "Runtime behavior: the synthetic fixture has no runnable application."
            ],
        },
        "findings": [
            {
                "native_id": "1",
                "native_severity": "Must fix",
                "native_group": "Must fix",
                "severity": "P1",
                "severity_rationale": (
                    "Binary floating point can produce an incorrect monetary preview."
                ),
                "title": "Money is converted through binary float",
                "location": {"path": "src/discounts.py", "line": 9},
                "what_this_is": (
                    "The tax preview converts Decimal money to a float and back to Decimal."
                ),
                "problem": "The float step can change the displayed amount.",
                "fix": "Keep Decimal arithmetic through the preview.",
                "if_we_skip_it": "The preview can show the wrong price.",
                "citations": [
                    {
                        "path": "src/discounts.py",
                        "line": 9,
                        "quote": "    return Decimal(str(float(amount) * 1.08))",
                    }
                ],
            },
            {
                "native_id": "2",
                "native_severity": "Should fix",
                "native_group": "Should fix",
                "severity": "P1",
                "severity_rationale": (
                    "The frozen requirement says an unknown coupon must raise an explicit error."
                ),
                "title": "Unknown coupons are silently accepted",
                "location": {"path": "src/discounts.py", "line": 6},
                "what_this_is": "Every coupon other than SAVE10 returns the amount unchanged.",
                "problem": "Callers cannot tell that an unknown coupon was not applied.",
                "fix": "Raise an explicit invalid-coupon error for every other code.",
                "if_we_skip_it": "A required rejection path remains missing.",
                "citations": [
                    {
                        "path": "src/discounts.py",
                        "line": 6,
                        "quote": "    return amount",
                    }
                ],
            },
            {
                "native_id": "3",
                "native_severity": "Should fix",
                "native_group": "Should fix",
                "severity": "P2",
                "severity_rationale": (
                    "No current runtime impact is shown, but risky money logic has no regression test."
                ),
                "title": "Money paths have no regression test",
                "location": {"path": "src/discounts.py", "line": 3},
                "what_this_is": "Coupon and tax-preview behavior is added without a test.",
                "problem": "A later change can break money handling without a failing test.",
                "fix": "Add one focused test for coupon rejection and one for Decimal preview math.",
                "if_we_skip_it": "The risky paths can regress silently.",
                "citations": [
                    {
                        "path": "src/discounts.py",
                        "line": 3,
                        "quote": "def redeem(code: str, amount: Decimal) -> Decimal:",
                    }
                ],
            },
        ],
    }


def valid_third_review_envelope(attestation, checked_sha="e" * 64):
    envelope = valid_ponytail_review_envelope(attestation, checked_sha)
    envelope["track_id"] = "third-review"
    envelope["invocation_id"] = "third-review-001"
    envelope["native"] = {
        "title": "/third-review",
        "sections": [
            {
                "name": "Third-track findings",
                "finding_ids": ["1", "2", "3"],
            }
        ],
    }
    return envelope


def run_attempt(
    invocation_id,
    request_sha256,
    *,
    envelope=None,
    failure=None,
    launch_status="launched",
    recovery=None,
):
    attempt = {
        "invocation_id": invocation_id,
        "status": "completed" if envelope is not None else "failed",
        "launch_status": launch_status,
        "request_sha256": request_sha256,
    }
    if envelope is not None:
        attempt["envelope"] = envelope
    else:
        attempt["failure"] = failure
    if recovery is not None:
        attempt["recovery"] = recovery
    return attempt


def review_run(code_attempts, ponytail_attempts, partial=None, checks=None):
    if checks is None:
        checks = [
            {
                "name": "independence_capability",
                "result": "not_run",
                "reason": "Synthetic records do not demonstrate live independence.",
            }
        ]
    return {
        "contract_version": 1,
        "tracks": [
            {"track_id": "code-review", "attempts": code_attempts},
            {"track_id": "ponytail-review", "attempts": ponytail_attempts},
        ],
        "checks": checks,
        "partial": partial,
    }


def write_current_acceptance_run(temp_dir, bundle, name="run.json"):
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    checked_source = next(
        (
            source
            for source in manifest["scope"]["tree_sources"]
            if source["path"] == "src/discounts.py"
        ),
        manifest["scope"]["tree_sources"][0],
    )
    checked_sha = checked_source["sha256"]
    attestation = json.loads(
        (bundle / "attestation.json").read_text(encoding="utf-8")
    )
    envelopes = [
        valid_code_review_envelope(attestation, checked_sha),
        valid_ponytail_review_envelope(attestation, checked_sha),
    ]
    attempts = []
    for track_id, envelope in zip(
        ("code-review", "ponytail-review"),
        envelopes,
    ):
        envelope_path = write(
            temp_dir,
            f"{Path(name).stem}-{track_id}.json",
            json.dumps(envelope),
        )
        attempts.append(
            run_attempt(
                envelope["invocation_id"],
                track_request_sha256(manifest, attestation, track_id),
                envelope=envelope_path.name,
            )
        )
    run = review_run(
        [attempts[0]],
        [attempts[1]],
        checks=[
            {
                "name": "independence_capability",
                "result": "passed",
                "reason": "Synthetic fixture records independence as passed.",
            }
        ],
    )
    return write(temp_dir, name, json.dumps(run)), envelopes


def track_request_sha256(manifest, attestation, track_id):
    payload = {
        "track_id": track_id,
        "manifest": manifest,
        "attestation": attestation,
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


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
    def test_shipped_routing_table_activates_code_review_then_ponytail_review(self):
        completed = run_contract(
            "preflight",
            "--skill-root",
            SKILL_ROOT,
            *upstream_args(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = result_json(completed)
        self.assertEqual("ready", result["status"])
        self.assertEqual(
            ["code-review", "ponytail-review"],
            [track["track_id"] for track in result["tracks"]],
        )
        self.assertEqual(
            ["patch", "tree", "requirements", "standards", "checks", "exclusions"],
            result["tracks"][0]["required_inputs"],
        )
        self.assertEqual(
            ["/code-review", "/ponytail-review"],
            [dependency["name"] for dependency in result["dependencies"]],
        )
        self.assertEqual(
            [
                "https://github.com/mattpocock/skills",
                "https://github.com/DietrichGebert/ponytail",
            ],
            [dependency["source"] for dependency in result["dependencies"]],
        )
        self.assertEqual(
            ["local_file", "local_file"],
            [dependency["kind"] for dependency in result["dependencies"]],
        )

    def test_two_track_row_order_controls_dispatch_and_pins_in_both_directions(self):
        orders = {
            "forward": [
                ("code-review", "references/tracks/code-review.md"),
                ("ponytail-review", "references/tracks/ponytail-review.md"),
            ],
            "reverse": [
                ("ponytail-review", "references/tracks/ponytail-review.md"),
                ("code-review", "references/tracks/code-review.md"),
            ],
        }
        for label, rows in orders.items():
            with self.subTest(label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    skill_root = Path(temp_dir) / "skill"
                    shutil.copytree(SKILL_ROOT, skill_root)
                    write_routing(skill_root, rows)
                    completed = run_contract(
                        "preflight",
                        "--skill-root",
                        skill_root,
                        *upstream_args(skill_root),
                    )

                self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                result = result_json(completed)
                expected = [track_id for track_id, _ in rows]
                self.assertEqual(expected, [track["track_id"] for track in result["tracks"]])
                self.assertEqual(
                    expected,
                    [pin["track_id"] for pin in result["pins"]["adapters"]],
                )

    def test_ponytail_metadata_failures_block_before_dispatch(self):
        cases = {
            "missing": (
                "# Adapter without metadata\n",
                "metadata_missing",
            ),
            "duplicate": (
                f"{METADATA_MARKER}\n\n```json\n"
                f"{json.dumps(metadata('/ponytail-review', source='https://github.com/DietrichGebert/ponytail'))}\n"
                f"```\n\n{METADATA_MARKER}\n\n```json\n"
                f"{json.dumps(metadata('/ponytail-review', source='https://github.com/DietrichGebert/ponytail'))}\n"
                f"```\n",
                "metadata_duplicate",
            ),
            "malformed": (
                f"{METADATA_MARKER}\n\n```json\n{{not json\n```\n",
                "metadata_malformed",
            ),
            "version mismatch": (
                f"{METADATA_MARKER}\n\n```json\n"
                f"{json.dumps(metadata('/ponytail-review', source='https://github.com/DietrichGebert/ponytail', version=2))}\n"
                f"```\n",
                "metadata_version_mismatch",
            ),
        }
        for label, (adapter_text, expected_code) in cases.items():
            with self.subTest(label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    skill_root = Path(temp_dir) / "skill"
                    shutil.copytree(SKILL_ROOT, skill_root)
                    (skill_root / "references" / "tracks" / "ponytail-review.md").write_text(
                        adapter_text,
                        encoding="utf-8",
                    )
                    completed = run_contract(
                        "preflight",
                        "--skill-root",
                        skill_root,
                        *upstream_args(skill_root),
                    )

                self.assertNotEqual(0, completed.returncode)
                result = result_json(completed)
                self.assertEqual("blocked", result["status"])
                self.assertIn(expected_code, [error["code"] for error in result["errors"]])
                self.assertNotIn("pins", result)

    def test_preflight_aggregates_adapter_and_upstream_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / "skill"
            shutil.copytree(SKILL_ROOT, skill_root)
            broken_adapter = (
                skill_root / "references" / "tracks" / "ponytail-review.md"
            )
            broken_adapter.write_text(
                "# Adapter without metadata\n",
                encoding="utf-8",
            )
            missing_upstream = Path(temp_dir) / "missing-upstream.md"
            completed = run_contract(
                "preflight",
                "--skill-root",
                skill_root,
                "--upstream",
                f"/code-review={missing_upstream}",
                "--upstream",
                f"/ponytail-review={broken_adapter}",
            )

        self.assertNotEqual(0, completed.returncode)
        result = result_json(completed)
        self.assertEqual("blocked", result["status"])
        self.assertEqual(
            ["metadata_missing", "upstream_unreadable"],
            [error["code"] for error in result["errors"]],
        )
        self.assertIn("ponytail-review.md", result["errors"][0]["message"])
        self.assertIn("/code-review", result["errors"][1]["message"])
        self.assertNotIn("pins", result)

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
            "--upstream",
            f"/ponytail-review={PONYTAIL_UPSTREAM_SOURCE}",
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
        return make_repo(temp_dir)

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
                ["code-review", "ponytail-review"],
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

    def test_freeze_and_current_verify_emit_canonical_scope_digest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            frozen_result = result_json(frozen)
            manifest = json.loads(
                (bundle / "manifest.json").read_text(encoding="utf-8")
            )
            expected = hashlib.sha256(
                json.dumps(
                    manifest["scope"],
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest()

            verified = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                *contract_args(),
            )

        self.assertRegex(frozen_result["scope_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(expected, frozen_result["scope_sha256"])
        self.assertEqual(verified.returncode, 0, verified.stderr or verified.stdout)
        self.assertEqual(
            frozen_result["scope_sha256"],
            result_json(verified)["scope_sha256"],
        )

    def test_scope_digest_changes_when_frozen_scope_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, _ = freeze_acceptance_bundle(temp_dir)
            changed_tree = Path(temp_dir) / "changed-tree"
            shutil.copytree(
                SKILL_ROOT / "references" / "acceptance-tree",
                changed_tree,
            )
            write(changed_tree, "tests/test_extra.py", "def test_extra():\n    pass\n")
            changed_bundle = Path(temp_dir) / "changed-bundle"
            changed = run_contract(
                "freeze",
                "--output",
                changed_bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                "--tree-root",
                changed_tree,
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

        self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
        self.assertEqual(changed.returncode, 0, changed.stderr or changed.stdout)
        self.assertNotEqual(
            result_json(frozen)["scope_sha256"],
            result_json(changed)["scope_sha256"],
        )

    def test_git_range_freeze_fails_when_tree_entry_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            base = git(repo, "rev-parse", "HEAD")
            git(
                repo,
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{'1' * 40},missing-submodule",
            )
            git(repo, "commit", "-m", "point at missing submodule")
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
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

            self.assertNotEqual(0, completed.returncode)
            error = result_json(completed)["errors"][0]
            self.assertEqual("git_command_failed", error["code"])
            self.assertIn("missing-submodule", error["message"])
            self.assertFalse((bundle / "manifest.json").exists())
            self.assertFalse((bundle / "attestation.json").exists())
            self.assertEqual(before, snapshot_tree(repo))

    def test_git_range_freeze_rejects_tracked_symlink(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            base = git(repo, "rev-parse", "HEAD")
            write(repo, "src/example.py", "value = 2\n")
            target_blob = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"],
                cwd=repo,
                input="src/example.py",
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            ).stdout.strip()
            git(
                repo,
                "update-index",
                "--add",
                "--cacheinfo",
                f"120000,{target_blob},src/example-link.py",
            )
            git(repo, "add", "src/example.py")
            git(repo, "commit", "-m", "add tracked symlink")
            head = git(repo, "rev-parse", "HEAD")
            bundle = Path(temp_dir) / "bundle"

            completed = run_contract(
                "freeze",
                "--repo",
                repo,
                "--output",
                bundle,
                "--range",
                f"{base}...{head}",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )

            self.assertNotEqual(0, completed.returncode)
            error = result_json(completed)["errors"][0]
            self.assertEqual("tree_symlink_unsupported", error["code"])
            self.assertIn("src/example-link.py", error["message"])
            self.assertFalse(
                (bundle / "tree" / "src" / "example-link.py").is_file()
            )
            self.assertFalse((bundle / "manifest.json").exists())
            self.assertFalse((bundle / "attestation.json").exists())

    def test_git_range_freeze_rejects_copied_tree_path_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            base = git(repo, "rev-parse", "HEAD")
            write(repo, "src/example.py", "value = 2\n")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "change")
            head = git(repo, "rev-parse", "HEAD")
            bundle = Path(temp_dir) / "bundle"
            contract = load_contract_module()
            original_write = contract.write_bundle_file

            def omit_copied_source(bundle_root, relative_path, data):
                if relative_path == "tree/src/example.py":
                    return None
                return original_write(bundle_root, relative_path, data)

            stdout = io.StringIO()
            with mock.patch.object(
                contract,
                "write_bundle_file",
                side_effect=omit_copied_source,
            ), contextlib.redirect_stdout(stdout):
                exit_code = contract.main(
                    [
                        "freeze",
                        "--repo",
                        str(repo),
                        "--output",
                        str(bundle),
                        "--range",
                        f"{base}...{head}",
                        "--requirements",
                        str(SKILL_ROOT / "references" / "acceptance-requirements.md"),
                        "--standards",
                        str(SKILL_ROOT / "references" / "acceptance-standard.md"),
                        "--not-run",
                        "repository tests=Synthetic patch is review-only.",
                        *contract_args(),
                    ]
                )

            error = json.loads(stdout.getvalue())["errors"][0]
            self.assertNotEqual(0, exit_code)
            self.assertEqual("tree_incomplete", error["code"])
            self.assertIn("src/example.py", error["message"])
            self.assertFalse((bundle / "manifest.json").exists())
            self.assertFalse((bundle / "attestation.json").exists())

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

    def test_explicit_patch_requires_tree_to_match_post_image(self):
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
            matching_tree = Path(temp_dir) / "matching-tree"
            write(matching_tree, "src/example.py", "value = 2\n")
            mismatched_tree = Path(temp_dir) / "mismatched-tree"
            write(mismatched_tree, "src/example.py", "value = 3\n")
            matching_bundle = Path(temp_dir) / "matching-bundle"
            mismatched_bundle = Path(temp_dir) / "mismatched-bundle"
            matching_before = snapshot_tree(matching_tree)
            mismatched_before = snapshot_tree(mismatched_tree)
            common_args = [
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            ]

            matching = run_contract(
                "freeze",
                "--output",
                matching_bundle,
                "--patch",
                patch_path,
                "--tree-root",
                matching_tree,
                *common_args,
            )
            mismatched = run_contract(
                "freeze",
                "--output",
                mismatched_bundle,
                "--patch",
                patch_path,
                "--tree-root",
                mismatched_tree,
                *common_args,
            )

            self.assertEqual(matching.returncode, 0, matching.stderr or matching.stdout)
            self.assertTrue(matching_bundle.is_dir())
            self.assertEqual(matching_before, snapshot_tree(matching_tree))
            self.assertNotEqual(0, mismatched.returncode)
            self.assertEqual(
                "tree_mismatch",
                result_json(mismatched)["errors"][0]["code"],
            )
            self.assertFalse(mismatched_bundle.exists())
            self.assertEqual(mismatched_before, snapshot_tree(mismatched_tree))

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

    def test_verify_rechecks_original_manifest_input_source_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            requirements = Path(temp_dir) / "requirements.md"
            requirements.write_bytes(b"Requirement A.\n")
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
            verify_args = [
                "verify",
                "--bundle",
                bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                *contract_args(),
            ]
            current = run_contract(*verify_args)
            self.assertEqual(current.returncode, 0, current.stdout)

            requirements.write_bytes(b"Requirement B.\n")
            changed = run_contract(*verify_args)
            self.assertEqual("stale", result_json(changed)["status"])
            self.assertTrue(
                any(
                    reason.startswith("Original pinned input source changed:")
                    for reason in result_json(changed)["reasons"]
                )
            )

            requirements.write_bytes(b"Requirement A.\n")
            moved = requirements.with_name("requirements.moved.md")
            requirements.rename(moved)
            missing = run_contract(*verify_args)
            self.assertEqual("stale", result_json(missing)["status"])
            self.assertTrue(
                any(
                    "Original pinned input source is missing or unreadable:"
                    in reason
                    for reason in result_json(missing)["reasons"]
                )
            )

            requirements.mkdir()
            unreadable = run_contract(*verify_args)
            self.assertEqual("stale", result_json(unreadable)["status"])
            self.assertTrue(
                any(
                    "Original pinned input source is missing or unreadable:"
                    in reason
                    for reason in result_json(unreadable)["reasons"]
                )
            )

    def test_verify_uncommitted_scope_rechecks_live_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            write(repo, "src/example.py", "value = 2\n")
            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
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
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            current = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--repo",
                repo,
                *contract_args(),
            )
            self.assertEqual(current.returncode, 0, current.stdout)

            write(repo, "src/example.py", "value = 3\n")
            stale = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--repo",
                repo,
                *contract_args(),
            )

        self.assertEqual("stale", result_json(stale)["status"])
        self.assertIn(
            "An uncommitted source changed: src/example.py",
            result_json(stale)["reasons"],
        )

    def test_verify_git_range_rechecks_the_exact_head_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            base = git(repo, "rev-parse", "HEAD")
            write(repo, "src/example.py", "value = 2\n")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "change")
            head = git(repo, "rev-parse", "HEAD")
            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
                "freeze",
                "--repo",
                repo,
                "--output",
                bundle,
                "--range",
                f"{base}...{head}",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            current = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--repo",
                repo,
                *contract_args(),
            )
            self.assertEqual(current.returncode, 0, current.stdout)

            manifest = json.loads(
                (bundle / "manifest.json").read_text(encoding="utf-8")
            )
            source = next(
                item
                for item in manifest["scope"]["tree_sources"]
                if item["path"] == "src/example.py"
            )
            readme = next(
                item
                for item in manifest["scope"]["tree_sources"]
                if item["path"] == "README.md"
            )
            replacement = (bundle / readme["snapshot_path"]).read_bytes()
            (bundle / source["snapshot_path"]).write_bytes(replacement)
            source["sha256"] = hashlib.sha256(replacement).hexdigest()
            source["size_bytes"] = len(replacement)
            rewrite_manifest_with_attestation(bundle, manifest)

            stale = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--repo",
                repo,
                *contract_args(),
            )

        self.assertEqual("stale", result_json(stale)["status"])
        self.assertIn(
            "A Git-range source changed: src/example.py",
            result_json(stale)["reasons"],
        )

    def test_verify_explicit_patch_rechecks_same_size_patch_bytes(self):
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
            frozen = run_contract(
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
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            current = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--patch",
                patch_path,
                *contract_args(),
            )
            self.assertEqual(current.returncode, 0, current.stdout)

            original = patch_path.read_bytes()
            changed = original.replace(b"+value = 2", b"+value = 3")
            self.assertNotEqual(original, changed)
            self.assertEqual(len(original), len(changed))
            patch_path.write_bytes(changed)
            stale = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--patch",
                patch_path,
                *contract_args(),
            )

        self.assertEqual("stale", result_json(stale)["status"])
        self.assertIn(
            "The explicit patch changed after the freeze.",
            result_json(stale)["reasons"],
        )

    def test_verify_requires_scope_appropriate_live_locators(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.make_repo(temp_dir)
            base = git(repo, "rev-parse", "HEAD")
            write(repo, "src/example.py", "value = 2\n")
            uncommitted_bundle = Path(temp_dir) / "uncommitted-bundle"
            uncommitted = run_contract(
                "freeze",
                "--repo",
                repo,
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
            self.assertEqual(uncommitted.returncode, 0, uncommitted.stdout)
            missing_uncommitted = run_contract(
                "verify",
                "--bundle",
                uncommitted_bundle,
                *contract_args(),
            )

            git(repo, "add", ".")
            git(repo, "commit", "-m", "change")
            head = git(repo, "rev-parse", "HEAD")
            range_bundle = Path(temp_dir) / "range-bundle"
            ranged = run_contract(
                "freeze",
                "--repo",
                repo,
                "--output",
                range_bundle,
                "--range",
                f"{base}...{head}",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertEqual(ranged.returncode, 0, ranged.stdout)
            missing_range = run_contract(
                "verify",
                "--bundle",
                range_bundle,
                *contract_args(),
            )

            explicit, explicit_bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(explicit.returncode, 0, explicit.stdout)
            missing_patch = run_contract(
                "verify",
                "--bundle",
                explicit_bundle,
                *contract_args(),
            )

        for completed, code in (
            (missing_uncommitted, "repo_required"),
            (missing_range, "repo_required"),
            (missing_patch, "patch_required"),
        ):
            result = result_json(completed)
            self.assertNotEqual(0, completed.returncode)
            self.assertEqual("blocked", result["status"])
            self.assertIn(code, [error["code"] for error in result["errors"]])

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

    def test_standalone_freeze_records_missing_requirements_as_not_assessed(self):
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
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            verified = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                *contract_args(),
            )
            manifest = (
                json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
                if (bundle / "manifest.json").is_file()
                else None
            )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("frozen", result_json(completed)["status"])
        self.assertEqual(0, verified.returncode, verified.stderr)
        self.assertEqual("current", result_json(verified)["status"])
        self.assertIsNotNone(manifest)
        self.assertEqual("not_assessed", manifest["input_status"]["requirements"])
        self.assertFalse(
            any(entry["role"] == "requirements" for entry in manifest["inputs"])
        )

    def test_final_loop_freeze_requires_pinned_requirements(self):
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
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                "--require-requirements",
                *contract_args(),
            )

        self.assertNotEqual(0, completed.returncode)
        self.assertTrue(completed.stdout, completed.stderr)
        result = result_json(completed)
        self.assertEqual("manifest_input_missing", result["errors"][0]["code"])
        self.assertIn("requirements", result["errors"][0]["message"])
        self.assertFalse(bundle.exists())

    def test_standalone_freeze_requires_standards_and_checks(self):
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
        self.assertIn("standards", result["errors"][0]["message"])
        self.assertIn("checks", result["errors"][0]["message"])
        self.assertNotIn("requirements", result["errors"][0]["message"])
        self.assertFalse(bundle.exists())

    def test_freeze_aggregates_adapter_upstream_and_all_input_file_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / "skill"
            shutil.copytree(SKILL_ROOT, skill_root)
            broken_adapter = (
                skill_root / "references" / "tracks" / "ponytail-review.md"
            )
            broken_adapter.write_text(
                "# Adapter without metadata\n",
                encoding="utf-8",
            )
            missing_upstream = Path(temp_dir) / "missing-upstream.md"
            missing_requirements = Path(temp_dir) / "missing-requirements.md"
            second_missing_requirements = Path(temp_dir) / "missing-requirements-2.md"
            unreadable_standards = Path(temp_dir) / "unreadable-standards.md"
            unreadable_standards.write_bytes(b"\xff")
            bundle = Path(temp_dir) / "bundle"
            completed = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                skill_root / "references" / "acceptance-fixture.patch",
                "--tree-root",
                skill_root / "references" / "acceptance-tree",
                "--requirements",
                missing_requirements,
                "--requirements",
                second_missing_requirements,
                "--standards",
                unreadable_standards,
                "--contract-root",
                skill_root,
                "--upstream",
                f"/code-review={missing_upstream}",
            )
            bundle_created = bundle.exists()

        self.assertNotEqual(0, completed.returncode)
        result = result_json(completed)
        self.assertEqual("blocked", result["status"])
        self.assertEqual(
            [
                "manifest_input_missing",
                "manifest_input_missing",
                "manifest_input_invalid",
                "metadata_missing",
                "upstream_unreadable",
                "manifest_input_missing",
            ],
            [error["code"] for error in result["errors"]],
        )
        self.assertIn("missing-requirements.md", result["errors"][0]["message"])
        self.assertIn("missing-requirements-2.md", result["errors"][1]["message"])
        self.assertIn("unreadable-standards.md", result["errors"][2]["message"])
        self.assertIn("ponytail-review.md", result["errors"][3]["message"])
        self.assertIn("/code-review", result["errors"][4]["message"])
        self.assertEqual(
            "Required manifest inputs were not supplied: checks",
            result["errors"][5]["message"],
        )
        self.assertFalse(bundle_created)

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

    def test_two_track_envelopes_share_attestation_and_preserve_native_structure_and_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            preflight = run_contract(
                "preflight",
                "--skill-root",
                SKILL_ROOT,
                *upstream_args(),
            )
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(preflight.returncode, 0, preflight.stderr or preflight.stdout)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            code_review = valid_code_review_envelope(attestation, checked_sha)
            ponytail_review = valid_ponytail_review_envelope(attestation, checked_sha)

            code_path = write(temp_dir, "code-review.json", json.dumps(code_review))
            ponytail_path = write(temp_dir, "ponytail-review.json", json.dumps(ponytail_review))
            code_result = run_contract(
                "validate-envelope",
                "--bundle",
                bundle,
                "--envelope",
                code_path,
                *contract_args(),
            )
            ponytail_result = run_contract(
                "validate-envelope",
                "--bundle",
                bundle,
                "--envelope",
                ponytail_path,
                *contract_args(),
            )

            reversed_envelope = copy.deepcopy(ponytail_review)
            reversed_envelope["findings"].reverse()
            reversed_path = write(
                temp_dir,
                "ponytail-review-reversed.json",
                json.dumps(reversed_envelope),
            )
            reversed_result = run_contract(
                "validate-envelope",
                "--bundle",
                bundle,
                "--envelope",
                reversed_path,
                *contract_args(),
            )

        for completed in (code_result, ponytail_result, reversed_result):
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

        code = result_json(code_result)
        ponytail = result_json(ponytail_result)
        reversed_track = result_json(reversed_result)
        route_order = [
            track["track_id"] for track in result_json(preflight)["tracks"]
        ]
        results_by_track = {
            "code-review": code,
            "ponytail-review": ponytail,
        }
        self.assertEqual("code-review", code["track_id"])
        self.assertEqual("ponytail-review", ponytail["track_id"])
        self.assertEqual(["code-review", "ponytail-review"], route_order)
        self.assertNotEqual(
            code_review["invocation_id"],
            ponytail_review["invocation_id"],
        )
        self.assertEqual(
            code_review["attestation"],
            ponytail_review["attestation"],
        )
        self.assertEqual(
            code_review["coverage"]["checked"],
            ponytail_review["coverage"]["checked"],
        )
        self.assertEqual(
            checked_sha,
            code_review["coverage"]["checked"][0]["sha256"],
        )
        self.assertEqual(
            ["STD-01", "SPEC-01", "1", "2", "3"],
            [
                finding["native_id"]
                for track_id in route_order
                for finding in results_by_track[track_id]["findings"]
            ],
        )
        self.assertEqual(
            ["3", "2", "1"],
            [finding["native_id"] for finding in reversed_track["findings"]],
        )
        self.assertEqual(
            ["P1", "P1", "P2"],
            [finding["severity"] for finding in ponytail["findings"]],
        )
        self.assertEqual(
            ["Must fix", "Should fix", "Should fix"],
            [finding["native_group"] for finding in ponytail["findings"]],
        )

        rendered = ponytail["rendered"]
        for native_content in (
            "The change adds coupon redemption and a tax preview",
            '"name": "Must fix"',
            '"name": "Should fix"',
            '"verdict": "Verdict: fix 1 first."',
            '"lean": "Lean: -0 lines possible."',
            '"not_checked"',
            "Native group: Must fix",
            "Native severity: Should fix",
        ):
            self.assertIn(native_content, rendered)
        self.assertLess(rendered.index("## Native report"), rendered.index("## Findings"))
        self.assertLess(rendered.index("### 1. Money is converted"), rendered.index("### 2. Unknown coupons"))
        self.assertLess(rendered.index("### 2. Unknown coupons"), rendered.index("### 3. Money paths"))

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


class ParallelCodeReviewRunTests(unittest.TestCase):
    def test_validate_run_rechecks_pinned_input_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            requirements = write(
                temp_dir,
                "requirements-source.md",
                "Requirement A.\n",
            )
            standards = write(
                temp_dir,
                "standards-source.md",
                "Standard A.\n",
            )
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
                standards,
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            run_path, envelopes = write_current_acceptance_run(temp_dir, bundle)
            validate_args = [
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                *contract_args(),
            ]
            current = run_contract(*validate_args)
            self.assertEqual(current.returncode, 0, current.stderr or current.stdout)
            self.assertEqual("complete", result_json(current)["status"])

            requirements.write_text("Requirement B.\n", encoding="utf-8")
            standards.write_text("Standard B.\n", encoding="utf-8")
            changed = run_contract(*validate_args)
            requirements.write_text("Requirement A.\n", encoding="utf-8")
            standards.write_text("Standard A.\n", encoding="utf-8")

            requirements.rename(requirements.with_suffix(".removed"))
            standards.rename(standards.with_suffix(".removed"))
            removed = run_contract(*validate_args)
            requirements.with_suffix(".removed").rename(requirements)
            standards.with_suffix(".removed").rename(standards)

            requirements.rename(requirements.with_suffix(".unreadable"))
            standards.rename(standards.with_suffix(".unreadable"))
            requirements.mkdir()
            standards.mkdir()
            unreadable = run_contract(*validate_args)

        for label, completed, reason in (
            ("changed", changed, "Original pinned input source changed:"),
            ("removed", removed, "Original pinned input source is missing or unreadable:"),
            ("unreadable", unreadable, "Original pinned input source is missing or unreadable:"),
        ):
            with self.subTest(label):
                self.assertEqual(1, completed.returncode)
                result = result_json(completed)
                self.assertEqual("blocked", result["status"])
                self.assertEqual(envelopes, result["completed_reports"])
                self.assertIn(
                    "scope_stale",
                    [error["code"] for error in result["errors"]],
                )
                messages = " ".join(
                    error["message"] for error in result["errors"]
                )
                self.assertIn(reason, messages)
                self.assertIn("requirements-source.md", messages)
                self.assertIn("standards-source.md", messages)
                self.assertIn("## Completed track reports", result["rendered"])

    def test_validate_run_requires_scope_appropriate_live_locators(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            explicit_bundle = Path(temp_dir) / "explicit-bundle"
            explicit = run_contract(
                "freeze",
                "--output",
                explicit_bundle,
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
                *contract_args(),
            )
            self.assertEqual(explicit.returncode, 0, explicit.stderr or explicit.stdout)
            missing_explicit = run_contract(
                "validate-run",
                "--bundle",
                explicit_bundle,
                "--run",
                Path(temp_dir) / "missing-explicit-run.json",
                *contract_args(),
            )
            wrong_explicit_locator = run_contract(
                "validate-run",
                "--bundle",
                explicit_bundle,
                "--run",
                Path(temp_dir) / "missing-explicit-run.json",
                "--repo",
                temp_dir,
                *contract_args(),
            )

            repo = make_repo(temp_dir)
            write(repo, "src/example.py", "value = 2\n")
            uncommitted_bundle = Path(temp_dir) / "uncommitted-bundle"
            uncommitted = run_contract(
                "freeze",
                "--repo",
                repo,
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
            self.assertEqual(
                uncommitted.returncode,
                0,
                uncommitted.stderr or uncommitted.stdout,
            )
            missing_uncommitted = run_contract(
                "validate-run",
                "--bundle",
                uncommitted_bundle,
                "--run",
                Path(temp_dir) / "missing-uncommitted-run.json",
                *contract_args(),
            )
            wrong_uncommitted_locator = run_contract(
                "validate-run",
                "--bundle",
                uncommitted_bundle,
                "--run",
                Path(temp_dir) / "missing-uncommitted-run.json",
                *explicit_patch_args(),
                *contract_args(),
            )

            base = git(repo, "rev-parse", "HEAD")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "change")
            head = git(repo, "rev-parse", "HEAD")
            range_bundle = Path(temp_dir) / "range-bundle"
            ranged = run_contract(
                "freeze",
                "--repo",
                repo,
                "--output",
                range_bundle,
                "--range",
                f"{base}...{head}",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertEqual(ranged.returncode, 0, ranged.stderr or ranged.stdout)
            missing_range = run_contract(
                "validate-run",
                "--bundle",
                range_bundle,
                "--run",
                Path(temp_dir) / "missing-range-run.json",
                *contract_args(),
            )
            wrong_range_locator = run_contract(
                "validate-run",
                "--bundle",
                range_bundle,
                "--run",
                Path(temp_dir) / "missing-range-run.json",
                *explicit_patch_args(),
                *contract_args(),
            )

        for label, completed, code in (
            ("explicit omitted", missing_explicit, "patch_required"),
            ("explicit wrong", wrong_explicit_locator, "patch_required"),
            ("uncommitted omitted", missing_uncommitted, "repo_required"),
            ("uncommitted wrong", wrong_uncommitted_locator, "repo_required"),
            ("range omitted", missing_range, "repo_required"),
            ("range wrong", wrong_range_locator, "repo_required"),
        ):
            with self.subTest(label=label, code=code):
                result = result_json(completed)
                self.assertEqual(1, completed.returncode)
                self.assertEqual("blocked", result["status"])
                self.assertIn(
                    code,
                    [error["code"] for error in result["errors"]],
                )
                self.assertNotIn(
                    "run_missing",
                    [error["code"] for error in result["errors"]],
                )

    def test_validate_run_rechecks_live_uncommitted_scope(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = make_repo(temp_dir)
            write(
                repo,
                "src/discounts.py",
                (
                    SKILL_ROOT
                    / "references"
                    / "acceptance-tree"
                    / "src"
                    / "discounts.py"
                ).read_text(encoding="utf-8"),
            )
            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
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
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            run_path, envelopes = write_current_acceptance_run(temp_dir, bundle)
            validate_args = [
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                "--repo",
                repo,
                *contract_args(),
            ]
            current = run_contract(*validate_args)
            self.assertEqual(current.returncode, 0, current.stderr or current.stdout)
            self.assertEqual("complete", result_json(current)["status"])

            write(repo, "src/example.py", "value = 3\n")
            stale = run_contract(*validate_args)

        self.assertEqual(1, stale.returncode)
        result = result_json(stale)
        self.assertEqual("blocked", result["status"])
        self.assertEqual(envelopes, result["completed_reports"])
        messages = " ".join(error["message"] for error in result["errors"])
        self.assertIn("An uncommitted source changed: src/example.py", messages)

    def test_validate_run_preserves_history_when_live_patch_touches_exclusion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = make_repo(temp_dir)
            write(repo, "vendor/generated.py", "generated = 1\n")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "add excluded source")
            write(
                repo,
                "src/discounts.py",
                (
                    SKILL_ROOT
                    / "references"
                    / "acceptance-tree"
                    / "src"
                    / "discounts.py"
                ).read_text(encoding="utf-8"),
            )
            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
                "freeze",
                "--repo",
                repo,
                "--output",
                bundle,
                "--uncommitted",
                "--exclude",
                "vendor/=third-party source",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            run_path, envelopes = write_current_acceptance_run(temp_dir, bundle)
            validate_args = [
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                "--repo",
                repo,
                *contract_args(),
            ]
            current = run_contract(*validate_args)
            self.assertEqual(current.returncode, 0, current.stderr or current.stdout)
            self.assertEqual("complete", result_json(current)["status"])

            write(repo, "vendor/generated.py", "generated = 2\n")
            stale = run_contract(*validate_args)

        self.assertEqual(1, stale.returncode)
        result = result_json(stale)
        self.assertEqual("blocked", result["status"])
        self.assertEqual(envelopes, result["completed_reports"])
        self.assertIn(
            "scope_stale",
            [error["code"] for error in result["errors"]],
        )
        messages = " ".join(error["message"] for error in result["errors"])
        self.assertIn("excluded_path_in_patch", messages)
        self.assertIn("vendor/generated.py", messages)
        self.assertIn("## Completed track reports", result["rendered"])
        self.assertIn("Preview converts Decimal money to float", result["rendered"])

    def test_validate_run_rechecks_live_git_range_head_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = make_repo(temp_dir)
            base = git(repo, "rev-parse", "HEAD")
            write(
                repo,
                "src/discounts.py",
                (
                    SKILL_ROOT
                    / "references"
                    / "acceptance-tree"
                    / "src"
                    / "discounts.py"
                ).read_text(encoding="utf-8"),
            )
            git(repo, "add", ".")
            git(repo, "commit", "-m", "change")
            head = git(repo, "rev-parse", "HEAD")
            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
                "freeze",
                "--repo",
                repo,
                "--output",
                bundle,
                "--range",
                f"{base}...{head}",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            run_path, _ = write_current_acceptance_run(temp_dir, bundle)
            validate_args = [
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                "--repo",
                repo,
                *contract_args(),
            ]
            current = run_contract(*validate_args)
            self.assertEqual(current.returncode, 0, current.stderr or current.stdout)
            self.assertEqual("complete", result_json(current)["status"])

            manifest = json.loads(
                (bundle / "manifest.json").read_text(encoding="utf-8")
            )
            source = next(
                item
                for item in manifest["scope"]["tree_sources"]
                if item["path"] == "src/discounts.py"
            )
            replacement = (
                (bundle / source["snapshot_path"]).read_bytes() + b"\n"
            )
            (bundle / source["snapshot_path"]).write_bytes(replacement)
            source["sha256"] = hashlib.sha256(replacement).hexdigest()
            source["size_bytes"] = len(replacement)
            rewrite_manifest_with_attestation(bundle, manifest)
            drift_run, drift_envelopes = write_current_acceptance_run(
                temp_dir,
                bundle,
                name="head-drift-run.json",
            )
            stale = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                drift_run,
                "--repo",
                repo,
                *contract_args(),
            )

        self.assertEqual(1, stale.returncode)
        result = result_json(stale)
        self.assertEqual("blocked", result["status"])
        self.assertEqual(drift_envelopes, result["completed_reports"])
        messages = " ".join(error["message"] for error in result["errors"])
        self.assertIn("A Git-range source changed: src/discounts.py", messages)

    def test_validate_run_rechecks_live_explicit_patch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            patch_path = Path(temp_dir) / "change.patch"
            shutil.copyfile(
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
                patch_path,
            )
            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                patch_path,
                "--tree-root",
                SKILL_ROOT / "references" / "acceptance-tree",
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            run_path, envelopes = write_current_acceptance_run(temp_dir, bundle)
            validate_args = [
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                "--patch",
                patch_path,
                *contract_args(),
            ]
            current = run_contract(*validate_args)
            self.assertEqual(current.returncode, 0, current.stderr or current.stdout)
            self.assertEqual("complete", result_json(current)["status"])

            original = patch_path.read_bytes()
            patch_path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
            stale = run_contract(*validate_args)

        self.assertEqual(1, stale.returncode)
        result = result_json(stale)
        self.assertEqual("blocked", result["status"])
        self.assertEqual(envelopes, result["completed_reports"])
        messages = " ".join(error["message"] for error in result["errors"])
        self.assertIn("The explicit patch changed after the freeze.", messages)

    def test_run_success_preserves_route_order_and_separates_coverage_from_launch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            code_envelope["coverage"]["status"] = "partial"
            ponytail_envelope = valid_ponytail_review_envelope(attestation, checked_sha)
            ponytail_envelope["coverage"]["status"] = "not_assessed"
            ponytail_envelope["coverage"]["checked"] = []
            code_request = track_request_sha256(
                manifest,
                attestation,
                "code-review",
            )
            ponytail_request = track_request_sha256(
                manifest,
                attestation,
                "ponytail-review",
            )
            write(temp_dir, "code-review.json", json.dumps(code_envelope))
            write(temp_dir, "ponytail-review.json", json.dumps(ponytail_envelope))
            checks = [
                {
                    "name": "independence_capability",
                    "result": "passed",
                    "reason": "Synthetic fixture records independence as passed.",
                },
                {
                    "name": "recovery_capability",
                    "result": "not_run",
                    "reason": "No live recovery was attempted.",
                },
            ]
            run = review_run(
                [
                    run_attempt(
                        "code-review-001",
                        code_request,
                        envelope="code-review.json",
                    )
                ],
                [
                    run_attempt(
                        "ponytail-review-001",
                        ponytail_request,
                        envelope="ponytail-review.json",
                    )
                ],
                checks=checks,
            )
            run["tracks"].reverse()
            run_path = write(temp_dir, "run.json", json.dumps(run))
            completed = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                *explicit_patch_args(),
                *contract_args(),
            )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = result_json(completed)
        self.assertEqual("complete", result["status"])
        self.assertEqual(
            ["code-review", "ponytail-review"],
            [track["track_id"] for track in result["tracks"]],
        )
        self.assertEqual(
            ["launched", "launched"],
            [track["launch_status"] for track in result["tracks"]],
        )
        self.assertEqual(
            ["partial", "not_assessed"],
            [track["coverage_status"] for track in result["tracks"]],
        )
        self.assertEqual(
            [code_envelope, ponytail_envelope],
            result["completed_reports"],
        )
        self.assertEqual(checks, result["checks"])
        rendered = result["rendered"]
        self.assertIn("Overall status: `complete`", rendered)
        self.assertLess(
            rendered.index("## Track report: `code-review`"),
            rendered.index("## Track report: `ponytail-review`"),
        )
        self.assertIn("independence_capability", rendered)
        self.assertIn("`not_run`", rendered)

    def test_completed_track_with_blocked_coverage_blocks_without_dropping_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads(
                (bundle / "attestation.json").read_text(encoding="utf-8")
            )
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            code_envelope["coverage"]["status"] = "blocked"
            ponytail_envelope = valid_ponytail_review_envelope(
                attestation,
                checked_sha,
            )
            write(temp_dir, "code-review.json", json.dumps(code_envelope))
            write(temp_dir, "ponytail-review.json", json.dumps(ponytail_envelope))
            run = review_run(
                [
                    run_attempt(
                        "code-review-001",
                        track_request_sha256(
                            manifest,
                            attestation,
                            "code-review",
                        ),
                        envelope="code-review.json",
                    )
                ],
                [
                    run_attempt(
                        "ponytail-review-001",
                        track_request_sha256(
                            manifest,
                            attestation,
                            "ponytail-review",
                        ),
                        envelope="ponytail-review.json",
                    )
                ],
                checks=[
                    {
                        "name": "independence_capability",
                        "result": "passed",
                        "reason": "Synthetic fixture records independence as passed.",
                    }
                ],
            )
            run_path = write(temp_dir, "blocked-coverage.json", json.dumps(run))
            blocked = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                *explicit_patch_args(),
                *contract_args(),
            )

        self.assertEqual(1, blocked.returncode)
        result = result_json(blocked)
        self.assertEqual("blocked", result["status"])
        self.assertEqual([], result["missing_tracks"])
        self.assertEqual(
            ["completed", "completed"],
            [track["status"] for track in result["tracks"]],
        )
        self.assertEqual(
            ["launched", "launched"],
            [track["launch_status"] for track in result["tracks"]],
        )
        self.assertEqual(
            ["blocked", "complete"],
            [track["coverage_status"] for track in result["tracks"]],
        )
        self.assertEqual(
            [code_envelope, ponytail_envelope],
            result["completed_reports"],
        )
        self.assertIn("coverage_blocked", [error["code"] for error in result["errors"]])
        self.assertIn(
            "Completed track did not verify the frozen requirements.",
            result["rendered"],
        )
        self.assertIn("## Completed track reports", result["rendered"])

    def test_run_requires_meaningful_capability_checks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            ponytail_envelope = valid_ponytail_review_envelope(
                attestation,
                checked_sha,
            )
            write(temp_dir, "code-review.json", json.dumps(code_envelope))
            write(
                temp_dir,
                "ponytail-review.json",
                json.dumps(ponytail_envelope),
            )
            run = review_run(
                [
                    run_attempt(
                        "code-review-001",
                        track_request_sha256(
                            manifest,
                            attestation,
                            "code-review",
                        ),
                        envelope="code-review.json",
                    )
                ],
                [
                    run_attempt(
                        "ponytail-review-001",
                        track_request_sha256(
                            manifest,
                            attestation,
                            "ponytail-review",
                        ),
                        envelope="ponytail-review.json",
                    )
                ],
                checks=[
                    {
                        "name": "independence_capability",
                        "result": "passed",
                        "reason": "Synthetic fixture records independence as passed.",
                    }
                ],
            )

            for label, checks in (
                ("no checks", []),
                (
                    "unrelated check",
                    [
                        {
                            "name": "unrelated assumption",
                            "result": "not_run",
                            "reason": "Not a host capability.",
                        }
                    ],
                ),
            ):
                with self.subTest(label):
                    payload = copy.deepcopy(run)
                    payload["checks"] = checks
                    run_path = write(
                        temp_dir,
                        f"{label.replace(' ', '-')}.json",
                        json.dumps(payload),
                    )
                    rejected = run_contract(
                        "validate-run",
                        "--bundle",
                        bundle,
                        "--run",
                        run_path,
                        *explicit_patch_args(),
                        *contract_args(),
                    )
                    self.assertNotEqual(0, rejected.returncode)
                    result = result_json(rejected)
                    self.assertEqual("blocked", result["status"])
                    self.assertEqual(
                        [code_envelope, ponytail_envelope],
                        result["completed_reports"],
                    )
                    self.assertIn(
                        "capability_check_missing",
                        [error["code"] for error in result["errors"]],
                    )

            payload = copy.deepcopy(run)
            payload["checks"] = [
                {
                    "name": "recovery_capability",
                    "result": "not_run",
                    "reason": "No recovery was attempted.",
                }
            ]
            run_path = write(temp_dir, "missing-independence.json", json.dumps(payload))
            rejected = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                *explicit_patch_args(),
                *contract_args(),
            )
            self.assertNotEqual(0, rejected.returncode)
            result = result_json(rejected)
            self.assertEqual("blocked", result["status"])
            self.assertEqual(
                [code_envelope, ponytail_envelope],
                result["completed_reports"],
            )
            self.assertIn(
                "independence_capability_check_missing",
                [error["code"] for error in result["errors"]],
            )

            for result_value in ("not_run", "failed", "not_assessed"):
                with self.subTest(f"independence capability {result_value}"):
                    checks = [
                        {
                            "name": "independence_capability",
                            "result": result_value,
                            "reason": f"Independence capability was {result_value}.",
                        }
                    ]
                    payload = copy.deepcopy(run)
                    payload["checks"] = checks
                    run_path = write(
                        temp_dir,
                        f"independence-capability-{result_value}.json",
                        json.dumps(payload),
                    )
                    blocked = run_contract(
                        "validate-run",
                        "--bundle",
                        bundle,
                        "--run",
                        run_path,
                        *explicit_patch_args(),
                        *contract_args(),
                    )
                    self.assertEqual(1, blocked.returncode)
                    result = result_json(blocked)
                    self.assertEqual("blocked", result["status"])
                    self.assertEqual([], result["missing_tracks"])
                    self.assertEqual(
                        [code_envelope, ponytail_envelope],
                        result["completed_reports"],
                    )
                    self.assertEqual(checks, result["checks"])

    def test_run_record_accepts_lf_and_crlf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            code_request = track_request_sha256(
                manifest,
                attestation,
                "code-review",
            )
            ponytail_request = track_request_sha256(
                manifest,
                attestation,
                "ponytail-review",
            )
            write(
                temp_dir,
                "code-review.json",
                json.dumps(valid_code_review_envelope(attestation, checked_sha)),
            )
            write(
                temp_dir,
                "ponytail-review.json",
                json.dumps(valid_ponytail_review_envelope(attestation, checked_sha)),
            )
            run = review_run(
                [
                    run_attempt(
                        "code-review-001",
                        code_request,
                        envelope="code-review.json",
                    )
                ],
                [
                    run_attempt(
                        "ponytail-review-001",
                        ponytail_request,
                        envelope="ponytail-review.json",
                    )
                ],
                checks=[
                    {
                        "name": "independence_capability",
                        "result": "passed",
                    "reason": "Synthetic fixture records independence as passed.",
                    }
                ],
            )
            lf_bytes = json.dumps(run, indent=2).encode("utf-8").replace(b"\r\n", b"\n")
            for label, data in (
                ("lf", lf_bytes),
                ("crlf", lf_bytes.replace(b"\n", b"\r\n")),
            ):
                with self.subTest(label):
                    self.assertIn(b"\n", data)
                    self.assertEqual(label == "crlf", b"\r\n" in data)
                    run_path = Path(temp_dir) / f"run-{label}.json"
                    run_path.write_bytes(data)
                    completed = run_contract(
                        "validate-run",
                        "--bundle",
                        bundle,
                        "--run",
                        run_path,
                        *explicit_patch_args(),
                        *contract_args(),
                    )
                    self.assertEqual(
                        completed.returncode,
                        0,
                        completed.stderr or completed.stdout,
                    )
                    self.assertEqual("complete", result_json(completed)["status"])

    def test_run_blocks_missing_unstartable_invalid_and_mismatched_required_tracks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            ponytail_envelope = valid_ponytail_review_envelope(attestation, checked_sha)
            code_request = track_request_sha256(
                manifest,
                attestation,
                "code-review",
            )
            ponytail_request = track_request_sha256(
                manifest,
                attestation,
                "ponytail-review",
            )
            write(temp_dir, "code-review.json", json.dumps(code_envelope))
            write(temp_dir, "ponytail-review.json", json.dumps(ponytail_envelope))
            code_attempt = run_attempt(
                "code-review-001",
                code_request,
                envelope="code-review.json",
            )

            write(temp_dir, "blank.json", "")
            write(temp_dir, "truncated.json", '{"contract_version":')
            unverifiable = copy.deepcopy(ponytail_envelope)
            del unverifiable["native"]
            write(temp_dir, "unverifiable.json", json.dumps(unverifiable))
            wrong_scope = copy.deepcopy(ponytail_envelope)
            wrong_scope["attestation"]["patch_sha256"] = "0" * 64
            write(temp_dir, "wrong-scope.json", json.dumps(wrong_scope))

            cases = {
                "missing": [],
                "unstartable": [
                    run_attempt(
                        "ponytail-review-001",
                        ponytail_request,
                        failure={
                            "class": "launch_failure",
                            "evidence": "No independent sub-agent runtime was available.",
                        },
                        launch_status="not_launched",
                    )
                ],
                "blank": [
                    run_attempt(
                        "ponytail-review-001",
                        ponytail_request,
                        envelope="blank.json",
                    )
                ],
                "truncated": [
                    run_attempt(
                        "ponytail-review-001",
                        ponytail_request,
                        envelope="truncated.json",
                    )
                ],
                "unverifiable": [
                    run_attempt(
                        "ponytail-review-001",
                        ponytail_request,
                        envelope="unverifiable.json",
                    )
                ],
                "missing report": [
                    run_attempt(
                        "ponytail-review-001",
                        ponytail_request,
                        envelope="not-created.json",
                    )
                ],
                "scope mismatch": [
                    run_attempt(
                        "ponytail-review-001",
                        ponytail_request,
                        envelope="wrong-scope.json",
                    )
                ],
                "malformed attempt": [
                    {
                        "invocation_id": "ponytail-review-001",
                        "status": "completed",
                        "launch_status": "unknown",
                        "request_sha256": ponytail_request,
                        "envelope": "ponytail-review.json",
                    }
                ],
                "malformed attempt list launch status": [
                    {
                        "invocation_id": "ponytail-review-001",
                        "status": "completed",
                        "launch_status": [],
                        "request_sha256": ponytail_request,
                        "envelope": "ponytail-review.json",
                    }
                ],
                "malformed attempt object launch status": [
                    {
                        "invocation_id": "ponytail-review-001",
                        "status": "completed",
                        "launch_status": {"source": "host"},
                        "request_sha256": ponytail_request,
                        "envelope": "ponytail-review.json",
                    }
                ],
            }
            for label, ponytail_attempts in cases.items():
                with self.subTest(label):
                    run_path = write(
                        temp_dir,
                        f"{label.replace(' ', '-')}.json",
                        json.dumps(review_run([code_attempt], ponytail_attempts)),
                    )
                    completed = run_contract(
                        "validate-run",
                        "--bundle",
                        bundle,
                        "--run",
                        run_path,
                        *explicit_patch_args(),
                        *contract_args(),
                    )
                    self.assertEqual(1, completed.returncode)
                    result = result_json(completed)
                    self.assertEqual("blocked", result["status"])
                    self.assertEqual(["ponytail-review"], result["missing_tracks"])
                    self.assertEqual([code_envelope], result["completed_reports"])
                    self.assertEqual(
                        "not_assessed",
                        result["tracks"][1]["coverage_status"],
                    )
                    self.assertIn("Overall status: `blocked`", result["rendered"])
                    self.assertIn("This is not a passing review.", result["rendered"])
                    self.assertIn(
                        "### 1. Preview converts Decimal money to float",
                        result["rendered"],
                    )

            invalid_track_run = review_run([code_attempt], [])
            invalid_track_run["tracks"][1]["attempts"] = None
            invalid_track_path = write(
                temp_dir,
                "invalid-track-attempts.json",
                json.dumps(invalid_track_run),
            )
            blocked = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                invalid_track_path,
                *explicit_patch_args(),
                *contract_args(),
            )
            self.assertEqual(1, blocked.returncode)
            result = result_json(blocked)
            self.assertEqual("blocked", result["status"])
            self.assertEqual([code_envelope], result["completed_reports"])
            self.assertEqual("failed", result["tracks"][1]["status"])

    def test_run_preserves_completed_reports_when_track_entries_or_checks_are_malformed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads(
                (bundle / "attestation.json").read_text(encoding="utf-8")
            )
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            ponytail_envelope = valid_ponytail_review_envelope(
                attestation,
                checked_sha,
            )
            write(temp_dir, "code-review.json", json.dumps(code_envelope))
            write(temp_dir, "ponytail-review.json", json.dumps(ponytail_envelope))
            code_attempt = run_attempt(
                "code-review-001",
                track_request_sha256(manifest, attestation, "code-review"),
                envelope="code-review.json",
            )
            ponytail_attempt = run_attempt(
                "ponytail-review-001",
                track_request_sha256(manifest, attestation, "ponytail-review"),
                envelope="ponytail-review.json",
            )

            malformed_tracks = review_run([code_attempt], [])
            malformed_tracks["tracks"] = [
                {"track_id": "code-review", "attempts": None},
                {"track_id": "code-review", "attempts": [code_attempt]},
                {"track_id": "unknown-review", "attempts": []},
                "not-an-object",
                {"attempts": []},
            ]
            malformed_tracks_path = write(
                temp_dir,
                "malformed-tracks.json",
                json.dumps(malformed_tracks),
            )
            blocked = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                malformed_tracks_path,
                *explicit_patch_args(),
                *contract_args(),
            )

            self.assertEqual(1, blocked.returncode)
            result = result_json(blocked)
            self.assertEqual("blocked", result["status"])
            self.assertEqual([code_envelope], result["completed_reports"])
            self.assertEqual(
                ["completed", "missing"],
                [track["status"] for track in result["tracks"]],
            )
            self.assertEqual(["ponytail-review"], result["missing_tracks"])
            error_codes = [error["code"] for error in result["errors"]]
            self.assertIn("run_invalid", error_codes)
            self.assertIn("track_not_routed", error_codes)
            self.assertIn(
                "Preview converts Decimal money to float",
                result["rendered"],
            )

            malformed_checks = review_run([code_attempt], [ponytail_attempt])
            malformed_checks["checks"] = None
            malformed_checks_path = write(
                temp_dir,
                "malformed-checks.json",
                json.dumps(malformed_checks),
            )
            blocked = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                malformed_checks_path,
                *explicit_patch_args(),
                *contract_args(),
            )

            self.assertEqual(1, blocked.returncode)
            result = result_json(blocked)
            self.assertEqual("blocked", result["status"])
            self.assertEqual(
                [code_envelope, ponytail_envelope],
                result["completed_reports"],
            )
            error_codes = [error["code"] for error in result["errors"]]
            self.assertIn("run_invalid", error_codes)
            self.assertIn("capability_check_missing", error_codes)

    def test_run_allows_one_bounded_recovery_with_the_same_frozen_request(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            ponytail_envelope = valid_ponytail_review_envelope(attestation, checked_sha)
            ponytail_envelope["invocation_id"] = "ponytail-review-002"
            code_request = track_request_sha256(
                manifest,
                attestation,
                "code-review",
            )
            ponytail_request = track_request_sha256(
                manifest,
                attestation,
                "ponytail-review",
            )
            checks = [
                {
                    "name": "independence_capability",
                    "result": "passed",
                    "reason": "Synthetic fixture records independence as passed.",
                },
                {
                    "name": "recovery_capability",
                    "result": "passed",
                    "reason": "Synthetic fixture records recovery as passed.",
                },
            ]
            write(temp_dir, "code-review.json", json.dumps(code_envelope))
            write(temp_dir, "ponytail-review.json", json.dumps(ponytail_envelope))
            code_attempt = run_attempt(
                "code-review-001",
                code_request,
                envelope="code-review.json",
            )
            failed_attempt = run_attempt(
                "ponytail-review-001",
                ponytail_request,
                failure={
                    "class": "transient_transport",
                    "evidence": {
                        "source": "host",
                        "phase": "transport",
                        "detail": "The transport reset after the request was sent.",
                    },
                },
            )
            recovered_attempt = run_attempt(
                "ponytail-review-002",
                ponytail_request,
                envelope="ponytail-review.json",
                recovery={
                    "of_invocation_id": "ponytail-review-001",
                    "analysis_reused": False,
                },
            )
            run = review_run(
                [code_attempt],
                [failed_attempt, recovered_attempt],
                checks=checks,
            )
            run_path = write(temp_dir, "recovered.json", json.dumps(run))
            completed = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                *explicit_patch_args(),
                *contract_args(),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            result = result_json(completed)
            self.assertEqual("complete", result["status"])
            self.assertEqual(
                [code_envelope, ponytail_envelope],
                result["completed_reports"],
            )
            self.assertEqual(checks, result["checks"])
            self.assertEqual(2, len(result["tracks"][1]["attempts"]))
            self.assertIn("one bounded recovery", result["rendered"])
            self.assertIn("recorded `analysis_reused: false`", result["rendered"])
            self.assertIn("not independently verified", result["rendered"])
            self.assertNotIn("fresh analysis", result["rendered"])

            for result_value in ("not_run", "failed", "not_assessed"):
                with self.subTest(f"recovery capability {result_value}"):
                    blocked_checks = copy.deepcopy(checks)
                    blocked_checks[1] = {
                        "name": "recovery_capability",
                        "result": result_value,
                        "reason": f"Recovery capability was {result_value}.",
                    }
                    bad = copy.deepcopy(run)
                    bad["checks"] = blocked_checks
                    run_path = write(
                        temp_dir,
                        f"recovery-capability-{result_value}.json",
                        json.dumps(bad),
                    )
                    blocked = run_contract(
                        "validate-run",
                        "--bundle",
                        bundle,
                        "--run",
                        run_path,
                        *explicit_patch_args(),
                        *contract_args(),
                    )
                    self.assertEqual(1, blocked.returncode)
                    blocked_result = result_json(blocked)
                    self.assertEqual("blocked", blocked_result["status"])
                    self.assertEqual([], blocked_result["missing_tracks"])
                    self.assertEqual(
                        [code_envelope, ponytail_envelope],
                        blocked_result["completed_reports"],
                    )
                    self.assertEqual(blocked_checks, blocked_result["checks"])

            blocked_cases = {}
            bad = copy.deepcopy(run)
            bad["tracks"][1]["attempts"][0]["failure"] = {
                "class": "launch_failure",
                "evidence": "The host had no sub-agent runtime.",
            }
            bad["tracks"][1]["attempts"][0]["launch_status"] = "not_launched"
            blocked_cases["permanent failure"] = bad

            bad = copy.deepcopy(run)
            bad["tracks"][1]["attempts"][1]["request_sha256"] = "c" * 64
            blocked_cases["arbitrary recovery request hash"] = bad

            bad = copy.deepcopy(run)
            bad["tracks"][1]["attempts"][0]["request_sha256"] = "c" * 64
            bad["tracks"][1]["attempts"][1]["request_sha256"] = "c" * 64
            blocked_cases["arbitrary request hashes"] = bad

            bad = copy.deepcopy(run)
            bad["tracks"][1]["attempts"][1]["invocation_id"] = "ponytail-review-001"
            blocked_cases["reused invocation"] = bad

            bad = copy.deepcopy(run)
            bad["tracks"][1]["attempts"][1]["recovery"]["analysis_reused"] = True
            blocked_cases["reused analysis"] = bad

            bad = copy.deepcopy(run)
            del bad["tracks"][1]["attempts"][1]["recovery"]
            blocked_cases["implicit retry"] = bad

            bad = copy.deepcopy(run)
            bad["tracks"][1]["attempts"][0]["failure"] = {
                "class": "transient_transport",
                "evidence": "Transport failed.",
            }
            blocked_cases["malformed transient evidence"] = bad

            bad = copy.deepcopy(run)
            bad["tracks"][1]["attempts"][0]["launch_status"] = "not_launched"
            blocked_cases["non-launched transient"] = bad

            bad = copy.deepcopy(run)
            bad["tracks"][1]["attempts"].append(
                run_attempt(
                    "ponytail-review-003",
                    ponytail_request,
                    envelope="ponytail-review.json",
                    recovery={
                        "of_invocation_id": "ponytail-review-002",
                        "analysis_reused": False,
                    },
                )
            )
            blocked_cases["second recovery"] = bad

            for label, payload in blocked_cases.items():
                with self.subTest(label):
                    run_path = write(
                        temp_dir,
                        f"{label.replace(' ', '-')}.json",
                        json.dumps(payload),
                    )
                    blocked = run_contract(
                        "validate-run",
                        "--bundle",
                        bundle,
                        "--run",
                        run_path,
                        *explicit_patch_args(),
                        *contract_args(),
                    )
                    self.assertNotEqual(0, blocked.returncode)
                    result = result_json(blocked)
                    self.assertEqual("blocked", result["status"])
                    self.assertEqual(["ponytail-review"], result["missing_tracks"])
                    self.assertEqual([code_envelope], result["completed_reports"])

            error_cases = {}
            recovered_code_envelope = copy.deepcopy(code_envelope)
            recovered_code_envelope["invocation_id"] = "code-review-002"
            write(
                temp_dir,
                "code-review-002.json",
                json.dumps(recovered_code_envelope),
            )
            bad = copy.deepcopy(run)
            bad["tracks"][0] = {
                "track_id": "code-review",
                "attempts": [
                    run_attempt(
                        "code-review-001",
                        code_request,
                        failure={
                            "class": "transient_runtime",
                            "evidence": {
                                "source": "host",
                                "phase": "runtime",
                                "detail": "The runtime stopped after launch.",
                            },
                        },
                    ),
                    run_attempt(
                        "code-review-002",
                        code_request,
                        envelope="code-review-002.json",
                        recovery={
                            "of_invocation_id": "code-review-001",
                            "analysis_reused": False,
                        },
                    ),
                ],
            }
            error_cases["two tracks recover"] = (
                bad,
                "recovery_limit",
                [recovered_code_envelope, ponytail_envelope],
            )

            bad = copy.deepcopy(run)
            bad["checks"] = [checks[0]]
            error_cases["missing recovery capability check"] = (
                bad,
                "recovery_capability_check_missing",
                [code_envelope, ponytail_envelope],
            )

            bad = copy.deepcopy(run)
            bad["tracks"][1]["attempts"][0]["invocation_id"] = "code-review-001"
            bad["tracks"][1]["attempts"][1]["recovery"]["of_invocation_id"] = (
                "code-review-001"
            )
            error_cases["duplicate invocation IDs"] = (
                bad,
                "run_invalid",
                [code_envelope, ponytail_envelope],
            )

            for label, (payload, expected_code, expected_reports) in error_cases.items():
                with self.subTest(label):
                    run_path = write(
                        temp_dir,
                        f"{label.replace(' ', '-')}.json",
                        json.dumps(payload),
                    )
                    blocked = run_contract(
                        "validate-run",
                        "--bundle",
                        bundle,
                        "--run",
                        run_path,
                        *explicit_patch_args(),
                        *contract_args(),
                    )
                    self.assertNotEqual(0, blocked.returncode)
                    result = result_json(blocked)
                    self.assertEqual("blocked", result["status"])
                    self.assertEqual(expected_reports, result["completed_reports"])
                    self.assertIn(
                        expected_code,
                        [error["code"] for error in result["errors"]],
                    )

    def test_recovery_envelope_failure_preserves_metadata_and_recovery_gate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads(
                (bundle / "attestation.json").read_text(encoding="utf-8")
            )
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            write(temp_dir, "code-review.json", json.dumps(code_envelope))
            code_attempt = run_attempt(
                "code-review-001",
                track_request_sha256(manifest, attestation, "code-review"),
                envelope="code-review.json",
            )
            ponytail_request = track_request_sha256(
                manifest,
                attestation,
                "ponytail-review",
            )
            checks = [
                {
                    "name": "independence_capability",
                    "result": "not_run",
                    "reason": "Synthetic records do not demonstrate live independence.",
                }
            ]

            for label, content in (
                ("blank", ""),
                ("corrupt", '{"contract_version":'),
            ):
                with self.subTest(label):
                    envelope_name = f"ponytail-{label}.json"
                    write(temp_dir, envelope_name, content)
                    failed_attempt = run_attempt(
                        "ponytail-review-001",
                        ponytail_request,
                        failure={
                            "class": "transient_runtime",
                            "evidence": {
                                "source": "host",
                                "phase": "runtime",
                                "detail": "The runtime stopped after launch.",
                            },
                        },
                    )
                    recovery_attempt = run_attempt(
                        "ponytail-review-002",
                        ponytail_request,
                        envelope=envelope_name,
                        recovery={
                            "of_invocation_id": "ponytail-review-001",
                            "analysis_reused": False,
                        },
                    )
                    run = review_run(
                        [code_attempt],
                        [failed_attempt, recovery_attempt],
                        checks=checks,
                    )
                    run_path = write(
                        temp_dir,
                        f"recovery-{label}.json",
                        json.dumps(run),
                    )
                    blocked = run_contract(
                        "validate-run",
                        "--bundle",
                        bundle,
                        "--run",
                        run_path,
                        *explicit_patch_args(),
                        *contract_args(),
                    )

                    self.assertEqual(1, blocked.returncode)
                    result = result_json(blocked)
                    self.assertEqual("blocked", result["status"])
                    self.assertEqual(["ponytail-review"], result["missing_tracks"])
                    self.assertEqual([code_envelope], result["completed_reports"])
                    attempts = result["tracks"][1]["attempts"]
                    self.assertEqual(2, len(attempts))
                    self.assertEqual(
                        "ponytail-review-002",
                        attempts[1]["invocation_id"],
                    )
                    self.assertIn("recovery", attempts[1])
                    self.assertEqual("invalid_result", attempts[1]["failure"]["class"])
                    self.assertIn(
                        "recovery_capability_check_missing",
                        [error["code"] for error in result["errors"]],
                    )
                    self.assertNotIn("implicit retry", result["rendered"])

    def test_nul_envelope_path_degrades_only_that_track(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads(
                (bundle / "attestation.json").read_text(encoding="utf-8")
            )
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            write(temp_dir, "code-review.json", json.dumps(code_envelope))
            run = review_run(
                [
                    run_attempt(
                        "code-review-001",
                        track_request_sha256(
                            manifest,
                            attestation,
                            "code-review",
                        ),
                        envelope="code-review.json",
                    )
                ],
                [
                    run_attempt(
                        "ponytail-review-001",
                        track_request_sha256(
                            manifest,
                            attestation,
                            "ponytail-review",
                        ),
                        envelope="ponytail-review\x00.json",
                    )
                ],
            )
            run_path = write(temp_dir, "nul-envelope.json", json.dumps(run))
            blocked = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                *explicit_patch_args(),
                *contract_args(),
            )

        self.assertEqual(1, blocked.returncode)
        result = result_json(blocked)
        self.assertEqual("blocked", result["status"])
        self.assertEqual(["ponytail-review"], result["missing_tracks"])
        self.assertEqual([code_envelope], result["completed_reports"])
        self.assertEqual("failed", result["tracks"][1]["status"])
        self.assertEqual(
            "invalid_result",
            result["tracks"][1]["attempts"][0]["failure"]["class"],
        )
        self.assertIn(
            "### 1. Preview converts Decimal money to float",
            result["rendered"],
        )

    def test_partial_mode_requires_post_block_approval_and_records_the_gap(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads((bundle / "attestation.json").read_text(encoding="utf-8"))
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            code_request = track_request_sha256(
                manifest,
                attestation,
                "code-review",
            )
            ponytail_request = track_request_sha256(
                manifest,
                attestation,
                "ponytail-review",
            )
            write(temp_dir, "code-review.json", json.dumps(code_envelope))
            code_attempt = run_attempt(
                "code-review-001",
                code_request,
                envelope="code-review.json",
            )
            failed_attempt = run_attempt(
                "ponytail-review-001",
                ponytail_request,
                failure={
                    "class": "launch_failure",
                    "evidence": "The second independent sub-agent did not start.",
                },
                launch_status="not_launched",
            )
            blocked_run = review_run([code_attempt], [failed_attempt])
            blocked_run_path = write(
                temp_dir,
                "blocked-run.json",
                json.dumps(blocked_run),
            )
            blocked = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                blocked_run_path,
                *explicit_patch_args(),
                *contract_args(),
            )
            self.assertEqual(1, blocked.returncode)
            blocked_result = result_json(blocked)
            self.assertEqual("blocked", blocked_result["status"])
            blocked_result_path = write(
                temp_dir,
                "blocked-result.json",
                json.dumps(blocked_result),
            )
            blocked_digest = hashlib.sha256(
                blocked_result_path.read_bytes()
            ).hexdigest()
            partial = {
                "approval": {
                    "source": "user",
                    "evidence": "User approved retaining the completed code-review track.",
                },
                "blocked_result": {
                    "path": "blocked-result.json",
                    "sha256": blocked_digest,
                },
                "missing_track_ids": ["ponytail-review"],
                "reduced_independence": (
                    "Only one of two required independent review tracks completed."
                ),
            }
            run = review_run([code_attempt], [failed_attempt], partial=partial)
            run_path = write(temp_dir, "partial-run.json", json.dumps(run))
            completed = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                *explicit_patch_args(),
                *contract_args(),
            )

            self.assertEqual(1, completed.returncode)
            result = result_json(completed)
            self.assertEqual("partial", result["status"], result.get("errors"))
            self.assertEqual(["ponytail-review"], result["missing_tracks"])
            self.assertEqual(
                [
                    {"track_id": "code-review", "status": "complete"},
                    {
                        "track_id": "ponytail-review",
                        "status": "not_assessed",
                        "reason": "Required review track did not complete.",
                    },
                ],
                result["partial"]["coverage"],
            )
            self.assertEqual(
                [
                    {
                        "track_id": code_envelope["track_id"],
                        "invocation_id": code_envelope["invocation_id"],
                    }
                ],
                result["partial"]["completed_reports"],
            )
            self.assertEqual([code_envelope], result["completed_reports"])
            rendered = result["rendered"]
            self.assertIn("Overall status: `partial`", rendered)
            self.assertIn("blocked one-track partial review", rendered)
            self.assertIn("not a complete parallel review", rendered)
            self.assertIn("Missing tracks: `ponytail-review`", rendered)
            self.assertIn("Approval source: user", rendered)
            self.assertIn(blocked_digest, rendered)
            self.assertIn("Reduced independence:", rendered)
            self.assertIn("`ponytail-review`: `not_assessed`", rendered)
            self.assertIn(
                "Preview converts Decimal money to float",
                rendered,
            )
            self.assertNotIn("Overall status: `complete`", rendered)

            cases = {}
            bad = copy.deepcopy(run)
            bad["partial"]["approval"]["source"] = "coordinator"
            cases["not user approved"] = (bad, "partial_approval_invalid")

            bad = copy.deepcopy(run)
            bad["partial"]["approval"]["evidence"] = ""
            cases["no evidence"] = (bad, "partial_approval_invalid")

            bad = copy.deepcopy(run)
            bad["partial"]["missing_track_ids"] = ["code-review"]
            cases["wrong gap"] = (bad, "partial_gap_mismatch")

            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"]["sha256"] = "0" * 64
            cases["wrong blocked digest"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            not_blocked = copy.deepcopy(blocked_result)
            not_blocked["status"] = "complete"
            not_blocked_path = write(
                temp_dir,
                "not-blocked-result.json",
                json.dumps(not_blocked),
            )
            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"] = {
                "path": "not-blocked-result.json",
                "sha256": hashlib.sha256(
                    not_blocked_path.read_bytes()
                ).hexdigest(),
            }
            cases["not blocked artifact"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            wrong_blocked = copy.deepcopy(blocked_result)
            wrong_blocked["missing_tracks"] = []
            wrong_blocked_path = write(
                temp_dir,
                "wrong-blocked-result.json",
                json.dumps(wrong_blocked),
            )
            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"] = {
                "path": "wrong-blocked-result.json",
                "sha256": hashlib.sha256(
                    wrong_blocked_path.read_bytes()
                ).hexdigest(),
            }
            cases["wrong blocked gap"] = (bad, "partial_gap_mismatch")

            minimal = {
                "status": "blocked",
                "missing_tracks": ["ponytail-review"],
                "completed_reports": [
                    {
                        "track_id": "code-review",
                        "invocation_id": "code-review-001",
                    }
                ],
            }
            minimal_path = write(
                temp_dir,
                "minimal-blocked-result.json",
                json.dumps(minimal),
            )
            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"] = {
                "path": "minimal-blocked-result.json",
                "sha256": hashlib.sha256(minimal_path.read_bytes()).hexdigest(),
            }
            cases["minimal blocked forgery"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            changed_findings = copy.deepcopy(blocked_result)
            changed_findings["completed_reports"][0]["findings"][0]["title"] = (
                "Changed with the same report identities"
            )
            changed_findings_path = write(
                temp_dir,
                "changed-findings-blocked-result.json",
                json.dumps(changed_findings),
            )
            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"] = {
                "path": "changed-findings-blocked-result.json",
                "sha256": hashlib.sha256(
                    changed_findings_path.read_bytes()
                ).hexdigest(),
            }
            cases["changed findings"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            changed_rendered = copy.deepcopy(blocked_result)
            changed_rendered["rendered"] += "\nForged review summary.\n"
            changed_rendered_path = write(
                temp_dir,
                "changed-rendered-blocked-result.json",
                json.dumps(changed_rendered),
            )
            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"] = {
                "path": "changed-rendered-blocked-result.json",
                "sha256": hashlib.sha256(
                    changed_rendered_path.read_bytes()
                ).hexdigest(),
            }
            cases["changed rendered summary"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            changed_summary = copy.deepcopy(blocked_result)
            changed_summary["tracks"][0]["finding_count"] += 1
            changed_summary_path = write(
                temp_dir,
                "changed-track-summary-blocked-result.json",
                json.dumps(changed_summary),
            )
            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"] = {
                "path": "changed-track-summary-blocked-result.json",
                "sha256": hashlib.sha256(changed_summary_path.read_bytes()).hexdigest(),
            }
            cases["changed track summary"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            changed_count = copy.deepcopy(blocked_result)
            changed_count["tracks"][0]["finding_count"] = float(
                changed_count["tracks"][0]["finding_count"]
            )
            changed_count_path = write(
                temp_dir,
                "changed-count-blocked-result.json",
                json.dumps(changed_count),
            )
            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"] = {
                "path": "changed-count-blocked-result.json",
                "sha256": hashlib.sha256(changed_count_path.read_bytes()).hexdigest(),
            }
            cases["float track count"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            changed_count = copy.deepcopy(blocked_result)
            changed_count["completed_reports"][0]["contract_version"] = True
            changed_count_path = write(
                temp_dir,
                "boolean-count-blocked-result.json",
                json.dumps(changed_count),
            )
            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"] = {
                "path": "boolean-count-blocked-result.json",
                "sha256": hashlib.sha256(changed_count_path.read_bytes()).hexdigest(),
            }
            cases["boolean track count"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"]["path"] = "../blocked-result.json"
            cases["unsafe artifact path"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            bad = copy.deepcopy(run)
            bad["partial"]["blocked_result"]["path"] = "blocked\x00-result.json"
            cases["NUL artifact path"] = (
                bad,
                "partial_blocked_result_invalid",
            )

            for label, (payload, expected_code) in cases.items():
                with self.subTest(label):
                    run_path = write(
                        temp_dir,
                        f"partial-{label.replace(' ', '-')}.json",
                        json.dumps(payload),
                    )
                    blocked = run_contract(
                        "validate-run",
                        "--bundle",
                        bundle,
                        "--run",
                        run_path,
                        *explicit_patch_args(),
                        *contract_args(),
                    )
                    self.assertNotEqual(0, blocked.returncode)
                    result = result_json(blocked)
                    self.assertEqual("blocked", result["status"])
                    self.assertEqual([code_envelope], result["completed_reports"])
                    self.assertIn(
                        expected_code,
                        [error["code"] for error in result["errors"]],
                    )

            same_pass = copy.deepcopy(run)
            same_pass["partial"]["blocked_result"]["path"] = "same-pass.json"
            same_pass_path = write(
                temp_dir,
                "same-pass.json",
                json.dumps(same_pass),
            )
            rejected = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                same_pass_path,
                *explicit_patch_args(),
                *contract_args(),
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn(
                "partial_blocked_result_invalid",
                [error["code"] for error in result_json(rejected)["errors"]],
            )

    def test_symlink_escape_is_rejected_for_envelopes_and_partial_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads(
                (bundle / "attestation.json").read_text(encoding="utf-8")
            )
            code_envelope = valid_code_review_envelope(attestation, checked_sha)
            ponytail_envelope = valid_ponytail_review_envelope(attestation, checked_sha)
            code_request = track_request_sha256(
                manifest,
                attestation,
                "code-review",
            )
            ponytail_request = track_request_sha256(
                manifest,
                attestation,
                "ponytail-review",
            )
            run_dir = Path(temp_dir) / "run"
            outside_dir = Path(temp_dir) / "outside"
            run_dir.mkdir()
            outside_dir.mkdir()
            write(run_dir, "code-review.json", json.dumps(code_envelope))
            write(
                outside_dir,
                "ponytail-review.json",
                json.dumps(ponytail_envelope),
            )
            try:
                make_directory_link(run_dir / "outside", outside_dir)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Directory links are unavailable: {exc}")

            code_attempt = run_attempt(
                "code-review-001",
                code_request,
                envelope="code-review.json",
            )
            ponytail_attempt = run_attempt(
                "ponytail-review-001",
                ponytail_request,
                envelope="outside/ponytail-review.json",
            )
            run = review_run([code_attempt], [ponytail_attempt])
            run_path = write(run_dir, "blocked-run.json", json.dumps(run))
            blocked = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                *explicit_patch_args(),
                *contract_args(),
            )

            self.assertEqual(1, blocked.returncode)
            blocked_result = result_json(blocked)
            self.assertEqual("blocked", blocked_result["status"])
            self.assertEqual([code_envelope], blocked_result["completed_reports"])
            self.assertEqual(
                "invalid_result",
                blocked_result["tracks"][1]["attempts"][0]["failure"]["class"],
            )

            outside_artifact = write(
                outside_dir,
                "blocked-result.json",
                json.dumps(blocked_result),
            )
            partial = {
                "approval": {
                    "source": "user",
                    "evidence": "User approved the one-track partial review.",
                },
                "blocked_result": {
                    "path": "outside/blocked-result.json",
                    "sha256": hashlib.sha256(
                        outside_artifact.read_bytes()
                    ).hexdigest(),
                },
                "missing_track_ids": ["ponytail-review"],
                "reduced_independence": "Only one required track completed.",
            }
            follow_up = review_run(
                [code_attempt],
                [ponytail_attempt],
                partial=partial,
            )
            follow_up_path = write(run_dir, "partial-run.json", json.dumps(follow_up))
            rejected = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                follow_up_path,
                *explicit_patch_args(),
                *contract_args(),
            )

        self.assertEqual(1, rejected.returncode)
        result = result_json(rejected)
        self.assertEqual("blocked", result["status"])
        self.assertEqual([code_envelope], result["completed_reports"])
        self.assertIn(
            "partial_blocked_result_invalid",
            [error["code"] for error in result["errors"]],
        )

    def test_partial_mode_rejects_a_hardlink_to_the_current_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads(
                (bundle / "attestation.json").read_text(encoding="utf-8")
            )
            write(
                temp_dir,
                "code-review.json",
                json.dumps(valid_code_review_envelope(attestation, checked_sha)),
            )
            run = review_run(
                [
                    run_attempt(
                        "code-review-001",
                        track_request_sha256(
                            manifest,
                            attestation,
                            "code-review",
                        ),
                        envelope="code-review.json",
                    )
                ],
                [
                    run_attempt(
                        "ponytail-review-001",
                        track_request_sha256(
                            manifest,
                            attestation,
                            "ponytail-review",
                        ),
                        failure={
                            "class": "launch_failure",
                            "evidence": "The second independent sub-agent did not start.",
                        },
                        launch_status="not_launched",
                    )
                ],
                partial={
                    "approval": {
                        "source": "user",
                        "evidence": "User approved the one-track partial review.",
                    },
                    "blocked_result": {
                        "path": "current-run-hardlink.json",
                        "sha256": "0" * 64,
                    },
                    "missing_track_ids": ["ponytail-review"],
                    "reduced_independence": "Only one required track completed.",
                },
            )
            run_path = write(temp_dir, "hardlink-run.json", json.dumps(run))
            try:
                os.link(
                    run_path,
                    Path(temp_dir) / "current-run-hardlink.json",
                )
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Hard links are unavailable: {exc}")
            rejected = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                *explicit_patch_args(),
                *contract_args(),
            )

        self.assertNotEqual(0, rejected.returncode)
        self.assertIn(
            "partial_blocked_result_invalid",
            [error["code"] for error in result_json(rejected)["errors"]],
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

    def test_ponytail_adapter_is_thin_and_preserves_the_upstream_native_report(self):
        text = PONYTAIL_UPSTREAM_SOURCE.read_text(encoding="utf-8")
        payload = json.loads(text.split("```json", 1)[1].split("```", 1)[0])
        self.assertEqual(1, payload["contract_version"])
        self.assertEqual(
            {
                "name": "/ponytail-review",
                "source": "https://github.com/DietrichGebert/ponytail",
            },
            payload["upstream"],
        )
        self.assertEqual(
            ["patch", "tree", "requirements", "standards", "checks", "exclusions"],
            payload["required_inputs"],
        )

        normalized = " ".join(text.lower().replace("`", "").split())
        self.assertIn("thin integration boundary", normalized)
        self.assertIn("supplies no replacement review criteria", normalized)
        self.assertIn("read the original upstream /ponytail-review skill", normalized)
        self.assertIn("same frozen bundle", normalized)
        self.assertIn("manifest digest", normalized)
        self.assertIn("patch attestation", normalized)
        self.assertIn("included paths", normalized)
        self.assertIn("must fix", normalized)
        self.assertIn("should fix", normalized)
        self.assertIn("nice to have", normalized)
        self.assertIn("verdict", normalized)
        self.assertIn("lean", normalized)
        self.assertIn("not checked", normalized)
        self.assertIn("do not merge", normalized)
        self.assertIn("reorder findings", normalized)
        self.assertIn("p0/p1/p2", normalized)
        self.assertIn("cite the exact frozen source path", normalized)
        self.assertIn("synthetic", normalized)
        self.assertIn("not evidence", normalized)
        self.assertNotIn("bug:** wrong result", normalized)

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

    def test_acceptance_package_is_review_only_and_renders_both_expected_tracks(self):
        patch = SKILL_ROOT / "references" / "acceptance-fixture.patch"
        scenario = " ".join(
            (SKILL_ROOT / "references" / "acceptance-scenario.md")
            .read_text(encoding="utf-8")
            .lower()
            .split()
        )
        self.assertIn("do not apply", scenario)
        self.assertIn("not run", scenario)
        self.assertIn("model discovery", scenario)
        self.assertIn("explicit invocation", scenario)
        self.assertIn("`/code-review` track", scenario)
        self.assertIn("`/ponytail-review` track", scenario)
        self.assertIn("same frozen bundle", scenario)
        self.assertIn("routing-table order", scenario)
        self.assertIn("different independent sub-agents", scenario)
        self.assertIn("must fix", scenario)
        self.assertIn("should fix", scenario)
        self.assertIn("verdict", scenario)
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
            for track_id, envelope in (
                ("code-review", valid_code_review_envelope(attestation, checked_sha)),
                ("ponytail-review", valid_ponytail_review_envelope(attestation, checked_sha)),
            ):
                envelope_path = write(temp_dir, f"{track_id}.json", json.dumps(envelope))
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

    def test_skill_contract_and_scenario_define_failure_recovery_and_partial_mode(self):
        skill = " ".join(
            (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").lower().split()
        )
        for phrase in (
            "validate-run",
            "overall status blocked",
            "preserve every completed track report",
            "at most one recovery invocation",
            "deterministic digest of the frozen manifest",
            "new invocation id",
            "failed-attempt analysis",
            "save that json result as an external artifact",
            "separate follow-up run record",
            "approval.source",
            "missing track",
            "reduced independence",
            "never claim a complete parallel review",
            "independence_capability",
            "recovery_capability",
            "not run",
        ):
            self.assertIn(phrase, skill)

        contract = " ".join(
            (SKILL_ROOT / "references" / "contract.md")
            .read_text(encoding="utf-8")
            .lower()
            .split()
        )
        for phrase in (
            "coordinator run result",
            "complete` requires every routed track",
            "transient_runtime",
            "transient_transport",
            "analysis_reused",
            "transient failure evidence has exactly",
            "same derived `request_sha256`",
            "its exact bytes must match `sha256`",
            "partial mode is never a complete parallel review",
            "coverage.status` remains a report fact separate from launch status",
        ):
            self.assertIn(phrase, contract)

        scenario = " ".join(
            (SKILL_ROOT / "references" / "acceptance-scenario.md")
            .read_text(encoding="utf-8")
            .lower()
            .split()
        )
        for phrase in (
            "successful two-track review",
            "required-track launch failure",
            "one bounded recovery",
            "explicit partial approval",
            "coverage is not launch failure",
            "distinct request hash derived from each track identity",
            "artifact by relative path and exact sha-256",
            "same-pass record is rejected",
            "not run",
            "static records",
            "not live evidence",
        ):
            self.assertIn(phrase, scenario)

    def test_remediation_change_stales_review_and_requires_a_new_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen, bundle = freeze_acceptance_bundle(temp_dir)
            self.assertEqual(frozen.returncode, 0, frozen.stderr or frozen.stdout)
            original_manifest = json.loads(
                (bundle / "manifest.json").read_text(encoding="utf-8")
            )
            original_patch = (
                SKILL_ROOT / "references" / "acceptance-fixture.patch"
            ).read_bytes()
            remediated_bytes = original_patch.replace(
                b'Decimal("0.9")',
                b'Decimal("0.90")',
            )
            self.assertNotEqual(original_patch, remediated_bytes)
            remediated_patch = Path(temp_dir) / "remediated.patch"
            remediated_patch.write_bytes(remediated_bytes)
            remediated_tree = Path(temp_dir) / "remediated-tree"
            shutil.copytree(
                SKILL_ROOT / "references" / "acceptance-tree",
                remediated_tree,
            )
            remediated_source = remediated_tree / "src" / "discounts.py"
            remediated_source.write_text(
                remediated_source.read_text(encoding="utf-8").replace(
                    'Decimal("0.9")',
                    'Decimal("0.90")',
                ),
                encoding="utf-8",
            )
            stale = run_contract(
                "verify",
                "--bundle",
                bundle,
                "--patch",
                remediated_patch,
                *contract_args(),
            )
            new_bundle = Path(temp_dir) / "remediated-bundle"
            refreshed = run_contract(
                "freeze",
                "--output",
                new_bundle,
                "--patch",
                remediated_patch,
                "--tree-root",
                remediated_tree,
                "--requirements",
                SKILL_ROOT / "references" / "acceptance-requirements.md",
                "--standards",
                SKILL_ROOT / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                *contract_args(),
            )
            refreshed_manifest = json.loads(
                (new_bundle / "manifest.json").read_text(encoding="utf-8")
            )
            refreshed_manifest_sha256 = hashlib.sha256(
                (new_bundle / "manifest.json").read_bytes()
            ).hexdigest()
            refreshed_checked_sha = refreshed_manifest["scope"][
                "tree_sources"
            ][0]["sha256"]
            refreshed_attestation = json.loads(
                (new_bundle / "attestation.json").read_text(encoding="utf-8")
            )
            refreshed_envelopes = [
                valid_code_review_envelope(
                    refreshed_attestation,
                    refreshed_checked_sha,
                ),
                valid_ponytail_review_envelope(
                    refreshed_attestation,
                    refreshed_checked_sha,
                ),
            ]
            refreshed_attempts = []
            for track_id, envelope in zip(
                ("code-review", "ponytail-review"),
                refreshed_envelopes,
            ):
                envelope_path = write(
                    temp_dir,
                    f"refreshed-{track_id}.json",
                    json.dumps(envelope),
                )
                refreshed_attempts.append(
                    run_attempt(
                        envelope["invocation_id"],
                        track_request_sha256(
                            refreshed_manifest,
                            refreshed_attestation,
                            track_id,
                        ),
                        envelope=envelope_path.name,
                    )
                )
            refreshed_run = review_run(
                [refreshed_attempts[0]],
                [refreshed_attempts[1]],
                checks=[
                    {
                        "name": "independence_capability",
                        "result": "passed",
                        "reason": "Synthetic fixture records independence as passed.",
                    }
                ],
            )
            refreshed_run_path = write(
                temp_dir,
                "refreshed-run.json",
                json.dumps(refreshed_run),
            )
            refreshed_validation = run_contract(
                "validate-run",
                "--bundle",
                new_bundle,
                "--run",
                refreshed_run_path,
                "--patch",
                remediated_patch,
                *contract_args(),
            )
            refreshed_result = result_json(refreshed_validation)

        self.assertEqual(1, stale.returncode)
        stale_result = result_json(stale)
        self.assertEqual("stale", stale_result["status"])
        self.assertIn(
            "The explicit patch changed after the freeze.",
            stale_result["reasons"],
        )
        self.assertEqual(
            refreshed.returncode,
            0,
            refreshed.stderr or refreshed.stdout,
        )
        self.assertNotEqual(
            original_manifest["scope"]["patch"]["sha256"],
            refreshed_manifest["scope"]["patch"]["sha256"],
        )
        self.assertEqual(
            ["code-review", "ponytail-review"],
            [
                track["track_id"]
                for track in refreshed_manifest["contract"]["tracks"]
            ],
        )
        self.assertEqual(
            refreshed_validation.returncode,
            0,
            refreshed_validation.stderr or refreshed_validation.stdout,
        )
        self.assertEqual("complete", refreshed_result["status"])
        self.assertEqual(
            refreshed_envelopes,
            refreshed_result["completed_reports"],
        )
        for envelope in refreshed_result["completed_reports"]:
            self.assertEqual(
                refreshed_attestation["manifest_sha256"],
                envelope["attestation"]["manifest_sha256"],
            )
        self.assertEqual(
            refreshed_manifest_sha256,
            refreshed_attestation["manifest_sha256"],
        )

    def test_third_track_extension_needs_one_adapter_and_one_routing_row(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / "skill"
            shutil.copytree(SKILL_ROOT, skill_root)
            common_paths = (
                "SKILL.md",
                "references/contract.md",
                "references/acceptance-scenario.md",
                "scripts/review_contract.py",
            )
            common_before = {
                path: (skill_root / path).read_bytes()
                for path in common_paths
            }
            third_adapter = write_adapter(
                skill_root,
                "third-review.md",
                metadata(
                    "/third-review",
                    source="<third-review-publisher-source>",
                    inputs=[
                        "patch",
                        "tree",
                        "requirements",
                        "standards",
                        "checks",
                        "exclusions",
                    ],
                ),
                extra=(
                    "\nReturn the same frozen-scope evidence in the common "
                    "envelope. This disposable adapter is acceptance-test "
                    "data, not a live reviewer.\n"
                ),
            )
            routing = write_routing(
                skill_root,
                [
                    ("code-review", "references/tracks/code-review.md"),
                    ("ponytail-review", "references/tracks/ponytail-review.md"),
                    ("third-review", "references/tracks/third-review.md"),
                ],
            )
            self.assertTrue(third_adapter.is_file())
            self.assertIn(
                "| third-review | references/tracks/third-review.md |",
                routing.read_text(encoding="utf-8"),
            )
            common_after = {
                path: (skill_root / path).read_bytes()
                for path in common_paths
            }
            self.assertEqual(common_before, common_after)

            upstreams = [
                "--upstream",
                f"/code-review={UPSTREAM_SOURCE}",
                "--upstream",
                f"/ponytail-review={skill_root / 'references/tracks/ponytail-review.md'}",
                "--upstream",
                f"/third-review={UPSTREAM_SOURCE}",
            ]
            preflight = run_contract(
                "preflight",
                "--skill-root",
                skill_root,
                *upstreams,
            )
            self.assertEqual(
                preflight.returncode,
                0,
                preflight.stderr or preflight.stdout,
            )
            preflight_result = result_json(preflight)
            expected_order = [
                "code-review",
                "ponytail-review",
                "third-review",
            ]
            self.assertEqual(
                expected_order,
                [track["track_id"] for track in preflight_result["tracks"]],
            )
            self.assertEqual(
                expected_order,
                [
                    pin["track_id"]
                    for pin in preflight_result["pins"]["adapters"]
                ],
            )

            bundle = Path(temp_dir) / "bundle"
            frozen = run_contract(
                "freeze",
                "--output",
                bundle,
                "--patch",
                skill_root / "references" / "acceptance-fixture.patch",
                "--tree-root",
                skill_root / "references" / "acceptance-tree",
                "--requirements",
                skill_root / "references" / "acceptance-requirements.md",
                "--standards",
                skill_root / "references" / "acceptance-standard.md",
                "--not-run",
                "repository tests=Synthetic patch is review-only.",
                "--contract-root",
                skill_root,
                *upstreams,
            )
            self.assertEqual(
                frozen.returncode,
                0,
                frozen.stderr or frozen.stdout,
            )
            manifest = json.loads(
                (bundle / "manifest.json").read_text(encoding="utf-8")
            )
            checked_sha = manifest["scope"]["tree_sources"][0]["sha256"]
            attestation = json.loads(
                (bundle / "attestation.json").read_text(encoding="utf-8")
            )
            envelopes = {
                "code-review": valid_code_review_envelope(
                    attestation,
                    checked_sha,
                ),
                "ponytail-review": valid_ponytail_review_envelope(
                    attestation,
                    checked_sha,
                ),
                "third-review": valid_third_review_envelope(
                    attestation,
                    checked_sha,
                ),
            }
            attempts = {}
            for track_id, envelope in envelopes.items():
                envelope_path = write(
                    temp_dir,
                    f"{track_id}.json",
                    json.dumps(envelope),
                )
                attempts[track_id] = run_attempt(
                    envelope["invocation_id"],
                    track_request_sha256(manifest, attestation, track_id),
                    envelope=envelope_path.name,
                )
            run = {
                "contract_version": 1,
                "tracks": [
                    {"track_id": track_id, "attempts": [attempts[track_id]]}
                    for track_id in reversed(expected_order)
                ],
                "checks": [
                    {
                        "name": "independence_capability",
                        "result": "passed",
                        "reason": (
                            "Synthetic acceptance fixture records independence "
                            "as passed."
                        ),
                    }
                ],
                "partial": None,
            }
            run_path = write(temp_dir, "third-track-run.json", json.dumps(run))
            completed = run_contract(
                "validate-run",
                "--bundle",
                bundle,
                "--run",
                run_path,
                "--patch",
                skill_root / "references" / "acceptance-fixture.patch",
                "--contract-root",
                skill_root,
                *upstreams,
            )

        self.assertEqual(
            completed.returncode,
            0,
            completed.stderr or completed.stdout,
        )
        result = result_json(completed)
        self.assertEqual("complete", result["status"])
        self.assertEqual(
            expected_order,
            [track["track_id"] for track in result["tracks"]],
        )
        self.assertEqual(
            [envelopes[track_id] for track_id in expected_order],
            result["completed_reports"],
        )
        rendered = result["rendered"]
        positions = [
            rendered.index(f"## Track report: `{track_id}`")
            for track_id in expected_order
        ]
        self.assertEqual(positions, sorted(positions))

    def test_acceptance_package_covers_spec_loop_seam_and_root_exception(self):
        scenario = " ".join(
            (SKILL_ROOT / "references" / "acceptance-scenario.md")
            .read_text(encoding="utf-8")
            .lower()
            .split()
        )
        for phrase in (
            "remediation code change",
            "new freeze",
            "rerun every routed track",
            "separate per-root exception",
            "confirmed append-only record",
            "root status synchronization",
            "root completion checkpoint",
            "one third-track adapter",
            "one routing-table row",
            "no common dispatch",
            "`/spec-implement-loop` caller seam",
            "exactly once",
            "ticket review remains on `/code-review`",
            "every complete track report",
            "unchanged",
            "live caller",
            "not run",
        ):
            self.assertIn(phrase, scenario)
        for field in (
            "starting oid",
            "final oid",
            "manifest digest",
            "scope digest",
            "blocked result path and sha-256",
            "root-exception approval source and evidence",
        ):
            self.assertIn(field, scenario)
        approval_order = (
            "show the proposed exception",
            "obtain the separate per-root exception approval",
            "add only its exact root-exception approval source and evidence",
            "freeze and show the final append-only comment series",
            "separate issue-comment write approval",
        )
        positions = [scenario.index(phrase) for phrase in approval_order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn(
            "<third-review-publisher-source>",
            scenario,
        )

        spec = (
            ROOT / "skills" / "spec-implement-loop" / "SKILL.md"
        ).read_text(encoding="utf-8").lower()
        self.assertIn(
            "ticket review remains on this `/code-review` path",
            spec,
        )
        self.assertIn(
            "call `/parallel-code-review` exactly once",
            spec,
        )
        self.assertIn(
            "hand every current complete track report unchanged",
            spec,
        )
        self.assertIn("separate per-root user exception", spec)
        self.assertIn("complete append-only record", spec)
        self.assertIn("root completion checkpoint remains mandatory", spec)

    def test_readme_lists_the_new_skill(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "[parallel-code-review](skills/parallel-code-review/SKILL.md)",
            readme,
        )
        self.assertIn("`/code-review` and `/ponytail-review`", readme)
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
                "--patch",
                skill_copy / "references" / "acceptance-fixture.patch",
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
                "--patch",
                skill_copy / "references" / "acceptance-fixture.patch",
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
                        "--patch",
                        skill_copy / "references" / "acceptance-fixture.patch",
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
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
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
                "--patch",
                SKILL_ROOT / "references" / "acceptance-fixture.patch",
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
