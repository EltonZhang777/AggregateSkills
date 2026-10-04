import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath


SCHEMA_VERSION = 1
FIXTURE_ID = "generic-agent-skills-host-v1"
STATUSES = {"pass", "fail", "blocked", "not_run"}
ROLES = {
    "completeness": {
        "entrypoint_and_format",
        "resource_closure",
        "references_and_cycles",
        "all_files_classified",
    },
    "workflow_portability": {
        "generic_workflow_primary",
        "harness_independence",
        "capabilities_and_unavailable_behavior",
        "external_requirements",
    },
}
INVENTORY_KEYS = {"schema_version", "inventory_sha256", "package_count", "file_count", "packages"}
REVIEW_KEYS = {
    "schema_version", "skill_name", "reviewer_id", "reviewer_role", "fixture_id",
    "inventory_sha256", "overall_status", "criteria", "required_capabilities", "file_coverage",
}
EVIDENCE_KEYS = {"path", "start_line", "end_line", "excerpt"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_record(path, root):
    relative = path.relative_to(root).as_posix()
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        contents = os.fsencode(os.readlink(path))
        kind, size, lines = "symlink", len(contents), None
    elif stat.S_ISREG(info.st_mode):
        contents = path.read_bytes()
        kind, size = "file", len(contents)
        try:
            lines = len(contents.decode("utf-8").splitlines())
        except UnicodeDecodeError:
            lines = None
    else:
        contents = None
        kind, size, lines = "special", info.st_size, None
    return {
        "path": relative,
        "kind": kind,
        "size_bytes": size,
        "line_count": lines,
        "sha256": hashlib.sha256(contents).hexdigest() if contents is not None else None,
    }


def fail_walk(error):
    raise error


def package_files(root):
    found = []
    for current, directories, files in os.walk(root, followlinks=False, onerror=fail_walk):
        current = Path(current)
        directories.sort()
        files.sort()
        for name in list(directories):
            path = current / name
            if path.is_symlink():
                found.append(file_record(path, root))
                directories.remove(name)
        found.extend(file_record(current / name, root) for name in files)
    return sorted(found, key=lambda item: item["path"])


def build_inventory(skills_root):
    root = Path(skills_root)
    if not root.is_dir():
        raise ValueError("Skills root is not a directory.")
    packages = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.is_dir() and not path.is_symlink():
            files = package_files(path)
            packages.append({
                "name": path.name,
                "entrypoint_present": any(
                    item["path"] == "SKILL.md" and item["kind"] == "file" for item in files
                ),
                "files": files,
            })
    return {
        "schema_version": SCHEMA_VERSION,
        "inventory_sha256": digest(packages),
        "package_count": len(packages),
        "file_count": sum(len(package["files"]) for package in packages),
        "packages": packages,
    }


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return json.load(stream, object_pairs_hook=no_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as failure:
        raise ValueError(f"Invalid JSON input {Path(path).name}: {type(failure).__name__}") from failure


def err(errors, code, message, skill=None, reviewer=None, path=None):
    errors.append({
        "code": code,
        "message": message,
        "skill_name": skill,
        "reviewer_id": reviewer,
        "path": path,
    })


def shape(value, keys):
    return isinstance(value, dict) and set(value) == set(keys)


def integer(value):
    return type(value) is int


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        bool(path.parts)
        and not path.is_absolute()
        and str(path) == value
        and all(part not in {"", ".", ".."} for part in path.parts)
        and ":" not in path.parts[0]
    )


def aggregate(statuses):
    statuses = set(statuses)
    if "fail" in statuses:
        return "fail"
    if "blocked" in statuses:
        return "blocked"
    if "not_run" in statuses:
        return "not_run"
    return "pass"


def validate_inventory(inventory, current, errors):
    if not shape(inventory, INVENTORY_KEYS) or type(inventory.get("schema_version")) is not int or inventory.get("schema_version") != SCHEMA_VERSION:
        err(errors, "invalid_inventory_schema", "Inventory has an invalid schema.")
        return False
    if (
        not isinstance(inventory["packages"], list)
        or not integer(inventory["package_count"])
        or not integer(inventory["file_count"])
        or not isinstance(inventory["inventory_sha256"], str)
        or not SHA256.fullmatch(inventory["inventory_sha256"])
    ):
        err(errors, "invalid_inventory_schema", "Inventory packages or digest are invalid.")
        return False
    if inventory["inventory_sha256"] != digest(inventory["packages"]):
        err(errors, "invalid_inventory_schema", "Inventory digest does not match its package records.")
        return False
    if canonical(inventory) != canonical(current):
        err(errors, "stale_inventory", "Package files changed after inventory capture; regenerate the inventory and reviews.")
        return False
    return True


def validate_evidence(items, skill, reviewer, file_map, skills_root, errors):
    if not isinstance(items, list):
        err(errors, "invalid_result_schema", "Evidence must be a list.", skill, reviewer)
        return
    root = Path(skills_root) / skill
    for item in items:
        if not shape(item, EVIDENCE_KEYS):
            err(errors, "invalid_result_schema", "Evidence item has an invalid schema.", skill, reviewer)
            continue
        path = item["path"]
        record = file_map.get(path) if relative_path(path) else None
        start, end, excerpt = item["start_line"], item["end_line"], item["excerpt"]
        if (
            record is None
            or record["kind"] != "file"
            or record["line_count"] is None
            or not integer(start)
            or not integer(end)
            or start < 1
            or end < start
            or end > record["line_count"]
            or not isinstance(excerpt, str)
            or not excerpt.strip()
        ):
            err(errors, "unsupported_evidence", "Evidence path, line range, or excerpt is unsupported.", skill, reviewer, path if isinstance(path, str) else None)
            continue
        try:
            lines = (root / Path(*PurePosixPath(path).parts)).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            err(errors, "unsupported_evidence", "Evidence source cannot be read.", skill, reviewer, path)
            continue
        excerpt = excerpt.replace("\r\n", "\n").replace("\r", "\n")
        if excerpt not in "\n".join(lines[start - 1:end]):
            err(errors, "unsupported_evidence", "Evidence excerpt does not occur on its declared lines.", skill, reviewer, path)


def validate_review(review, inventory, package, reviewer_ids, errors, skills_root):
    if not shape(review, REVIEW_KEYS):
        err(errors, "invalid_result_schema", "Review has an invalid schema.")
        return None
    skill, reviewer, role = review["skill_name"], review["reviewer_id"], review["reviewer_role"]
    if skill != package["name"]:
        err(errors, "unsupported_skill_coverage", "Review is attached to the wrong skill.", package["name"], reviewer if isinstance(reviewer, str) else None)
        return None
    if not isinstance(reviewer, str) or not reviewer.strip():
        err(errors, "invalid_result_schema", "Reviewer ID must be non-empty text.", skill)
        return None
    if reviewer in reviewer_ids:
        err(errors, "duplicate_reviewer", "Reviewer IDs must be unique.", skill, reviewer)
    reviewer_ids.add(reviewer)
    if not isinstance(role, str) or role not in ROLES:
        err(errors, "invalid_result_schema", "Reviewer role is invalid.", skill, reviewer)
        return None
    if type(review["schema_version"]) is not int or review["schema_version"] != SCHEMA_VERSION:
        err(errors, "invalid_result_schema", "Review schema version is invalid.", skill, reviewer)
    if review["fixture_id"] != FIXTURE_ID:
        err(errors, "fixture_mismatch", "Review used a different host fixture.", skill, reviewer)
    if review["inventory_sha256"] != inventory["inventory_sha256"]:
        err(errors, "inventory_mismatch", "Review used a different package inventory.", skill, reviewer)

    criteria = review["criteria"]
    if not isinstance(criteria, list):
        err(errors, "invalid_result_schema", "Criteria must be a list.", skill, reviewer)
        criteria = []
    ids, statuses = [], []
    for criterion in criteria:
        if not shape(criterion, {"id", "status", "evidence", "findings"}):
            err(errors, "invalid_result_schema", "Criterion has an invalid schema.", skill, reviewer)
            continue
        criterion_id, status = criterion["id"], criterion["status"]
        if not isinstance(criterion_id, str) or criterion_id not in ROLES[role]:
            err(errors, "invalid_result_schema", "Criterion is not assigned to this review role.", skill, reviewer)
            continue
        ids.append(criterion_id)
        if not isinstance(status, str) or status not in STATUSES:
            err(errors, "invalid_result_schema", "Criterion status is invalid.", skill, reviewer)
            continue
        statuses.append(status)
        if isinstance(criterion["evidence"], list) and not criterion["evidence"]:
            err(errors, "unsupported_evidence", "Every criterion requires package-relative evidence.", skill, reviewer)
        validate_evidence(criterion["evidence"], skill, reviewer, package["file_map"], skills_root, errors)
        findings = criterion["findings"]
        if not isinstance(findings, list):
            err(errors, "invalid_result_schema", "Criterion findings must be a list.", skill, reviewer)
            continue
        if status != "pass" and not findings:
            err(errors, "invalid_result_schema", "Non-pass criteria require a finding.", skill, reviewer)
        for finding in findings:
            if (
                not shape(finding, {"summary", "impact"})
                or not isinstance(finding["summary"], str)
                or not finding["summary"].strip()
                or not isinstance(finding["impact"], str)
                or not finding["impact"].strip()
            ):
                err(errors, "invalid_result_schema", "Finding requires summary and impact text.", skill, reviewer)
    if len(ids) != len(set(ids)):
        err(errors, "duplicate_criterion_coverage", "Review contains duplicate criteria.", skill, reviewer)
    if set(ids) != ROLES[role]:
        err(errors, "missing_criterion_coverage", "Review does not cover its role's exact criteria.", skill, reviewer)
    status = review["overall_status"]
    if not isinstance(status, str) or status not in STATUSES:
        err(errors, "invalid_result_schema", "Overall review status is invalid.", skill, reviewer)
    elif statuses and status != aggregate(statuses):
        err(errors, "overall_status_mismatch", "Overall status promotes a non-pass criterion.", skill, reviewer)

    capabilities = review["required_capabilities"]
    if not isinstance(capabilities, list):
        err(errors, "invalid_result_schema", "Required capabilities must be a list.", skill, reviewer)
    else:
        for capability in capabilities:
            if not shape(capability, {"name", "scope", "unavailable_behavior", "evidence"}):
                err(errors, "invalid_result_schema", "Capability has an invalid schema.", skill, reviewer)
                continue
            if (
                not isinstance(capability["name"], str)
                or not capability["name"].strip()
                or not isinstance(capability["scope"], str)
                or capability["scope"] not in {"core", "optional"}
                or not isinstance(capability["unavailable_behavior"], str)
                or not capability["unavailable_behavior"].strip()
            ):
                err(errors, "invalid_result_schema", "Capability fields are invalid.", skill, reviewer)
            if isinstance(capability["evidence"], list) and not capability["evidence"]:
                err(errors, "unsupported_evidence", "Every required capability needs package-relative evidence.", skill, reviewer)
            validate_evidence(capability["evidence"], skill, reviewer, package["file_map"], skills_root, errors)

    coverage = review["file_coverage"]
    if not isinstance(coverage, list):
        err(errors, "invalid_result_schema", "File coverage must be a list.", skill, reviewer)
        coverage = []
    seen = []
    for item in coverage:
        if not shape(item, {"path", "classification", "disposition", "evidence"}):
            err(errors, "invalid_result_schema", "File coverage item has an invalid schema.", skill, reviewer)
            continue
        path = item["path"]
        if not isinstance(path, str) or path not in package["file_map"] or not relative_path(path):
            err(errors, "unsupported_file_coverage", "File coverage path is outside the inventoried package.", skill, reviewer, path if isinstance(path, str) else None)
            continue
        seen.append(path)
        if (
            not isinstance(item["classification"], str)
            or not item["classification"].strip()
            or not isinstance(item["disposition"], str)
            or item["disposition"] not in {"reviewed", "not_reviewed"}
        ):
            err(errors, "invalid_result_schema", "File classification or disposition is invalid.", skill, reviewer, path)
        if item["disposition"] == "not_reviewed" and status == "pass":
            err(errors, "incomplete_file_coverage", "A review with unreviewed files cannot pass.", skill, reviewer, path)
        validate_evidence(item["evidence"], skill, reviewer, package["file_map"], skills_root, errors)
    if len(seen) != len(set(seen)):
        err(errors, "duplicate_file_coverage", "Review contains duplicate file coverage.", skill, reviewer)
    missing = set(package["file_map"]) - set(seen)
    if missing:
        err(errors, "missing_file_coverage", f"Review omits files: {', '.join(sorted(missing))}.", skill, reviewer)

    return review if isinstance(status, str) and status in STATUSES else None


def check(skills_root, inventory, results):
    errors = []
    try:
        current = build_inventory(skills_root)
    except (OSError, ValueError) as failure:
        err(errors, "inventory_failed", str(failure))
        current = None

    valid_inventory = current is not None and validate_inventory(inventory, current, errors)
    if not valid_inventory:
        return {
            "schema_version": SCHEMA_VERSION,
            "fixture_id": FIXTURE_ID,
            "inventory_sha256": inventory.get("inventory_sha256") if isinstance(inventory, dict) else None,
            "overall_status": "blocked",
            "packages": [],
            "errors": errors,
        }
    if not inventory["packages"]:
        err(errors, "empty_inventory", "No skill packages were found to audit.")
        return output(inventory, [], errors)

    if not shape(results, {"schema_version", "fixture_id", "inventory_sha256", "reviews"}):
        err(errors, "invalid_results_schema", "Results have an invalid schema.")
        return output(inventory, [], errors)
    if type(results["schema_version"]) is not int or results["schema_version"] != SCHEMA_VERSION:
        err(errors, "invalid_results_schema", "Results schema version is invalid.")
    if results["fixture_id"] != FIXTURE_ID:
        err(errors, "fixture_mismatch", "Results use a different host fixture.")
    if results["inventory_sha256"] != inventory["inventory_sha256"]:
        err(errors, "inventory_mismatch", "Results use a different inventory digest.")
    reviews = results["reviews"]
    if not isinstance(reviews, list):
        err(errors, "invalid_results_schema", "Reviews must be a list.")
        reviews = []

    by_name = {
        item["name"]: {**item, "file_map": {record["path"]: record for record in item["files"]}}
        for item in inventory["packages"]
    }
    reviews_by_name = {name: [] for name in by_name}
    roles_seen, reviewer_ids = set(), set()

    for review in reviews:
        if not isinstance(review, dict):
            err(errors, "invalid_result_schema", "Review must be an object.")
            continue
        name = review.get("skill_name")
        if not isinstance(name, str) or name not in by_name:
            err(errors, "unsupported_skill_coverage", "Review names a skill missing from the inventory.")
            continue
        validated = validate_review(review, inventory, by_name[name], reviewer_ids, errors, skills_root)
        if validated is None:
            continue
        role_key = name, validated["reviewer_role"]
        if role_key in roles_seen:
            err(errors, "duplicate_reviewer", "Skill has duplicate reviewer-role coverage.", name, validated["reviewer_id"])
            continue
        roles_seen.add(role_key)
        reviews_by_name[name].append(validated)

    output_packages = []
    for name in sorted(by_name):
        items = sorted(reviews_by_name[name], key=lambda item: item["reviewer_role"])
        roles = {item["reviewer_role"] for item in items}
        if roles != set(ROLES):
            err(errors, "missing_reviewer", "Skill needs one reviewer for each role.", name)
            status = "blocked"
        elif len({item["overall_status"] for item in items}) != 1:
            err(errors, "reviewer_disagreement", "The reviewers disagree on overall status.", name)
            status = "blocked"
        else:
            status = items[0]["overall_status"]
        if any(item["skill_name"] == name for item in errors):
            status = "blocked"
        output_packages.append({"skill_name": name, "status": status, "reviews": items})
    return output(inventory, output_packages, errors)


def output(inventory, packages, errors):
    overall = "blocked" if errors else aggregate(package["status"] for package in packages)
    return {
        "schema_version": SCHEMA_VERSION,
        "fixture_id": FIXTURE_ID,
        "inventory_sha256": inventory.get("inventory_sha256") if isinstance(inventory, dict) else None,
        "overall_status": overall,
        "packages": packages,
        "errors": errors,
    }


def emit(value):
    print(json.dumps(value, sort_keys=True, indent=2))


def write_json_outside_skills(path, skills_root, value):
    destination = Path(path).resolve()
    try:
        destination.relative_to(Path(skills_root).resolve())
    except ValueError:
        pass
    else:
        raise ValueError("Audit output must be outside the skills root.")
    with destination.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def parser():
    root = argparse.ArgumentParser(description="Inventory skills and check isolated portability reviews.")
    commands = root.add_subparsers(dest="command", required=True)
    inventory = commands.add_parser("inventory", help="hash every file in every skill directory")
    inventory.add_argument("--skills-root", required=True, type=Path)
    inventory.add_argument("--output", type=Path, help="save UTF-8 JSON outside the skills root")
    check_cmd = commands.add_parser("check", help="check review schemas, coverage, evidence, and agreement")
    check_cmd.add_argument("--skills-root", required=True, type=Path)
    check_cmd.add_argument("--inventory", required=True, type=Path)
    check_cmd.add_argument("--results", required=True, type=Path)
    check_cmd.add_argument("--output", type=Path, help="save UTF-8 JSON outside the skills root")
    return root


def main(argv=None):
    arguments = parser().parse_args(argv)
    if arguments.command == "inventory":
        try:
            snapshot = build_inventory(arguments.skills_root)
            if arguments.output:
                write_json_outside_skills(arguments.output, arguments.skills_root, snapshot)
            emit(snapshot)
            return 0
        except (OSError, ValueError) as failure:
            emit({"schema_version": SCHEMA_VERSION, "overall_status": "not_run", "packages": [], "errors": [error("inventory_failed", str(failure))]})
            return 2
    try:
        inventory = read_json(arguments.inventory)
        results = read_json(arguments.results)
    except ValueError as failure:
        emit({
            "schema_version": SCHEMA_VERSION,
            "fixture_id": FIXTURE_ID,
            "inventory_sha256": None,
            "overall_status": "blocked",
            "packages": [],
            "errors": [error("input_failed", str(failure))],
        })
        return 2
    report = check(arguments.skills_root, inventory, results)
    if arguments.output:
        try:
            write_json_outside_skills(arguments.output, arguments.skills_root, report)
        except (OSError, ValueError) as failure:
            err(report["errors"], "output_failed", str(failure))
            report["overall_status"] = "blocked"
    emit(report)
    if report["errors"]:
        return 2
    return 0 if report["overall_status"] == "pass" else 1


def error(code, message):
    return {"code": code, "message": message, "skill_name": None, "reviewer_id": None, "path": None}


if __name__ == "__main__":
    sys.exit(main())
