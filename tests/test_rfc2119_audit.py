"""Public CLI contracts for the read-only RFC 2119 audit."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    KERNEL32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    KERNEL32.CreateFileW.restype = wintypes.HANDLE


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "skills" / "rfc2119-audit" / "scripts" / "audit_rfc2119.py"


def run_audit(*args, cwd=ROOT):
    return subprocess.run(
        [sys.executable, str(AUDIT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def snapshot_tree(root: Path):
    snapshot = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot.append((relative, "symlink", str(path.readlink())))
        elif path.is_file():
            snapshot.append((relative, "file", path.read_bytes()))
        elif path.is_dir():
            snapshot.append((relative, "directory", b""))
    return snapshot


class Rfc2119AuditCliTests(unittest.TestCase):
    def test_root_is_required_and_has_no_default(self):
        completed = run_audit()

        self.assertEqual(2, completed.returncode)
        self.assertIn("--root", completed.stderr)
        self.assertEqual("", completed.stdout)

    def test_relative_root_reports_a_candidate_without_modifying_input(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            source = root / "notes.md"
            original = b"The operator must continue.\n"
            source.write_bytes(original)
            before_entries = sorted(path.name for path in root.iterdir())

            completed = run_audit("--root", ".", cwd=root)

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "notes.md:1: lowercase requirement word: The operator must continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )
            self.assertEqual("", completed.stderr)
            self.assertEqual(original, source.read_bytes())
            self.assertEqual(before_entries, sorted(path.name for path in root.iterdir()))

    def test_candidate_categories_and_precedence_follow_the_fixed_sets(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "prose.md").write_text(
                "The operator must continue.\n"
                "The operator don't continue.\n"
                "Continue reading.\n"
                "The operator MUST continue.\n"
                "Browse the index.\n"
                "The operator must not skip.\n"
                "The operator has a musty smell.\n"
                "Do not continue.\n",
                encoding="utf-8",
            )

            normal = run_audit("--root", str(root))
            strict = run_audit("--root", str(root), "--strict")

            expected = [
                "prose.md:1: lowercase requirement word: The operator must continue.",
                "prose.md:2: unmarked prohibition: The operator don't continue.",
                "prose.md:3: unmarked imperative: Continue reading.",
                "prose.md:6: lowercase requirement word: The operator must not skip.",
                "prose.md:8: unmarked prohibition: Do not continue.",
                "RFC 2119 candidate audit: 5 candidate(s) in 1 Markdown files.",
            ]
            self.assertEqual(0, normal.returncode, normal.stderr)
            self.assertEqual(expected, normal.stdout.splitlines())
            self.assertEqual(1, strict.returncode, strict.stderr)
            self.assertEqual(normal.stdout, strict.stdout)

    def test_recursive_discovery_is_deterministic_and_uses_posix_locations(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "nested").mkdir()
            (root / "nested" / "b.md").write_text("Continue.\n", encoding="utf-8")
            (root / "a.md").write_text("Continue.\n", encoding="utf-8")
            (root / "z.md").write_text("Continue.\n", encoding="utf-8")

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "a.md:1: unmarked imperative: Continue.",
                    "nested/b.md:1: unmarked imperative: Continue.",
                    "z.md:1: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 3 candidate(s) in 3 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_empty_and_candidate_free_roots_have_explicit_success_messages(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)

            empty = run_audit("--root", str(root), "--strict")
            (root / "clean.md").write_text(
                "The operator MUST continue.\n", encoding="utf-8"
            )
            clean = run_audit("--root", str(root), "--strict")

            self.assertEqual(0, empty.returncode, empty.stderr)
            self.assertEqual(
                "RFC 2119 candidate audit: 0 files scanned; no candidates found.\n",
                empty.stdout,
            )
            self.assertEqual(0, clean.returncode, clean.stderr)
            self.assertEqual(
                "RFC 2119 candidate audit: no candidates found "
                "in 1 Markdown files.\n",
                clean.stdout,
            )

    def test_missing_and_non_directory_roots_fail_without_candidate_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_root = Path(temp_dir)
            missing = temp_root / "missing"
            regular_file = temp_root / "not-a-directory.md"
            regular_file.write_text("Continue.\n", encoding="utf-8")

            for root in (missing, regular_file):
                with self.subTest(root=root.name):
                    completed = run_audit("--root", str(root))
                    self.assertEqual(2, completed.returncode)
                    self.assertEqual("", completed.stdout)
                    self.assertNotEqual("", completed.stderr)

    def test_invalid_utf8_fails_closed_without_a_partial_report(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "a-good.md").write_text("Continue.\n", encoding="utf-8")
            invalid = root / "z-bad.md"
            original = b"\xff\xfe\x00bad bytes\n"
            invalid.write_bytes(original)
            before = snapshot_tree(root)

            completed = run_audit("--root", str(root))

            self.assertEqual(2, completed.returncode)
            self.assertEqual("", completed.stdout)
            self.assertIn("z-bad.md", completed.stderr)
            self.assertIn("utf-8", completed.stderr.lower())
            self.assertEqual(original, invalid.read_bytes())
            self.assertEqual(before, snapshot_tree(root))

    def test_markdown_symlink_fails_without_reading_the_target(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            base = Path(temp_dir)
            root = base / "root"
            root.mkdir()
            target = base / "target.txt"
            target.write_text("Continue.\n", encoding="utf-8")
            linked = root / "linked.md"
            try:
                linked.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            before = snapshot_tree(root)

            completed = run_audit("--root", str(root))

            self.assertEqual(2, completed.returncode)
            self.assertEqual("", completed.stdout)
            self.assertIn("linked.md", completed.stderr)
            self.assertIn("symlink", completed.stderr.lower())
            self.assertEqual(before, snapshot_tree(root))

    def test_nested_symlink_directories_are_not_traversed(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            base = Path(temp_dir)
            root = base / "root"
            root.mkdir()
            outside = base / "outside"
            outside.mkdir()
            (outside / "hidden.md").write_text("Continue.\n", encoding="utf-8")
            try:
                (root / "linked-dir").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            before = snapshot_tree(root)

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                "RFC 2119 candidate audit: 0 files scanned; no candidates found.\n",
                completed.stdout,
            )
            self.assertEqual(before, snapshot_tree(root))

    def test_non_regular_markdown_entry_fails_as_an_operational_error(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "blocked.md").mkdir()
            before = snapshot_tree(root)

            completed = run_audit("--root", str(root))

            self.assertEqual(2, completed.returncode)
            self.assertEqual("", completed.stdout)
            self.assertIn("blocked.md", completed.stderr)
            self.assertEqual(before, snapshot_tree(root))

    @unittest.skipUnless(sys.platform == "win32", "Windows exclusive-file setup")
    def test_read_failure_fails_closed_without_a_partial_report(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            source = root / "locked.md"
            source.write_text("Continue.\n", encoding="utf-8")
            before = snapshot_tree(root)
            handle = KERNEL32.CreateFileW(
                str(source),
                0x80000000,
                0,
                None,
                3,
                0,
                None,
            )
            self.assertNotEqual(wintypes.HANDLE(-1).value, handle)
            try:
                completed = run_audit("--root", str(root))
            finally:
                KERNEL32.CloseHandle(handle)

            self.assertEqual(2, completed.returncode)
            self.assertEqual("", completed.stdout)
            self.assertIn("locked.md", completed.stderr)
            self.assertIn("cannot read", completed.stderr.lower())
            self.assertEqual(before, snapshot_tree(root))


if __name__ == "__main__":
    unittest.main()
