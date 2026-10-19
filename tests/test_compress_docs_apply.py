import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "compress-docs" / "scripts"
WORKTREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import apply_candidate


class ApplyCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir=WORKTREE)
        self.addCleanup(self.temp_dir.cleanup)
        self.source = Path(self.temp_dir.name) / "notes with spaces.md"
        self.backup = Path(f"{self.source}.original.md")
        self.original = b"Original document with enough prose to shorten.\n"
        self.candidate = b"Shorter prose.\n"
        self.source.write_bytes(self.original)

    def apply_candidate(self):
        return apply_candidate.apply_candidate(
            self.source, "unused-version-token", self.candidate
        )

    def test_local_path_is_rejected_before_reading_or_writing(self):
        with patch.object(Path, "read_bytes", side_effect=AssertionError("read source")):
            result = self.apply_candidate()

        self.assertEqual(result["status"], "not_applied")
        self.assertEqual(result["reason"], "conditional_replace_unsupported")
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(self.backup.exists())
        self.assertEqual(list(Path(self.temp_dir.name).iterdir()), [self.source])

    def test_cli_reports_local_path_rejection_without_modifying_files(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_DIR / "apply_candidate.py"),
                str(self.source),
                "unused-version-token",
            ],
            input=self.candidate,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "not_applied")
        self.assertEqual(result["reason"], "conditional_replace_unsupported")
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(self.backup.exists())

    def test_conflicting_backup_is_left_untouched(self):
        self.backup.write_bytes(b"Existing backup.\n")

        result = self.apply_candidate()

        self.assertEqual(result["status"], "not_applied")
        self.assertEqual(result["reason"], "conditional_replace_unsupported")
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(self.backup.read_bytes(), b"Existing backup.\n")


if __name__ == "__main__":
    unittest.main()
