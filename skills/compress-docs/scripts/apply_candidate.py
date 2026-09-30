import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path


def _apply_result(status, backup=None, reason=None):
    result = {"status": status}
    if backup is not None:
        result["backup_path"] = str(backup)
    if reason:
        result["reason"] = reason
    return result


def _within_approved_root(source, approved_root):
    try:
        source_path = os.path.normcase(os.path.abspath(source))
        root_path = os.path.normcase(os.path.abspath(approved_root))
        resolved_source = os.path.normcase(str(Path(source).resolve(strict=True)))
        resolved_root = os.path.normcase(str(Path(approved_root).resolve(strict=True)))
        return (
            resolved_source == source_path
            and resolved_root == root_path
            and os.path.commonpath((root_path, source_path)) == root_path
            and Path(approved_root).is_dir()
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def apply_candidate(source_path, expected_sha256, candidate, approved_root=None):
    source = Path(source_path)
    backup = Path(f"{source}.original.md")
    staged = None
    backup_verified = False

    try:
        def root_is_valid():
            return approved_root is None or _within_approved_root(source, approved_root)

        if not root_is_valid():
            return _apply_result("not_applied", reason="outside_approved_root")
        if source.is_symlink() or not source.is_file():
            return _apply_result("not_applied", reason="source_not_regular_file")

        original = source.read_bytes()
        if hashlib.sha256(original).hexdigest() != expected_sha256:
            return _apply_result("not_applied", reason="source_changed")
        if not candidate or len(candidate) >= len(original):
            return _apply_result("not_applied", reason="candidate_not_shorter")

        if not root_is_valid():
            return _apply_result("not_applied", reason="outside_approved_root")
        if not backup.exists():
            if not root_is_valid():
                return _apply_result("not_applied", reason="outside_approved_root")
            try:
                with backup.open("xb") as stream:
                    stream.write(original)
            except FileExistsError:
                pass
        if backup.is_symlink() or not backup.is_file() or backup.read_bytes() != original:
            return _apply_result("not_applied", backup=backup, reason="backup_conflict")
        backup_verified = True

        if not root_is_valid():
            return _apply_result("not_applied", backup=backup, reason="outside_approved_root")
        descriptor, staged_name = tempfile.mkstemp(
            prefix=f".{source.name}.", suffix=".tmp", dir=source.parent
        )
        staged = Path(staged_name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(candidate)
        if staged.read_bytes() != candidate:
            return _apply_result("not_applied", backup=backup, reason="staging_verification_failed")

        os.chmod(staged, stat.S_IMODE(source.stat().st_mode))
        root_valid = root_is_valid()
        if not root_valid or source.is_symlink() or not source.is_file() or source.read_bytes() != original:
            reason = "outside_approved_root" if not root_valid else "source_changed"
            return _apply_result("not_applied", backup=backup, reason=reason)

        if not root_is_valid():
            return _apply_result("not_applied", backup=backup, reason="outside_approved_root")
        try:
            os.replace(staged, source)
        except OSError:
            return _apply_result("replacement_unknown", backup=backup)

        staged = None
        return _apply_result("applied", backup=backup)
    except (OSError, ValueError, TypeError) as error:
        return _apply_result(
            "not_applied",
            backup=backup if backup_verified or backup.exists() or backup.is_symlink() else None,
            reason=type(error).__name__,
        )
    finally:
        if staged is not None:
            try:
                if approved_root is None or _within_approved_root(staged, approved_root):
                    staged.unlink(missing_ok=True)
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description="Apply a validated shorter document candidate.")
    parser.add_argument("source")
    parser.add_argument("expected_sha256")
    parser.add_argument("--approved-root")
    args = parser.parse_args()

    result = apply_candidate(
        args.source,
        args.expected_sha256,
        sys.stdin.buffer.read(),
        approved_root=args.approved_root,
    )
    print(json.dumps(result))
    return {"applied": 0, "not_applied": 1, "replacement_unknown": 2}[result["status"]]


if __name__ == "__main__":
    sys.exit(main())
