import hashlib
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
        self.original = b"Original document with enough prose to shorten.\n"
        self.candidate = b"Shorter prose.\n"
        self.source.write_bytes(self.original)
        self.expected_hash = hashlib.sha256(self.original).hexdigest()

    def apply_candidate(self):
        return apply_candidate.apply_candidate(
            self.source, self.expected_hash, self.candidate
        )

    def test_success_keeps_exact_backup_and_replaces_source(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_DIR / "apply_candidate.py"),
                str(self.source),
                self.expected_hash,
            ],
            input=self.candidate,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        result = json.loads(completed.stdout)

        self.assertEqual(result["status"], "applied")
        self.assertEqual(self.source.read_bytes(), self.candidate)
        self.assertEqual(Path(result["backup_path"]).read_bytes(), self.original)

    def test_changed_source_is_left_alone_before_backup(self):
        changed = b"Changed by another writer.\n"
        self.source.write_bytes(changed)

        result = self.apply_candidate()

        self.assertEqual(result["status"], "not_applied")
        self.assertEqual(self.source.read_bytes(), changed)
        self.assertFalse(Path(f"{self.source}.original.md").exists())

    def test_conflicting_backup_and_source_are_left_alone(self):
        backup = Path(f"{self.source}.original.md")
        backup.write_bytes(b"Different backup.\n")

        result = self.apply_candidate()

        self.assertEqual(result["status"], "not_applied")
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(backup.read_bytes(), b"Different backup.\n")

    def test_matching_backup_is_reused(self):
        backup = Path(f"{self.source}.original.md")
        backup.write_bytes(self.original)

        result = self.apply_candidate()

        self.assertEqual(result["status"], "applied")
        self.assertEqual(Path(result["backup_path"]).read_bytes(), self.original)

    def test_staging_failure_keeps_source_and_verified_backup(self):
        with patch.object(apply_candidate.tempfile, "mkstemp", side_effect=OSError("stage failed")):
            result = self.apply_candidate()

        self.assertEqual(result["status"], "not_applied")
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(Path(result["backup_path"]).read_bytes(), self.original)

    def test_source_changed_after_backup_is_not_replaced(self):
        changed = b"Changed after the verified backup.\n"
        real_mkstemp = apply_candidate.tempfile.mkstemp

        def change_source_before_staging(*args, **kwargs):
            self.source.write_bytes(changed)
            return real_mkstemp(*args, **kwargs)

        with patch.object(
            apply_candidate.tempfile,
            "mkstemp",
            side_effect=change_source_before_staging,
        ):
            result = self.apply_candidate()

        self.assertEqual(result["status"], "not_applied")
        self.assertEqual(self.source.read_bytes(), changed)
        self.assertEqual(Path(result["backup_path"]).read_bytes(), self.original)

    def test_replace_error_is_unknown_and_does_not_roll_back(self):
        real_replace = apply_candidate.os.replace

        def replace_then_report_error(staged, source):
            real_replace(staged, source)
            raise OSError("replace reported an error after applying")

        with patch.object(apply_candidate.os, "replace", side_effect=replace_then_report_error):
            result = self.apply_candidate()

        self.assertEqual(result["status"], "replacement_unknown")
        self.assertEqual(self.source.read_bytes(), self.candidate)
        self.assertEqual(Path(result["backup_path"]).read_bytes(), self.original)

    def test_one_file_failure_does_not_undo_another_file(self):
        other = Path(self.temp_dir.name) / "other.md"
        other_original = b"Another document with enough prose to shorten.\n"
        other.write_bytes(other_original)
        other_backup = Path(f"{other}.original.md")
        other_backup.write_bytes(b"Conflicting backup.\n")

        first = apply_candidate.apply_candidate(
            self.source, self.expected_hash, self.candidate
        )
        second = apply_candidate.apply_candidate(
            other, hashlib.sha256(other_original).hexdigest(), self.candidate
        )

        self.assertEqual(first["status"], "applied")
        self.assertEqual(second["status"], "not_applied")
        self.assertEqual(self.source.read_bytes(), self.candidate)
        self.assertEqual(other.read_bytes(), other_original)


if __name__ == "__main__":
    unittest.main()
