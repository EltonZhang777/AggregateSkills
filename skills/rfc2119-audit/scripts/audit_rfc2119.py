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
LIST_ITEM_PREFIX = re.compile(
    r"^( {0,3})([-*+]|\d+[.)])([ \t]+)(.*)$"
)
EMPTY_LIST_ITEM = re.compile(r"^( {0,3})([-*+]|\d+[.)])[ \t]*$")
BLOCKQUOTE_PREFIX = re.compile(r"^ {0,3}>([ \t]*)(.*)$")
FENCE_LINE = re.compile(r"^( *)(`{3,}|~{3,})(.*)$")
LIST_FENCE = re.compile(
    r"^( {0,3})([-*+]|\d+[.)])( {1,4})(`{3,}|~{3,})(.*)$"
)
BACKTICK_RUN = re.compile(r"`+")
ATX_HEADING = re.compile(r"^ {0,3}#{1,6}(?:\s|$)")
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)\s*$")
THEMATIC_BREAK = re.compile(
    r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$"
)
TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")


class AuditError(Exception):
    pass


def find_comment_opening(line: str, start: int = 0) -> int:
    opening = line.find("<!--", start)
    while opening != -1:
        backslashes = 0
        position = opening - 1
        while position >= 0 and line[position] == "\\":
            backslashes += 1
            position -= 1
        if backslashes % 2 == 0:
            return opening
        opening = line.find("<!--", opening + 4)
    return -1


def block_comment_opening(line: str) -> int:
    opening = find_comment_opening(line)
    if 0 <= opening <= 3 and not line[:opening].strip():
        return opening
    return -1


def fence_opener(line: str):
    list_fence = LIST_FENCE.match(line)
    if list_fence is not None:
        indent, marker, spacing, fence, remainder = list_fence.groups()
        close_indent = len(indent) + len(marker) + len(spacing) + 3
    else:
        match = FENCE_LINE.match(line)
        if match is None:
            return None
        indent, fence, remainder = match.groups()
        if len(indent) > 3:
            return None
        close_indent = 3
    if fence[0] == "`" and "`" in remainder:
        return None
    return fence, remainder, close_indent


def fence_closer(line: str, max_indent: int):
    match = FENCE_LINE.match(line)
    if match is None:
        return None
    indent, marker, remainder = match.groups()
    if len(indent) > max_indent:
        return None
    return marker, remainder


def find_inline_code_opening(line: str, start: int):
    for match in BACKTICK_RUN.finditer(line, start):
        backslashes = 0
        position = match.start() - 1
        while position >= 0 and line[position] == "\\":
            backslashes += 1
            position -= 1
        if backslashes % 2 == 0:
            return match
        remaining = BACKTICK_RUN.match(line, match.start() + 1)
        if remaining is not None:
            return remaining
    return None


def matching_inline_close(
    lines: list[str], line_index: int, start: int, delimiter_length: int,
    allow_multiline: bool, tabular_rows: set[int],
):
    boundary = None
    if line_index in tabular_rows:
        pipes = [
            pipe for pipe in table_parts(lines[line_index])[1]
            if pipe >= start
        ]
        boundary = min(pipes) if pipes else None
    for match in BACKTICK_RUN.finditer(lines[line_index], start):
        if boundary is not None and match.start() >= boundary:
            break
        if len(match.group()) == delimiter_length:
            return line_index, match.start(), match.end()
    if not allow_multiline:
        return None
    if line_index in tabular_rows:
        return None
    for index in range(line_index + 1, len(lines)):
        line = lines[index]
        if (
            not line.strip()
            or line.startswith("    ")
            or line.lstrip().startswith(">")
            or fence_opener(line)
            or ATX_HEADING.match(line)
            or LIST_MARKER.match(line.lstrip())
            or SETEXT_UNDERLINE.fullmatch(line)
            or THEMATIC_BREAK.fullmatch(line)
        ):
            return None
        close = next(
            (
                match
                for match in BACKTICK_RUN.finditer(line)
                if len(match.group()) == delimiter_length
            ),
            None,
        )
        comment_opening = block_comment_opening(line)
        comment_positions = (
            [comment_opening] if comment_opening != -1 else []
        )
        pipe_positions = table_parts(line)[1] if index in tabular_rows else []
        boundary_positions = comment_positions + pipe_positions
        boundary = min(boundary_positions) if boundary_positions else None
        if close is not None and (boundary is None or close.start() < boundary):
            return index, close.start(), close.end()
        if boundary is not None:
            return None
    return None


def mask_comments_and_inline_code(
    line: str, in_comment: bool, code_length: int, lines: list[str],
    line_index: int, allow_multiline: bool, tabular_rows: set[int],
):
    pieces = []
    index = 0
    while index < len(line):
        if in_comment:
            end = line.find("-->", index)
            if end == -1:
                pieces.append(" " * (len(line) - index))
                return "".join(pieces), True, code_length
            pieces.append(" " * (end + 3 - index))
            index = end + 3
            in_comment = False
        elif code_length:
            close = next(
                (
                    match
                    for match in BACKTICK_RUN.finditer(line, index)
                    if len(match.group()) == code_length
                ),
                None,
            )
            if close is None:
                pieces.append(" " * (len(line) - index))
                return "".join(pieces), False, code_length
            pieces.append(" " * (close.end() - index))
            index = close.end()
            code_length = 0
        else:
            start = find_comment_opening(line, index)
            code = find_inline_code_opening(line, index)
            if code is not None and (start == -1 or code.start() < start):
                delimiter_length = len(code.group())
                close = matching_inline_close(
                    lines,
                    line_index,
                    code.end(),
                    delimiter_length,
                    allow_multiline,
                    tabular_rows,
                )
                if close is None:
                    pieces.append(line[index:code.end()])
                    index = code.end()
                elif close[0] == line_index:
                    pieces.append(line[index:code.start()])
                    pieces.append(" " * (close[2] - code.start()))
                    index = close[2]
                else:
                    pieces.append(line[index:code.start()])
                    pieces.append(" " * (len(line) - code.start()))
                    return "".join(pieces), False, delimiter_length
            elif start == -1:
                pieces.append(line[index:])
                return "".join(pieces), False, 0
            else:
                pieces.append(line[index:start])
                pieces.append("    ")
                index = start + 4
                in_comment = True
    return "".join(pieces), in_comment, code_length


def table_separator_columns(line: str):
    if line is None:
        return None
    cells, pipes = table_parts(line)
    if not pipes:
        return None
    if cells and all(TABLE_SEPARATOR_CELL.fullmatch(cell) for cell in cells):
        return len(cells)
    return None


def table_parts(line: str):
    value = line.strip()
    leading = len(line) - len(line.lstrip())
    cells = []
    pipes = []
    cell = []
    backslashes = 0
    for index, character in enumerate(value):
        if character == "\\":
            cell.append(character)
            backslashes += 1
        elif character == "|":
            if backslashes % 2:
                cell.append(character)
            else:
                cells.append("".join(cell).strip())
                pipes.append(index)
                cell = []
            backslashes = 0
        else:
            cell.append(character)
            backslashes = 0
    cells.append("".join(cell).strip())
    if pipes and pipes[0] == 0:
        cells.pop(0)
    if pipes and pipes[-1] == len(value) - 1:
        cells.pop()
    return cells, [pipe + leading for pipe in pipes]


def table_cells(line: str) -> list[str]:
    return table_parts(line)[0]


def setext_underline_before(
    lines: list[str],
    index: int,
    source_table_rows: set[int],
    previous_visible,
    container_indent: int,
) -> bool:
    underline_indent = len(lines[index]) - len(lines[index].lstrip(" "))
    if (
        index == 0
        or index - 1 in source_table_rows
        or SETEXT_UNDERLINE.fullmatch(lines[index]) is None
        or underline_indent < container_indent
        or (previous_visible is not None and not previous_visible.strip())
        or (
            previous_visible is None
            and SETEXT_UNDERLINE.fullmatch(lines[index - 1]) is not None
        )
    ):
        return False
    previous = lines[index - 1]
    if (
        not previous.strip()
        or previous.startswith("    ")
        or ATX_HEADING.match(previous) is not None
        or BLOCKQUOTE_PREFIX.match(previous) is not None
        or fence_opener(previous) is not None
        or THEMATIC_BREAK.fullmatch(previous) is not None
        or block_comment_opening(previous) != -1
    ):
        return False
    list_item = LIST_ITEM_PREFIX.match(previous)
    if list_item is None:
        return True
    content_indent = sum(len(group) for group in list_item.groups()[:3])
    return underline_indent >= content_indent


def table_rows(lines: list[str], masked_lines=None) -> set[int]:
    rows = set()
    in_table = False
    table_columns = 0
    for index, line in enumerate(lines):
        if line is None or not line.strip():
            in_table = False
            table_columns = 0
            continue
        if LIST_MARKER.match(line.strip()):
            in_table = False
            table_columns = 0
            continue
        if in_table:
            if (
                fence_opener(line) is not None
                or ATX_HEADING.match(line) is not None
                or THEMATIC_BREAK.fullmatch(line) is not None
                or EMPTY_LIST_ITEM.fullmatch(line) is not None
                or BLOCKQUOTE_PREFIX.match(line) is not None
                or block_comment_opening(line) != -1
                or line.startswith("    ")
            ):
                in_table = False
                table_columns = 0
            elif table_parts(line)[1]:
                rows.add(index)
                continue
            elif table_columns == 1:
                rows.add(index)
                continue
            else:
                in_table = False
                table_columns = 0
        separator_columns = (
            table_separator_columns(lines[index + 1])
            if index + 1 < len(lines)
            else None
        )
        masked_header = masked_lines[index] if masked_lines is not None else line
        if (
            table_parts(line)[1]
            and separator_columns == len(table_cells(line))
            and masked_header is not None
            and table_parts(masked_header)[1]
        ):
            rows.update((index, index + 1))
            in_table = True
            table_columns = separator_columns
    return rows


def candidate_category(line: str, is_table: bool = False):
    text = line.strip()
    if UPPERCASE_KEYWORD.search(text):
        return None
    if LOWERCASE_REQUIREMENT.search(text):
        return "lowercase requirement word"
    if UNMARKED_PROHIBITION.search(text):
        return "unmarked prohibition"
    if is_table:
        return None
    if UNMARKED_IMPERATIVE.match(LIST_MARKER.sub("", text)):
        return "unmarked imperative"
    return None


def visible_markdown_lines(lines: list[str]):
    visible = []
    source_table_rows = table_rows(lines)
    in_frontmatter = False
    first_line = True
    fence_char = None
    fence_length = 0
    fence_indent = 3
    fence_min_indent = 0
    in_html_comment = False
    inline_code_length = 0
    list_indents = []

    for index, raw_line in enumerate(lines):
        line = raw_line.rstrip()
        if first_line:
            first_line = False
            line = line.removeprefix("\ufeff")
            if line == "---":
                in_frontmatter = True
                visible.append(None)
                continue
        if in_frontmatter:
            if line == "---":
                in_frontmatter = False
            visible.append(None)
            continue

        if fence_char is not None:
            indentation = len(line) - len(line.lstrip(" "))
            if not line.strip() or indentation >= fence_min_indent:
                fence = fence_closer(line, fence_indent)
                if fence is not None:
                    marker, remainder = fence
                    if (
                        marker[0] == fence_char
                        and len(marker) >= fence_length
                        and not remainder.strip()
                    ):
                        fence_char = None
                        fence_length = 0
                        fence_indent = 3
                        fence_min_indent = 0
                visible.append(None)
                continue
            fence_char = None
            fence_length = 0
            fence_indent = 3
            fence_min_indent = 0

        starts_in_comment = in_html_comment
        list_item = LIST_ITEM_PREFIX.match(line)
        empty_list_item = EMPTY_LIST_ITEM.fullmatch(line)
        is_thematic_break = THEMATIC_BREAK.fullmatch(line) is not None
        list_content = list_item.group(4) if list_item is not None else ""
        if not starts_in_comment:
            if list_item is not None:
                if is_thematic_break:
                    indentation = len(line) - len(line.lstrip(" "))
                    while list_indents and list_indents[-1] > indentation:
                        list_indents.pop()
                else:
                    marker_indent = len(list_item.group(1))
                    while list_indents and list_indents[-1] > marker_indent:
                        list_indents.pop()
                    list_indents.append(
                        marker_indent
                        + len(list_item.group(2))
                        + len(list_item.group(3))
                    )
            elif (
                empty_list_item is not None
                and not setext_underline_before(
                    lines,
                    index,
                    source_table_rows,
                    visible[-1] if visible else None,
                    list_indents[-1] if list_indents else 0,
                )
            ):
                marker_indent = len(empty_list_item.group(1))
                while list_indents and list_indents[-1] > marker_indent:
                    list_indents.pop()
                list_indents.append(
                    marker_indent + len(empty_list_item.group(2)) + 1
                )
            elif line.strip() and list_indents:
                indentation = len(line) - len(line.lstrip(" "))
                while list_indents and list_indents[-1] > indentation:
                    list_indents.pop()

        list_indent = list_indents[-1] if list_indents else 0
        fence_min_indent = 0
        fence = None
        if list_indent:
            indentation = len(line) - len(line.lstrip(" "))
            if list_indent <= indentation <= list_indent + 3:
                fence = fence_opener(line[list_indent:])
                if fence is not None:
                    marker, remainder, close_indent = fence
                    fence = marker, remainder, list_indent + close_indent
                    fence_min_indent = list_indent
        if fence is None:
            fence = fence_opener(line)
            if fence is not None and LIST_FENCE.match(line) is not None:
                fence_min_indent = list_indent
        if not starts_in_comment and fence is not None:
            marker, remainder, fence_indent = fence
            fence_char = marker[0]
            fence_length = len(marker)
            visible.append(None)
            continue

        quote = BLOCKQUOTE_PREFIX.match(line)
        quote_content = quote.group(2) if quote is not None else ""
        nested_quote = BLOCKQUOTE_PREFIX.match(list_content)
        nested_list = LIST_ITEM_PREFIX.match(quote_content)
        is_indented_code = (
            line.startswith("    ")
            or (list_item is not None and len(list_item.group(3)) > 4)
            or (quote is not None and len(quote.group(1)) > 4)
            or (nested_quote is not None and len(nested_quote.group(1)) > 4)
            or (nested_list is not None and len(nested_list.group(3)) > 4)
        ) and not starts_in_comment
        is_block_quote = (
            not starts_in_comment
            and (
                quote is not None
                or nested_quote is not None
            )
        )
        is_atx_heading = (
            not starts_in_comment
            and (
                ATX_HEADING.match(line) is not None
                or ATX_HEADING.match(list_content) is not None
                or ATX_HEADING.match(quote_content) is not None
                or (
                    nested_list is not None
                    and ATX_HEADING.match(nested_list.group(4)) is not None
                )
            )
        )
        next_line_is_setext = False
        if (
            index + 1 < len(lines)
            and SETEXT_UNDERLINE.fullmatch(lines[index + 1]) is not None
        ):
            next_line_indent = len(lines[index + 1]) - len(
                lines[index + 1].lstrip(" ")
            )
            next_line_is_setext = (
                not list_indents or next_line_indent >= list_indents[-1]
            )
        is_setext_candidate = (
            not starts_in_comment
            and line.strip()
            and next_line_is_setext
            and index not in source_table_rows
        )
        if is_indented_code:
            visible.append(None)
            continue

        line, in_html_comment, inline_code_length = mask_comments_and_inline_code(
            line,
            starts_in_comment,
            inline_code_length,
            lines,
            index,
            not (is_block_quote or is_atx_heading or is_setext_candidate),
            source_table_rows,
        )
        is_setext_heading = is_setext_candidate and not in_html_comment
        if is_block_quote or is_atx_heading or is_setext_heading:
            visible.append(None)
        else:
            visible.append(line)

    return visible


def audit_text(text: str):
    findings = []
    lines = text.splitlines()
    visible_lines = visible_markdown_lines(lines)
    tabular_rows = table_rows(lines, visible_lines)
    for line_number, (raw_line, line) in enumerate(
        zip(lines, visible_lines), start=1
    ):
        if line is None:
            continue
        if not line.strip():
            continue

        category = candidate_category(line, line_number - 1 in tabular_rows)
        if category:
            findings.append((line_number, category, raw_line.strip()))

    return findings


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
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
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

        findings.extend(
            (relative_path, line_number, category, text)
            for line_number, category, text in audit_text(text)
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
