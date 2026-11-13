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

    def test_unicode_candidates_are_reported_as_utf8(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "unicode.md").write_text(
                "Continue 😀.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "unicode.md:1: unmarked imperative: Continue 😀.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

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

    def test_frontmatter_headings_quotes_indented_code_and_inline_code_are_excluded(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "contexts.md").write_text(
                "---\n"
                "must: Continue.\n"
                "---\n"
                "# Continue.\n"
                "> Continue.\n"
                "    Continue.\n"
                "Prose with `MUST` and must continue.\n"
                "Prose with `must` only.\n"
                "Prose with ``must`` only.\n",
                encoding="utf-8",
            )
            (root / "inline-spans.md").write_text(
                "The operator uses `must\n"
                "continue` safely.\n"
                "Continue.\n",
                encoding="utf-8",
            )
            (root / "unclosed-inline.md").write_text(
                "`must continue.\n"
                "The operator must continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "contexts.md:7: lowercase requirement word: "
                    "Prose with `MUST` and must continue.",
                    "inline-spans.md:3: unmarked imperative: Continue.",
                    "unclosed-inline.md:1: lowercase requirement word: "
                    "`must continue.",
                    "unclosed-inline.md:2: lowercase requirement word: "
                    "The operator must continue.",
                    "RFC 2119 candidate audit: 4 candidate(s) in 3 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_all_fences_are_excluded_and_unclosed_fences_extend_to_eof(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "fences.md").write_text(
                "```python\n"
                "Continue.\n"
                "```\n"
                "~~~text\n"
                "Continue.\n"
                "~~~\n"
                "```unknown info\n"
                "Continue.\n"
                "```\n"
                "Continue after blocks.\n"
                "```text\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "fences.md:10: unmarked imperative: Continue after blocks.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_unclosed_tilde_fence_extends_to_eof(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "unclosed-tilde.md").write_text(
                "Continue before.\n"
                "~~~text\n"
                "Continue.\n"
                "The operator must continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "unclosed-tilde.md:1: unmarked imperative: Continue before.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_fence_markers_respect_indentation_and_html_comment_span(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "commented-fence.md").write_text(
                "<!--\n"
                "```\n"
                "-->\n"
                "The operator must continue.\n",
                encoding="utf-8",
            )
            (root / "indented-opener.md").write_text(
                "    ```\n"
                "Continue.\n",
                encoding="utf-8",
            )
            (root / "indented-closer.md").write_text(
                "```\n"
                "    ```\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "commented-fence.md:4: lowercase requirement word: "
                    "The operator must continue.",
                    "indented-opener.md:2: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 2 candidate(s) in 3 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_fenced_blocks_inside_list_items_are_excluded(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "list-fence.md").write_text(
                "- ```text\n"
                "  Continue.\n"
                "  ```\n"
                "Continue after the list.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "list-fence.md:4: unmarked imperative: "
                    "Continue after the list.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_overindented_list_fence_marker_does_not_hide_following_prose(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "pseudo-fence.md").write_text(
                "-     ```\n"
                "The operator must continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "pseudo-fence.md:2: lowercase requirement word: "
                    "The operator must continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_list_fence_closers_allow_container_indentation(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "list-fence.md").write_text(
                "- ```text\n"
                "    Continue.\n"
                "    ```\n"
                "Continue after the list.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "list-fence.md:4: unmarked imperative: "
                    "Continue after the list.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_list_continuation_fence_ignores_content_and_resumes_after_close(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "list-continuation-fence.md").write_text(
                "- item\n"
                "\n"
                "    ```\n"
                "  must continue.\n"
                "    ```\n"
                "\n"
                "Continue after list.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "list-continuation-fence.md:7: unmarked imperative: "
                    "Continue after list.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_list_fence_close_uses_container_relative_indent(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "list-fence-close.md").write_text(
                "\n"
                "- item\n"
                "  ```\n"
                "  must continue.\n"
                "    ```\n"
                "\n"
                "Continue after list.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "list-fence-close.md:7: unmarked imperative: "
                    "Continue after list.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_nested_list_parent_fence_uses_active_container_stack(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "nested-list-fence.md").write_text(
                "\n"
                "- outer\n"
                "  - inner\n"
                "\n"
                "  ```\n"
                "  code\n"
                "     ```\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "nested-list-fence.md:8: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_dedented_list_fence_ends_before_paragraph(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "fence-dedent.md").write_text(
                "- outer\n"
                "  ```\n"
                "  must continue.\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "fence-dedent.md:4: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_dedented_list_fence_starts_new_top_level_fence(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "fence-restart.md").write_text(
                "- ```text\n"
                "  must continue.\n"
                "```\n"
                "Continue after.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "RFC 2119 candidate audit: no candidates found "
                    "in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_thematic_break_does_not_enter_list_stack(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "thematic-break.md").write_text(
                "- - -\n"
                "\n"
                "  ```\n"
                "  code\n"
                "    ```\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "RFC 2119 candidate audit: no candidates found "
                    "in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_thematic_break_pops_ended_list_containers(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "thematic-break-after-list.md").write_text(
                "- item\n"
                "- - -\n"
                "\n"
                "  ```\n"
                "  code\n"
                "    ```\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "RFC 2119 candidate audit: no candidates found "
                    "in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_empty_list_item_enters_container_stack(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "empty-list-item.md").write_text(
                "- outer\n"
                "-\n"
                "  ```\n"
                "  code\n"
                "    ```\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "empty-list-item.md:6: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_paragraph_bare_dash_is_a_setext_underline(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "setext.md").write_text(
                "Paragraph\n"
                "-\n"
                "  ```\n"
                "code\n"
                "  ```\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "setext.md:6: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_bare_dash_after_non_paragraph_blocks_starts_a_list(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "setext.md").write_text(
                "Heading\n"
                "-\n"
                "-\n"
                "  ```\n"
                "  hidden\n"
                "    ```\n"
                "Continue.\n",
                encoding="utf-8",
            )
            (root / "comment.md").write_text(
                "<!-- hidden\n"
                "-->\n"
                "-\n"
                "  ```\n"
                "  hidden\n"
                "    ```\n"
                "Continue.\n",
                encoding="utf-8",
            )
            (root / "single-comment.md").write_text(
                "<!-- hidden -->\n"
                "-\n"
                "  ```\n"
                "  hidden\n"
                "    ```\n"
                "Continue.\n",
                encoding="utf-8",
            )
            (root / "list-continuation.md").write_text(
                "- item\n"
                "\n"
                "  text\n"
                "-\n"
                "  ```\n"
                "  hidden\n"
                "    ```\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "comment.md:7: unmarked imperative: Continue.",
                    "list-continuation.md:8: unmarked imperative: Continue.",
                    "setext.md:7: unmarked imperative: Continue.",
                    "single-comment.md:6: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 4 candidate(s) in 4 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_list_continuation_before_empty_sibling_remains_auditable(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "list.md").write_text(
                "- item\n"
                "\n"
                "  Continue.\n"
                "-\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "list.md:3: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_html_comments_mask_only_their_span_and_unclosed_comments_extend_to_eof(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "comments.md").write_text(
                "Before <!-- Continue. --> The operator must continue.\n"
                "<!-- Continue. -->\n"
                "Before <!--\n"
                "Continue.\n"
                "--> The operator must continue.\n"
                "Continue after comment.\n"
                "<!--\n"
                "    -->\n"
                "The operator must continue.\n"
                "<!--\n"
                "    ```\n"
                "-->\n"
                "The operator must continue.\n"
                "<!--\n"
                "---\n"
                "The operator must continue.\n"
                "Before <!-- unclosed\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "comments.md:1: lowercase requirement word: "
                    "Before <!-- Continue. --> The operator must continue.",
                    "comments.md:5: lowercase requirement word: "
                    "--> The operator must continue.",
                    "comments.md:6: unmarked imperative: Continue after comment.",
                    "comments.md:9: lowercase requirement word: "
                    "The operator must continue.",
                    "comments.md:13: lowercase requirement word: "
                    "The operator must continue.",
                    "RFC 2119 candidate audit: 5 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_inline_code_and_comments_do_not_create_masked_structure(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "inline-code.md").write_text(
                "The operator uses `<!--` and must continue.\n"
                "Continue.\n",
                encoding="utf-8",
            )
            (root / "comment-close.md").write_text(
                "<!--\n"
                "--> Literal `<!--` token.\n"
                "The operator must continue.\n",
                encoding="utf-8",
            )
            (root / "masked-structure.md").write_text(
                "<!-- --> # The operator must continue.\n"
                "<!-- --> > The operator must continue.\n"
                "<!-- -->     The operator must continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "comment-close.md:3: lowercase requirement word: "
                    "The operator must continue.",
                    "inline-code.md:1: lowercase requirement word: "
                    "The operator uses `<!--` and must continue.",
                    "inline-code.md:2: unmarked imperative: Continue.",
                    "masked-structure.md:1: lowercase requirement word: "
                    "<!-- --> # The operator must continue.",
                    "masked-structure.md:2: lowercase requirement word: "
                    "<!-- --> > The operator must continue.",
                    "masked-structure.md:3: lowercase requirement word: "
                    "<!-- -->     The operator must continue.",
                    "RFC 2119 candidate audit: 6 candidate(s) in 3 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_multiline_inline_code_does_not_cross_comment_or_table_boundaries(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "comment-boundary.md").write_text(
                "Use `must\n"
                "<!-- hidden -->\n"
                "Continue.\n"
                "close` here.\n",
                encoding="utf-8",
            )
            (root / "table-boundary.md").write_text(
                "| `must | value |\n"
                "| --- | --- |\n"
                "| continue` | value |\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "comment-boundary.md:1: lowercase requirement word: "
                    "Use `must",
                    "comment-boundary.md:3: unmarked imperative: Continue.",
                    "table-boundary.md:1: lowercase requirement word: "
                    "| `must | value |",
                    "RFC 2119 candidate audit: 3 candidate(s) in 2 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_multiline_inline_code_stops_at_a_thematic_break(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "thematic-break.md").write_text(
                "`must\n"
                "***\n"
                "Continue`\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "thematic-break.md:1: lowercase requirement word: `must",
                    "thematic-break.md:3: unmarked imperative: Continue`",
                    "RFC 2119 candidate audit: 2 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_multiline_inline_code_allows_inline_comments(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "inline-comment.md").write_text(
                "`must\n"
                "prefix <!-- hidden --> Continue`\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "RFC 2119 candidate audit: no candidates found "
                    "in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_multiline_inline_code_closes_before_comment_and_table_boundaries(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "comment-after-close.md").write_text(
                "The operator uses `must\n"
                "continue` <!-- hidden -->\n"
                "Continue.\n",
                encoding="utf-8",
            )
            (root / "table-after-close.md").write_text(
                "The operator uses `must\n"
                "continue` | value\n"
                "--- | ---\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "comment-after-close.md:3: unmarked imperative: Continue.",
                    "table-after-close.md:4: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 2 candidate(s) in 2 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_bare_comment_closer_does_not_break_multiline_inline_code(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "bare-closer.md").write_text(
                "The operator uses `must\n"
                "--> continue` here.\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "bare-closer.md:3: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_container_indented_code_cannot_open_html_comments(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "list-code.md").write_text(
                "-     Continue.\n"
                "The operator must continue.\n"
                "-     <!--\n"
                "Continue.\n",
                encoding="utf-8",
            )
            (root / "quote-code.md").write_text(
                ">     <!--\n"
                "The operator must continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "list-code.md:2: lowercase requirement word: "
                    "The operator must continue.",
                    "list-code.md:4: unmarked imperative: Continue.",
                    "quote-code.md:2: lowercase requirement word: "
                    "The operator must continue.",
                    "RFC 2119 candidate audit: 3 candidate(s) in 2 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_escaped_comment_openers_and_nested_container_code_are_literal(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "escaped-comment.md").write_text(
                r"Literal \<!-- token." + "\n"
                "Continue.\n",
                encoding="utf-8",
            )
            (root / "nested-code.md").write_text(
                "> -     <!--\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "escaped-comment.md:2: unmarked imperative: Continue.",
                    "nested-code.md:2: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 2 candidate(s) in 2 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_escaped_backtick_is_not_an_inline_code_opener(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "backticks.md").write_text(
                r"The operator uses \`must\` here." + "\n"
                "The operator uses `must\\` here.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "backticks.md:1: lowercase requirement word: "
                    r"The operator uses \`must\` here.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_escaped_first_backtick_leaves_remaining_run_as_opener(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "escaped-run.md").write_text(
                r"The operator uses \``must` here." + "\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "RFC 2119 candidate audit: no candidates found "
                    "in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_prose_after_multiline_comment_close_remains_auditable(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "comment-close.md").write_text(
                "<!--\n"
                "> --> The operator must continue.\n"
                "<!--\n"
                "# --> The operator should continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "comment-close.md:2: lowercase requirement word: "
                    "> --> The operator must continue.",
                    "comment-close.md:4: lowercase requirement word: "
                    "# --> The operator should continue.",
                    "RFC 2119 candidate audit: 2 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_comment_masking_precedes_setext_heading_detection(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "commented-underline.md").write_text(
                "Continue. <!--\n"
                "---\n"
                "-->\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "commented-underline.md:1: unmarked imperative: "
                    "Continue. <!--",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_headings_and_block_quotes_in_list_items_are_excluded(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "list-structure.md").write_text(
                "- # The operator must continue.\n"
                "- > The operator should continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "RFC 2119 candidate audit: no candidates found "
                    "in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_backtick_fence_info_rejects_backticks(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "fence-info.md").write_text(
                "``` invalid `info\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "fence-info.md:2: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_tables_and_removed_suppressors_follow_the_conservative_policy(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "contexts.md").write_text(
                "| Continue | Label |\n"
                "| --- | --- |\n"
                "| The operator must continue. | value |\n"
                "| The operator don't continue. | value |\n"
                "| The operator MUST continue. | value |\n"
                "route: must continue.\n"
                "request: must continue.\n"
                "action: must continue.\n"
                "good: must continue.\n"
                "bad: must continue.\n",
                encoding="utf-8",
            )
            navigation_root = root / "source-code-navigation"
            navigation_root.mkdir()
            (navigation_root / "nested.md").write_text(
                "Continue.\n", encoding="utf-8"
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "contexts.md:3: lowercase requirement word: "
                    "| The operator must continue. | value |",
                    "contexts.md:4: unmarked prohibition: "
                    "| The operator don't continue. | value |",
                    "contexts.md:6: lowercase requirement word: route: must continue.",
                    "contexts.md:7: lowercase requirement word: request: must continue.",
                    "contexts.md:8: lowercase requirement word: action: must continue.",
                    "contexts.md:9: lowercase requirement word: good: must continue.",
                    "contexts.md:10: lowercase requirement word: bad: must continue.",
                    "source-code-navigation/nested.md:1: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 8 candidate(s) in 2 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_markdown_table_and_heading_structure_follow_the_rendered_blocks(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "table.md").write_text(
                "Continue | Label\n"
                "--- | ---\n"
                "The operator must continue. | value\n",
                encoding="utf-8",
            )
            (root / "headings.md").write_text(
                "# Continue.\n"
                "## The operator must continue.\n"
                "#must continue.\n"
                "Continue reading.\n"
                "=========\n"
                "The operator must continue.\n"
                "---\n",
                encoding="utf-8",
            )
            (root / "table-context.md").write_text(
                "# Heading | Label\n"
                "--- | ---\n"
                "Continue | text\n"
                "Continue reading <!-- | -->.\n"
                "--- | ---\n",
                encoding="utf-8",
            )
            (root / "indented-table.md").write_text(
                "    Continue | Label\n"
                "    --- | ---\n"
                "Continue after indented example.\n",
                encoding="utf-8",
            )
            (root / "table-boundaries.md").write_text(
                "| Header | Value |\n"
                "| --- | --- |\n"
                "- Continue | value\n"
                "Continue | Label\n"
                "--- | --- | ---\n",
                encoding="utf-8",
            )
            (root / "setext-list.md").write_text(
                "- Continue.\n"
                "---\n",
                encoding="utf-8",
            )
            (root / "heading-comment.md").write_text(
                "# Heading <!--\n"
                "The operator must continue.\n",
                encoding="utf-8",
            )
            (root / "malformed-table.md").write_text(
                "|\n"
                "--- | ---\n"
                "Continue after malformed table.\n",
                encoding="utf-8",
            )
            (root / "list-table.md").write_text(
                "- Continue | value\n"
                "--- | ---\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "headings.md:3: lowercase requirement word: #must continue.",
                    "indented-table.md:3: unmarked imperative: "
                    "Continue after indented example.",
                    "list-table.md:1: unmarked imperative: "
                    "- Continue | value",
                    "malformed-table.md:3: unmarked imperative: "
                    "Continue after malformed table.",
                    "setext-list.md:1: unmarked imperative: - Continue.",
                    "table-boundaries.md:3: unmarked imperative: "
                    "- Continue | value",
                    "table-boundaries.md:4: unmarked imperative: Continue | Label",
                    "table-context.md:3: unmarked imperative: Continue | text",
                    "table-context.md:4: unmarked imperative: "
                    "Continue reading <!-- | -->.",
                    "table.md:3: lowercase requirement word: "
                    "The operator must continue. | value",
                    "RFC 2119 candidate audit: 10 candidate(s) in 9 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_escaped_pipe_in_table_header_keeps_the_table_policy(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "escaped-pipe.md").write_text(
                "Continue \\| Label | Value\n"
                "--- | ---\n"
                "The operator must continue. | value\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "escaped-pipe.md:3: lowercase requirement word: "
                    "The operator must continue. | value",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_table_header_with_masked_last_cell_keeps_columns(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "masked-header.md").write_text(
                "Header | `x`\n"
                "--- | ---\n"
                "Continue | y\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "RFC 2119 candidate audit: no candidates found "
                    "in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_table_data_row_before_setext_underline_is_audited(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "table-setext.md").write_text(
                "| A | B |\n"
                "| --- | --- |\n"
                "| The operator must continue. | value |\n"
                "---\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "table-setext.md:3: lowercase requirement word: "
                    "| The operator must continue. | value |",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_table_pipe_limits_inline_code_across_leading_space_indents(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "table-boundaries.md").write_text(
                " | `must | value `closing |\n"
                " | --- | --- |\n"
                "\n"
                "  | `must | value `closing |\n"
                "  | --- | --- |\n"
                "\n"
                "   | `must | value `closing |\n"
                "   | --- | --- |\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "table-boundaries.md:1: lowercase requirement word: "
                    "| `must | value `closing |",
                    "table-boundaries.md:4: lowercase requirement word: "
                    "| `must | value `closing |",
                    "table-boundaries.md:7: lowercase requirement word: "
                    "| `must | value `closing |",
                    "RFC 2119 candidate audit: 3 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_one_column_table_body_suppresses_imperative_labels(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "one-column.md").write_text(
                "| Header |\n"
                "| --- |\n"
                "Continue\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "RFC 2119 candidate audit: no candidates found "
                    "in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_one_column_table_stops_at_supported_block_boundaries(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "fence.md").write_text(
                "| Header |\n"
                "| --- |\n"
                "```\n"
                "code\n"
                "```\n"
                "Continue after fence.\n",
                encoding="utf-8",
            )
            (root / "heading.md").write_text(
                "| Header |\n"
                "| --- |\n"
                "# Heading\n"
                "Continue after heading.\n",
                encoding="utf-8",
            )
            (root / "thematic-break.md").write_text(
                "| Header |\n"
                "| --- |\n"
                "***\n"
                "Continue after break.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "fence.md:6: unmarked imperative: Continue after fence.",
                    "heading.md:4: unmarked imperative: Continue after heading.",
                    "thematic-break.md:4: unmarked imperative: "
                    "Continue after break.",
                    "RFC 2119 candidate audit: 3 candidate(s) in 3 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_block_comment_ends_a_one_column_table(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "table-comment.md").write_text(
                "| Header |\n"
                "| --- |\n"
                "<!-- hidden -->\n"
                "Continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "table-comment.md:4: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_setext_headings_inside_list_items_are_excluded(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "list-heading.md").write_text(
                "- The operator must continue.\n"
                "  =========\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "RFC 2119 candidate audit: no candidates found "
                    "in 1 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_packaged_skill_passes_its_own_strict_audit(self):
        completed = run_audit(
            "--root",
            str(ROOT / "skills" / "rfc2119-audit"),
            "--strict",
        )

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("no candidates found", completed.stdout)
        self.assertEqual("", completed.stderr)

    def test_frontmatter_only_starts_at_file_start_and_unclosed_frontmatter_extends_to_eof(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "late-delimiter.md").write_text(
                "Intro.\n---\nContinue.\n",
                encoding="utf-8",
            )
            (root / "unclosed-frontmatter.md").write_text(
                "---\nContinue.\nmust continue.\n",
                encoding="utf-8",
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "late-delimiter.md:3: unmarked imperative: Continue.",
                    "RFC 2119 candidate audit: 1 candidate(s) in 2 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )

    def test_frontmatter_requires_column_zero_and_accepts_a_utf8_bom(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / "indented.md").write_text(
                "    ---\n"
                "must continue.\n",
                encoding="utf-8",
            )
            (root / "bom.md").write_bytes(
                b"\xef\xbb\xbf---\n"
                b"must continue.\n"
                b"---\n"
                b"Continue.\n"
            )

            completed = run_audit("--root", str(root))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    "bom.md:4: unmarked imperative: Continue.",
                    "indented.md:2: lowercase requirement word: must continue.",
                    "RFC 2119 candidate audit: 2 candidate(s) in 2 Markdown files.",
                ],
                completed.stdout.splitlines(),
            )


if __name__ == "__main__":
    unittest.main()
