#!/usr/bin/env python3
"""Audit authored Markdown for likely unmarked RFC 2119 instructions."""

import argparse
import os
import re
import sys
from pathlib import Path


UPPERCASE_KEYWORD = re.compile(
    r"\b(?:MUST(?:\s+NOT)?|SHALL(?:\s+NOT)?|SHOULD(?:\s+NOT)?|"
    r"REQUIRED|RECOMMENDED|NOT\s+RECOMMENDED|MAY|OPTIONAL)\b"
)
LOWERCASE_REQUIREMENT = re.compile(
    r"\b(?:must(?:\s+not)?|shall(?:\s+not)?|should(?:\s+not)?)\b"
)
UNMARKED_PROHIBITION = re.compile(r"\b(?:do\s+not|don't)\b", re.IGNORECASE)
UNMARKED_IMPERATIVE = re.compile(
    r"^(?:do\s+not|don't|use|check|read|follow|keep|make\s+sure|ensure|"
    r"ask|run|analyze|prioritize|inspect|verify|load|route|call|include|"
    r"avoid|return|delete|create|set|select|copy|move|add|remove|apply|"
    r"preserve|prefer|stop|continue|report|provide|display|choose|write|"
    r"save|validate|treat|target|organize|record|override|release|register|"
    r"place|expose|limit|consider)\b",
    re.IGNORECASE,
)
LIST_MARKER = re.compile(r"^(?:[-*+]\s+|\d+[.)]\s+)")


class AuditError(Exception):
    pass


def candidate_category(line: str):
    text = line.strip()
    if UPPERCASE_KEYWORD.search(text):
        return None
    if LOWERCASE_REQUIREMENT.search(text):
        return "lowercase requirement word"
    if UNMARKED_PROHIBITION.search(text):
        return "unmarked prohibition"
    if UNMARKED_IMPERATIVE.match(LIST_MARKER.sub("", text)):
        return "unmarked imperative"
    return None


def discover_markdown(root: Path) -> list[Path]:
    files: list[Path] = []

    def walk(directory: Path) -> None:
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            relative = directory.relative_to(root).as_posix() or "."
            raise AuditError(f"cannot scan {relative}: {exc}") from exc

        for entry in entries:
            relative = Path(entry.path).relative_to(root).as_posix()
            try:
                if entry.is_symlink():
                    if entry.name.lower().endswith(".md"):
                        raise AuditError(
                            f"symlink Markdown entry is not supported: {relative}"
                        )
                    continue
                if entry.name.lower().endswith(".md"):
                    if not entry.is_file(follow_symlinks=False):
                        raise AuditError(
                            f"non-regular Markdown entry is not supported: {relative}"
                        )
                    files.append(Path(entry.path))
                elif entry.is_dir(follow_symlinks=False):
                    walk(Path(entry.path))
            except OSError as exc:
                raise AuditError(f"cannot inspect {relative}: {exc}") from exc

    walk(root)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def operational_error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 2


def main() -> int:
    args = parse_args()
    try:
        root = args.root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        return operational_error(f"invalid root {args.root}: {exc}")
    if not root.is_dir():
        return operational_error(f"root is not a directory: {args.root}")

    try:
        files = discover_markdown(root)
    except AuditError as exc:
        return operational_error(str(exc))

    findings = []
    for path in files:
        relative_path = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            return operational_error(f"{relative_path} is not valid UTF-8: {exc}")
        except OSError as exc:
            return operational_error(f"cannot read {relative_path}: {exc}")

        for line_number, line in enumerate(text.splitlines(), start=1):
            category = candidate_category(line)
            if category:
                findings.append(
                    (
                        relative_path,
                        line_number,
                        category,
                        line.strip(),
                    )
                )

    if findings:
        for relative_path, line_number, category, text in findings:
            print(f"{relative_path}:{line_number}: {category}: {text}")
        print(
            f"RFC 2119 candidate audit: {len(findings)} candidate(s) "
            f"in {len(files)} Markdown files."
        )
        return 1 if args.strict else 0

    if not files:
        print("RFC 2119 candidate audit: 0 files scanned; no candidates found.")
    else:
        print(
            f"RFC 2119 candidate audit: no candidates found "
            f"in {len(files)} Markdown files."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
