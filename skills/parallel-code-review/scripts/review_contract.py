import argparse
import codecs
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlparse
from pathlib import Path, PurePosixPath


CONTRACT_VERSION = 1
ROUTING_MARKER = "<!-- parallel-code-review-routing-table -->"
METADATA_MARKER = "<!-- parallel-code-review-track-metadata -->"
ROUTING_PATH = "references/routing-table.md"
TRACKS_DIR = PurePosixPath("references/tracks")
REQUIRED_INPUTS = {
    "patch",
    "tree",
    "requirements",
    "standards",
    "checks",
    "exclusions",
}
METADATA_FIELDS = {"contract_version", "upstream", "required_inputs"}
UPSTREAM_FIELDS = {"name", "source"}
PATCH_PATH = "scope/patch.diff"
SEVERITIES = {"P0", "P1", "P2"}
CHECK_RESULTS = {"passed", "failed", "not_assessed"}
ENVELOPE_FIELDS = {
    "contract_version",
    "track_id",
    "invocation_id",
    "launch_status",
    "attestation",
    "coverage",
    "native",
    "findings",
}
FINDING_COMMON_FIELDS = {
    "severity",
    "severity_rationale",
    "title",
    "location",
    "what_this_is",
    "problem",
    "fix",
    "if_we_skip_it",
    "citations",
}
FINDING_NATIVE_FIELDS = {
    "native_axis",
    "native_id",
    "native_severity",
    "native_group",
}
RUN_FIELDS = {"contract_version", "tracks", "checks", "partial"}
RUN_TRACK_FIELDS = {"track_id", "attempts"}
RUN_ATTEMPT_FIELDS = {
    "invocation_id",
    "status",
    "launch_status",
    "request_sha256",
}
RUN_FAILURE_CLASSES = {
    "launch_failure",
    "transient_runtime",
    "transient_transport",
    "invalid_result",
    "scope_mismatch",
}
TRANSIENT_FAILURE_CLASSES = {"transient_runtime", "transient_transport"}
RUN_PARTIAL_FIELDS = {
    "approval",
    "blocked_result",
    "missing_track_ids",
    "reduced_independence",
}
RUN_APPROVAL_FIELDS = {"source", "evidence"}
RUN_BLOCKED_RESULT_FIELDS = {"path", "sha256"}
RUN_RECOVERY_FIELDS = {"of_invocation_id", "analysis_reused"}
TRANSIENT_EVIDENCE_FIELDS = {"source", "phase", "detail"}
CAPABILITY_CHECKS = {"independence_capability", "recovery_capability"}
RUN_RESULT_FIELDS = {
    "status",
    "tracks",
    "completed_reports",
    "missing_tracks",
    "coverage",
    "checks",
    "partial",
}


class ContractFailure(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def normalized_text_sha256_bytes(data):
    text = data.decode("utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def exact_file_pin(path):
    data = path.read_bytes()
    return {
        "sha256": sha256_bytes(data),
        "size_bytes": len(data),
        "normalized_sha256": normalized_text_sha256_bytes(data),
    }


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(payload):
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def scope_sha256(scope):
    return sha256_bytes(canonical_json_bytes(scope))


def error_payload(errors):
    return {
        "status": "blocked",
        "errors": [{"code": error.code, "message": error.message} for error in errors],
    }


def parse_routing_table(skill_root):
    path = skill_root / ROUTING_PATH
    if not path.is_file():
        raise ContractFailure("routing_table_missing", f"Missing route table: {ROUTING_PATH}")

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ContractFailure("routing_table_malformed", f"Cannot read route table: {exc}") from exc

    if text.count(ROUTING_MARKER) != 1:
        raise ContractFailure(
            "routing_table_malformed",
            "The route table must contain exactly one fixed routing marker.",
        )

    lines = text.split(ROUTING_MARKER, 1)[1].splitlines()
    table_lines = [line.strip() for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 2:
        raise ContractFailure("routing_table_empty", "The route table has no track rows.")

    def cells(line):
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    header = [cell.lower() for cell in cells(table_lines[0])]
    if header != ["track id", "adapter document"]:
        raise ContractFailure(
            "routing_table_malformed",
            "The route table header must be: Track ID | Adapter document.",
        )

    separator = cells(table_lines[1])
    if len(separator) != 2 or any(not re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
        raise ContractFailure("routing_table_malformed", "The route table separator is invalid.")

    rows = []
    for line in table_lines[2:]:
        row = cells(line)
        if len(row) != 2:
            raise ContractFailure("routing_table_malformed", f"Malformed route row: {line}")
        rows.append((row[0], row[1]))
    if not rows:
        raise ContractFailure("routing_table_empty", "The route table has no track rows.")
    return path, rows


def safe_adapter_path(skill_root, adapter_text):
    normalized = adapter_text.replace("\\", "/")
    adapter = PurePosixPath(normalized)
    if (
        adapter.is_absolute()
        or re.match(r"^[A-Za-z]:", normalized)
        or ".." in adapter.parts
        or adapter.parts[:2] != TRACKS_DIR.parts
        or adapter.suffix != ".md"
    ):
        raise ContractFailure(
            "adapter_path_invalid",
            f"Adapter must be a Markdown file under references/tracks: {adapter_text}",
        )
    return skill_root.joinpath(*adapter.parts)


def parse_metadata(text):
    marker_count = text.count(METADATA_MARKER)
    if marker_count == 0:
        raise ContractFailure("metadata_missing", "Adapter has no fixed-marker metadata block.")
    if marker_count > 1:
        raise ContractFailure("metadata_duplicate", "Adapter has more than one metadata marker.")

    if text.split(METADATA_MARKER, 1)[0].strip():
        raise ContractFailure(
            "metadata_malformed",
            "Adapter metadata must be the first non-whitespace content.",
        )

    tail = text.split(METADATA_MARKER, 1)[1].lstrip("\r\n ")
    opening = "```json"
    if not tail.startswith(opening):
        raise ContractFailure("metadata_malformed", "Metadata must be a json fenced block.")
    tail = tail[len(opening):].lstrip("\r\n")
    block, separator, _ = tail.partition("```")
    if not separator:
        raise ContractFailure("metadata_malformed", "Metadata fenced block is not closed.")
    try:
        payload = json.loads(block)
    except json.JSONDecodeError as exc:
        raise ContractFailure("metadata_malformed", f"Metadata is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractFailure("metadata_invalid", "Metadata must be a JSON object.")
    return payload


def validate_metadata(payload):
    unknown = sorted(set(payload) - METADATA_FIELDS)
    if unknown:
        raise ContractFailure(
            "metadata_unknown_field",
            f"Unknown metadata fields: {', '.join(unknown)}",
        )
    if set(payload) != METADATA_FIELDS:
        raise ContractFailure("metadata_invalid", "Metadata fields are incomplete.")

    version = payload["contract_version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise ContractFailure("metadata_invalid", "contract_version must be an integer.")
    if version != CONTRACT_VERSION:
        raise ContractFailure(
            "metadata_version_mismatch",
            f"Expected contract_version {CONTRACT_VERSION}, got {version}.",
        )

    upstream = payload["upstream"]
    if not isinstance(upstream, dict) or set(upstream) != UPSTREAM_FIELDS:
        raise ContractFailure(
            "metadata_invalid",
            "upstream must contain exactly name and source.",
        )
    if any(not isinstance(upstream[field], str) or not upstream[field].strip() for field in UPSTREAM_FIELDS):
        raise ContractFailure("metadata_invalid", "upstream name and source must be non-empty strings.")

    inputs = payload["required_inputs"]
    if (
        not isinstance(inputs, list)
        or not inputs
        or any(not isinstance(item, str) or not item for item in inputs)
        or len(inputs) != len(set(inputs))
    ):
        raise ContractFailure(
            "metadata_invalid",
            "required_inputs must be a non-empty list of unique strings.",
        )
    unknown_inputs = sorted(set(inputs) - REQUIRED_INPUTS)
    if unknown_inputs:
        raise ContractFailure(
            "metadata_unknown_input",
            f"Unknown required inputs: {', '.join(unknown_inputs)}",
        )


def parse_upstream_values(values, code):
    parsed = parse_named_values(values, code)
    names = [name for name, _ in parsed]
    if len(names) != len(set(names)):
        raise ContractFailure("upstream_duplicate", "Upstream resolutions must be unique.")
    return dict(parsed)


def parse_upstream_sizes(values):
    parsed = parse_named_values(values, "upstream_size_invalid")
    names = [name for name, _ in parsed]
    if len(names) != len(set(names)):
        raise ContractFailure("upstream_duplicate", "Upstream sizes must be unique.")
    sizes = {}
    for name, value in parsed:
        if not re.fullmatch(r"[0-9]+", value):
            raise ContractFailure(
                "upstream_size_invalid",
                f"Upstream exact byte size is invalid for {name}: {value}",
            )
        sizes[name] = int(value)
    return sizes


def local_upstream_path(value):
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return Path(value)
    parsed = urlparse(value)
    if parsed.scheme == "file":
        path = unquote(parsed.path)
        if parsed.netloc:
            path = f"//{parsed.netloc}{path}"
        if re.match(r"^/[A-Za-z]:", path):
            path = path[1:]
        return Path(path)
    if parsed.scheme:
        return None
    return Path(value)


def validate_upstream_resolutions(
    dependencies,
    resolutions,
    normalized_hashes,
    exact_hashes,
    sizes,
    validate_unknown=True,
):
    errors = []
    expected = {dependency["name"] for dependency in dependencies}
    supplied = set(resolutions)
    supplied_normalized_hashes = set(normalized_hashes)
    supplied_exact_hashes = set(exact_hashes)
    supplied_sizes = set(sizes)
    unknown = sorted(supplied - expected) if validate_unknown else []
    if unknown:
        errors.append(
            ContractFailure(
                "upstream_unknown",
                f"Upstream resolutions do not match routed dependencies: {', '.join(unknown)}",
            )
        )
    unknown_normalized_hashes = (
        sorted(supplied_normalized_hashes - expected) if validate_unknown else []
    )
    if unknown_normalized_hashes:
        errors.append(
            ContractFailure(
                "upstream_unknown",
                "Upstream normalized hashes do not match routed dependencies: "
                f"{', '.join(unknown_normalized_hashes)}",
            )
        )
    unknown_exact_hashes = (
        sorted(supplied_exact_hashes - expected) if validate_unknown else []
    )
    if unknown_exact_hashes:
        errors.append(
            ContractFailure(
                "upstream_unknown",
                "Upstream exact hashes do not match routed dependencies: "
                f"{', '.join(unknown_exact_hashes)}",
            )
        )
    unknown_sizes = sorted(supplied_sizes - expected) if validate_unknown else []
    if unknown_sizes:
        errors.append(
            ContractFailure(
                "upstream_unknown",
                "Upstream sizes do not match routed dependencies: "
                f"{', '.join(unknown_sizes)}",
            )
        )

    pins = {}
    for dependency in dependencies:
        name = dependency["name"]
        if name not in resolutions:
            errors.append(
                ContractFailure(
                    "upstream_unresolved",
                    f"No resolved upstream source was supplied for {name}.",
                )
            )
            continue
        resolved_uri = resolutions[name].strip()
        if not resolved_uri:
            errors.append(
                ContractFailure(
                    "upstream_unresolved",
                    f"Resolved upstream source is empty for {name}.",
                )
            )
            continue

        local_path = local_upstream_path(resolved_uri)
        supplied_normalized = normalized_hashes.get(name)
        supplied_exact = exact_hashes.get(name)
        supplied_size = sizes.get(name)
        if local_path is not None:
            path = local_path.expanduser()
            if path.is_dir():
                resolution_kind = "local_directory"
                path = path / "SKILL.md"
            else:
                resolution_kind = "local_file"
            if path.is_symlink() or not path.is_file():
                errors.append(
                    ContractFailure(
                        "upstream_unreadable",
                        f"Resolved upstream skill is not a readable file for {name}: {path}",
                    )
                )
                continue
            try:
                data = path.read_bytes()
                text = data.decode("utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(
                    ContractFailure(
                        "upstream_unreadable",
                        f"Cannot read resolved upstream skill for {name}: {exc}",
                    )
                )
                continue
            if not text.strip():
                errors.append(
                    ContractFailure(
                        "upstream_empty",
                        f"Resolved upstream skill is empty for {name}: {path}",
                    )
                )
                continue
            resolved_uri = path.resolve().as_uri()
            exact_sha256 = sha256_bytes(data)
            size_bytes = len(data)
            normalized_sha256 = normalized_text_sha256_bytes(data)
            if supplied_exact is not None and supplied_exact != exact_sha256:
                errors.append(
                    ContractFailure(
                        "upstream_hash_mismatch",
                        f"Resolved upstream exact hash changed for {name}.",
                    )
                )
                continue
            if supplied_size is not None and supplied_size != size_bytes:
                errors.append(
                    ContractFailure(
                        "upstream_size_mismatch",
                        f"Resolved upstream exact size changed for {name}.",
                    )
                )
                continue
            if supplied_normalized is not None and supplied_normalized != normalized_sha256:
                errors.append(
                    ContractFailure(
                        "upstream_hash_mismatch",
                        f"Resolved upstream normalized text hash changed for {name}.",
                    )
                )
                continue
        else:
            resolution_kind = "remote_uri"
            if not supplied_exact:
                errors.append(
                    ContractFailure(
                        "upstream_unresolved",
                        f"An exact SHA-256 is required for resolved URI {name}: {resolved_uri}",
                    )
                )
                continue
            if supplied_size is None:
                errors.append(
                    ContractFailure(
                        "upstream_unresolved",
                        f"An exact byte size is required for resolved URI {name}: {resolved_uri}",
                    )
                )
                continue
            exact_sha256 = supplied_exact
            size_bytes = supplied_size
            normalized_sha256 = supplied_normalized

        if not re.fullmatch(r"[0-9a-f]{64}", exact_sha256 or ""):
            errors.append(
                ContractFailure(
                    "upstream_hash_invalid",
                    f"Upstream exact hash is invalid for {name}.",
                )
            )
            continue
        if (
            normalized_sha256 is not None
            and not re.fullmatch(r"[0-9a-f]{64}", normalized_sha256)
        ):
            errors.append(
                ContractFailure(
                    "upstream_hash_invalid",
                    f"Upstream normalized text hash is invalid for {name}.",
                )
            )
            continue
        if size_bytes <= 0:
            errors.append(
                ContractFailure(
                    "upstream_empty",
                    f"Resolved upstream skill is empty for {name}: {resolved_uri}",
                )
            )
            continue
        identity = (name, dependency["source"])
        pins[identity] = {
            "name": name,
            "source": dependency["source"],
            "kind": resolution_kind,
            "uri": resolved_uri,
            "sha256": exact_sha256,
            "size_bytes": size_bytes,
        }
        if normalized_sha256 is not None:
            pins[identity]["normalized_sha256"] = normalized_sha256
    return pins, errors


def collect_preflight(
    skill_root,
    upstream_values=None,
    upstream_normalized_hashes=None,
    upstream_exact_hashes=None,
    upstream_sizes=None,
    require_upstream=True,
):
    routing_path, rows = parse_routing_table(skill_root)
    errors = []
    tracks = []
    routed_paths = set()
    seen_ids = set()
    seen_adapters = set()
    resolutions = {}
    normalized_hashes = {}
    exact_hashes = {}
    sizes = {}
    try:
        resolutions = parse_upstream_values(upstream_values or [], "upstream_invalid")
        normalized_hashes = parse_upstream_values(
            upstream_normalized_hashes or [],
            "upstream_hash_invalid",
        )
        exact_hashes = parse_upstream_values(
            upstream_exact_hashes or [],
            "upstream_hash_invalid",
        )
        sizes = parse_upstream_sizes(upstream_sizes or [])
    except ContractFailure as exc:
        errors.append(exc)

    for track_id, adapter_text in rows:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", track_id):
            errors.append(
                ContractFailure("track_id_invalid", f"Invalid track ID: {track_id}")
            )
            continue
        if track_id in seen_ids:
            errors.append(
                ContractFailure("duplicate_track_id", f"Duplicate track ID: {track_id}")
            )
            continue
        seen_ids.add(track_id)

        try:
            adapter_path = safe_adapter_path(skill_root, adapter_text)
        except ContractFailure as exc:
            errors.append(exc)
            continue
        if adapter_path in seen_adapters:
            errors.append(
                ContractFailure("duplicate_adapter", f"Duplicate adapter: {adapter_text}")
            )
            continue
        seen_adapters.add(adapter_path)
        resolved_adapter = adapter_path.resolve()
        routed_paths.add(resolved_adapter)

        if not adapter_path.exists():
            errors.append(
                ContractFailure("adapter_missing", f"Missing adapter: {adapter_text}")
            )
            continue
        try:
            within_skill = os.path.commonpath(
                [str(skill_root.resolve()), str(resolved_adapter)]
            ) == str(skill_root.resolve())
        except ValueError:
            within_skill = False
        if adapter_path.is_symlink() or not within_skill or not adapter_path.is_file():
            errors.append(
                ContractFailure("adapter_unreadable", f"Adapter is not a file: {adapter_text}")
            )
            continue
        try:
            text = adapter_path.read_text(encoding="utf-8")
            payload = parse_metadata(text)
            validate_metadata(payload)
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(
                ContractFailure("adapter_unreadable", f"Cannot read {adapter_text}: {exc}")
            )
            continue
        except ContractFailure as exc:
            errors.append(
                ContractFailure(exc.code, f"{adapter_text}: {exc.message}")
            )
            continue

        tracks.append(
            {
                "track_id": track_id,
                "adapter": adapter_text,
                "upstream": payload["upstream"],
                "required_inputs": payload["required_inputs"],
            }
        )

    tracks_root = skill_root.joinpath(*TRACKS_DIR.parts)
    if tracks_root.is_dir():
        for candidate in tracks_root.rglob("*.md"):
            if candidate.resolve() not in routed_paths:
                errors.append(
                    ContractFailure(
                        "orphan_adapter",
                        f"Adapter is not referenced by the route table: {candidate.relative_to(skill_root).as_posix()}",
                    )
                )

    sources_by_name = {}
    for track in tracks:
        upstream = track["upstream"]
        sources_by_name.setdefault(upstream["name"], set()).add(upstream["source"])
    for name, sources in sorted(sources_by_name.items()):
        if len(sources) > 1:
            errors.append(
                ContractFailure(
                    "upstream_identity_conflict",
                    f"Routed upstream {name} has conflicting sources: "
                    f"{', '.join(sorted(sources))}",
                )
            )

    dependencies = []
    seen_dependencies = set()
    required_inputs = []
    for track in tracks:
        identity = (track["upstream"]["name"], track["upstream"]["source"])
        if identity not in seen_dependencies:
            dependencies.append(
                {
                    "name": track["upstream"]["name"],
                    "source": track["upstream"]["source"],
                    "track_ids": [],
                }
            )
            seen_dependencies.add(identity)
        next(dep for dep in dependencies if (dep["name"], dep["source"]) == identity)[
            "track_ids"
        ].append(track["track_id"])
        for input_name in track["required_inputs"]:
            if input_name not in required_inputs:
                required_inputs.append(input_name)

    upstream_pins = {}
    if require_upstream or resolutions or normalized_hashes or exact_hashes or sizes:
        upstream_pins, upstream_errors = validate_upstream_resolutions(
            dependencies,
            resolutions,
            normalized_hashes,
            exact_hashes,
            sizes,
            validate_unknown=len(tracks) == len(rows),
        )
        errors.extend(upstream_errors)
        if errors:
            return None, errors

        for dependency in dependencies:
            pin = upstream_pins[(dependency["name"], dependency["source"])]
            dependency["resolved_uri"] = pin["uri"]
            dependency["kind"] = pin["kind"]
            dependency["sha256"] = pin["sha256"]
            dependency["source_sha256"] = pin["sha256"]
            dependency["size_bytes"] = pin["size_bytes"]
            if "normalized_sha256" in pin:
                dependency["normalized_sha256"] = pin["normalized_sha256"]

    routing_pin = exact_file_pin(routing_path)
    routing_pin["path"] = ROUTING_PATH
    adapter_pins = []
    for track in tracks:
        pin = exact_file_pin(skill_root / track["adapter"])
        pin["track_id"] = track["track_id"]
        pin["path"] = track["adapter"]
        adapter_pins.append(pin)
    result = {
        "status": "ready",
        "contract_version": CONTRACT_VERSION,
        "tracks": tracks,
        "dependencies": dependencies,
        "required_inputs": required_inputs,
        "pins": {
            "routing_table": routing_pin,
            "adapters": adapter_pins,
            "upstreams": [
                upstream_pins[(dependency["name"], dependency["source"])]
                for dependency in dependencies
            ] if upstream_pins else [],
        },
    }
    return result, []


def git_output(repo, *args, check=True):
    completed = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ContractFailure(
            "git_command_failed",
            f"git {' '.join(args)} failed: {detail}",
        )
    return completed


def resolve_commit(repo, ref):
    completed = git_output(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    return completed.stdout.decode("utf-8").strip()


def nul_paths(data):
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in data.split(b"\0")
        if item
    ]


def parse_git_range(value):
    match = re.fullmatch(r"(.+?)\.\.\.(.+)", value)
    if not match:
        raise ContractFailure(
            "range_invalid",
            "Git scope must use BASE...HEAD so review uses the merge-base.",
        )
    return match.group(1), match.group(2)


def safe_relative_path(value):
    normalized = value.replace("\\", "/")
    if "\x00" in normalized:
        raise ContractFailure("path_unsafe", f"Unsafe bundle path: {value}")
    path = PurePosixPath(normalized)
    if (
        path.is_absolute()
        or re.match(r"^[A-Za-z]:", normalized)
        or ".." in path.parts
        or not path.parts
    ):
        raise ContractFailure("path_unsafe", f"Unsafe bundle path: {value}")
    return path


def resolve_relative_under(root, value, code, label):
    try:
        relative = safe_relative_path(value)
    except ContractFailure as exc:
        raise ContractFailure(code, f"{label} path is unsafe: {exc.message}") from exc
    try:
        root = Path(root).resolve()
        candidate = root.joinpath(*relative.parts)
        resolved = candidate.resolve()
    except (OSError, RuntimeError) as exc:
        raise ContractFailure(
            code,
            f"{label} path cannot be resolved safely: {exc}",
        ) from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ContractFailure(
            code,
            f"{label} must stay inside {root}.",
        ) from exc
    return resolved


def normalize_exclusion(value):
    normalized = value.replace("\\", "/")
    if "\x00" in normalized:
        raise ContractFailure("exclusion_invalid", f"Unsafe exclusion path: {value}")
    path = PurePosixPath(normalized)
    if (
        path.is_absolute()
        or re.match(r"^[A-Za-z]:", normalized)
        or ".." in path.parts
        or not path.parts
    ):
        raise ContractFailure("exclusion_invalid", f"Unsafe exclusion path: {value}")
    return path.as_posix()


def is_excluded(value, exclusions):
    path = PurePosixPath(value).as_posix()
    return any(
        path == exclusion or path.startswith(f"{exclusion}/")
        for exclusion in exclusions
    )


def write_bundle_file(bundle, relative_path, data):
    relative = safe_relative_path(relative_path)
    target = bundle.joinpath(*relative.parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def copy_file_sources(source_root, paths, bundle):
    sources = []
    for value in sorted(set(paths)):
        relative = safe_relative_path(value)
        source = source_root.joinpath(*relative.parts)
        if source.is_symlink():
            raise ContractFailure(
                "tree_symlink_unsupported",
                f"Tree symlink is not frozen: {relative.as_posix()}",
            )
        if not source.is_file():
            continue
        data = source.read_bytes()
        write_bundle_file(bundle, f"tree/{relative.as_posix()}", data)
        sources.append(
            {
                "path": relative.as_posix(),
                "snapshot_path": f"tree/{relative.as_posix()}",
                "sha256": sha256_bytes(data),
                "size_bytes": len(data),
            }
        )
    return sources


def copy_git_tree(repo, head, paths, bundle):
    requested = {safe_relative_path(value).as_posix() for value in paths}
    sources = []
    for value in sorted(requested):
        relative = safe_relative_path(value)
        data = git_output(repo, "show", f"{head}:{relative.as_posix()}").stdout
        write_bundle_file(bundle, f"tree/{relative.as_posix()}", data)
        sources.append(
            {
                "path": relative.as_posix(),
                "snapshot_path": f"tree/{relative.as_posix()}",
                "sha256": sha256_bytes(data),
                "size_bytes": len(data),
            }
        )
    copied = {
        path.relative_to(bundle / "tree").as_posix()
        for path in (bundle / "tree").rglob("*")
        if path.is_file()
    }
    if copied != requested:
        missing = ", ".join(sorted(requested - copied)) or "none"
        unexpected = ", ".join(sorted(copied - requested)) or "none"
        raise ContractFailure(
            "tree_incomplete",
            "Copied Git tree paths do not match the requested paths: "
            f"missing: {missing}; unexpected: {unexpected}",
        )
    return sources


def collect_tree_root_paths(tree_root, exclusions):
    if not tree_root.is_dir():
        raise ContractFailure("tree_root_invalid", f"Tree root is not a directory: {tree_root}")
    paths = []
    for source in tree_root.rglob("*"):
        if ".git" in source.relative_to(tree_root).parts:
            continue
        if source.is_symlink():
            raise ContractFailure("tree_symlink_unsupported", f"Tree symlink is not frozen: {source}")
        if source.is_file():
            relative = source.relative_to(tree_root).as_posix()
            if not is_excluded(relative, exclusions):
                paths.append(relative)
    return paths


def copy_tree_root(tree_root, bundle, exclusions, paths=None):
    paths = paths if paths is not None else collect_tree_root_paths(tree_root, exclusions)
    sources = copy_file_sources(tree_root, paths, bundle)
    if not sources:
        raise ContractFailure("tree_required", "An explicit patch requires a non-empty frozen tree.")
    return [source["path"] for source in sources], sources


def validate_tree_post_image(patch, tree_root, paths):
    with tempfile.TemporaryDirectory(prefix="parallel-review-tree-") as temp_dir:
        snapshot = Path(temp_dir)
        for value in paths:
            relative = safe_relative_path(value)
            target = snapshot.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(tree_root.joinpath(*relative.parts), target)
        completed = subprocess.run(
            ["git", "-c", "core.quotePath=false", "apply", "--check", "--reverse", "-"],
            cwd=snapshot,
            input=patch,
            capture_output=True,
            check=False,
        )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ContractFailure(
            "tree_mismatch",
            f"The frozen tree is not the patch's exact post-image: {detail}",
        )


def run_git_apply_query(patch, *query_args):
    completed = subprocess.run(
        ["git", "-c", "core.quotePath=false", "apply", *query_args, "-"],
        input=patch,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ContractFailure(
            "patch_parse_failed",
            f"Git could not parse the patch without applying it: {detail}",
        )
    return completed.stdout


def parse_numstat_zero_output(output):
    records = []
    tokens = output.split(b"\0")
    index = 0
    while index < len(tokens):
        record = tokens[index]
        index += 1
        if not record:
            continue
        fields = record.split(b"\t", 2)
        if len(fields) != 3:
            raise ContractFailure("patch_parse_failed", "Malformed git --numstat record.")
        added, deleted, path = fields
        if not re.fullmatch(rb"(?:\d+|-)", added) or not re.fullmatch(rb"(?:\d+|-)", deleted):
            raise ContractFailure("patch_parse_failed", "Malformed git --numstat counts.")
        if path:
            records.append(
                {
                    "path": path.decode("utf-8", errors="surrogateescape"),
                    "old_path": None,
                }
            )
            continue
        if index + 1 >= len(tokens):
            raise ContractFailure("patch_parse_failed", "Renamed patch path is incomplete.")
        old_path = tokens[index].decode("utf-8", errors="surrogateescape")
        new_path = tokens[index + 1].decode("utf-8", errors="surrogateescape")
        index += 2
        records.append({"path": new_path, "old_path": old_path})
    return records


def decode_git_path(value):
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        try:
            decoded = codecs.escape_decode(value[1:-1].encode("ascii"))[0]
        except (UnicodeEncodeError, ValueError) as exc:
            raise ContractFailure(
                "patch_parse_failed",
                f"Cannot decode Git-quoted patch path: {value}",
            ) from exc
        return decoded.decode("utf-8", errors="surrogateescape")
    return value


def parse_rename_headers(patch):
    renames = []
    pending = None
    for raw_line in patch.decode("utf-8", errors="surrogateescape").splitlines():
        if raw_line.startswith("diff --git "):
            pending = None
            continue
        if raw_line.startswith(("rename from ", "copy from ")):
            kind = "rename" if raw_line.startswith("rename from ") else "copy"
            prefix = "rename from " if kind == "rename" else "copy from "
            path = raw_line[len(prefix):]
            pending = (kind, decode_git_path(path))
            continue
        if raw_line.startswith(("rename to ", "copy to ")):
            kind = "rename" if raw_line.startswith("rename to ") else "copy"
            prefix = "rename to " if kind == "rename" else "copy to "
            path = raw_line[len(prefix):]
            if pending is None or pending[0] != kind:
                raise ContractFailure("patch_parse_failed", "Rename patch header is incomplete.")
            renames.append(
                {
                    "kind": kind,
                    "old_path": pending[1],
                    "new_path": decode_git_path(path),
                }
            )
            pending = None
    if pending is not None:
        raise ContractFailure("patch_parse_failed", "Rename patch header is incomplete.")
    return renames


def parse_summary_paths(output):
    deleted = set()
    text = output.decode("utf-8", errors="surrogateescape")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("delete mode "):
            parts = line.split(" ", 3)
            if len(parts) == 4:
                deleted.add(decode_git_path(parts[3]))
            continue
    return deleted


def inspect_patch_paths(patch):
    numstat = run_git_apply_query(patch, "--numstat", "-z")
    summary = run_git_apply_query(patch, "--summary")
    records = parse_numstat_zero_output(numstat)
    summary_deleted = parse_summary_paths(summary)
    renames = parse_rename_headers(patch)

    changed = set()
    deleted = set(summary_deleted)
    for record in records:
        path = safe_relative_path(record["path"]).as_posix()
        changed.add(path)
        old_path = record["old_path"]
        if old_path:
            old_path = safe_relative_path(old_path).as_posix()
            changed.add(old_path)
            deleted.add(old_path)
    for rename in renames:
        old_path = safe_relative_path(rename["old_path"]).as_posix()
        new_path = safe_relative_path(rename["new_path"]).as_posix()
        changed.add(old_path)
        changed.add(new_path)
        if rename["kind"] == "rename":
            deleted.add(old_path)
    for path in summary_deleted:
        path = safe_relative_path(path).as_posix()
        deleted.add(path)
    return sorted(changed), {safe_relative_path(path).as_posix() for path in deleted}


def collect_inputs(paths, role, bundle):
    entries = []
    for index, value in enumerate(paths, start=1):
        path = Path(value).resolve()
        if not path.is_file():
            raise ContractFailure("manifest_input_missing", f"Missing {role} input: {path}")
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContractFailure(
                "manifest_input_invalid",
                f"{role} input is not UTF-8 text: {path}",
            ) from exc
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        snapshot_path = f"inputs/{role}/{index:03d}-{path.name}"
        write_bundle_file(bundle, snapshot_path, data)
        entries.append(
            {
                "path": str(path),
                "role": role,
                "sha256": sha256_bytes(data),
                "normalized_sha256": sha256_bytes(normalized),
                "size_bytes": len(data),
                "snapshot_path": snapshot_path,
            }
        )
    return entries


def parse_named_values(values, code):
    parsed = []
    for value in values:
        name, separator, detail = value.partition("=")
        if not separator or not name.strip() or not detail.strip():
            raise ContractFailure(code, f"Expected NAME=VALUE, got: {value}")
        parsed.append((name.strip(), detail.strip()))
    return parsed


def collect_checks(check_values, not_run_values):
    checks = []
    for name, result in parse_named_values(check_values, "check_invalid"):
        if result not in CHECK_RESULTS:
            raise ContractFailure(
                "check_invalid",
                f"Unknown check result for {name}: {result}",
            )
        checks.append(
            {"name": name, "command": "", "result": result, "reason": ""}
        )
    for name, reason in parse_named_values(not_run_values, "check_invalid"):
        checks.append(
            {"name": name, "command": "", "result": "not_run", "reason": reason}
        )
    return checks


def collect_exclusions(values):
    exclusions = []
    for path, reason in parse_named_values(values, "exclusion_invalid"):
        exclusions.append({"path": normalize_exclusion(path), "reason": reason})
    return exclusions


def reject_excluded_patch_paths(patch_paths, exclusions):
    excluded = [path for path in patch_paths if is_excluded(path, exclusions)]
    if excluded:
        raise ContractFailure(
            "excluded_path_in_patch",
            f"The patch changes excluded paths: {', '.join(sorted(excluded))}",
        )


def output_outside_repo(repo, output):
    if repo is None:
        probe = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(Path.cwd()),
            capture_output=True,
            check=False,
        )
        if probe.returncode == 0:
            repo = Path(probe.stdout.decode("utf-8").strip())
    if repo is None:
        return
    repo_path = repo.resolve()
    output_path = output.resolve()
    try:
        common = os.path.commonpath([str(repo_path), str(output_path)])
    except ValueError:
        return
    if os.path.normcase(common) == os.path.normcase(str(repo_path)):
        raise ContractFailure(
            "output_inside_repository",
            "The frozen bundle must be written outside the reviewed repository.",
        )


def git_top_level(path):
    completed = subprocess.run(
        ["git", "-C", str(Path(path).resolve()), "rev-parse", "--show-toplevel"],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return Path(completed.stdout.decode("utf-8").strip())


def resolve_repo_root(path):
    top_level = git_top_level(path)
    if top_level is None:
        raise ContractFailure(
            "repo_invalid",
            f"Repository input is not inside a Git work tree: {path}",
        )
    return top_level.resolve()


def ensure_output_outside_sources(output, source_roots):
    if output.exists() or output.is_symlink():
        raise ContractFailure("output_exists", f"Refusing to overwrite bundle: {output}")
    for source_root in source_roots:
        source = Path(source_root).resolve()
        try:
            common = os.path.commonpath([str(source), str(output)])
        except ValueError:
            continue
        if os.path.normcase(common) == os.path.normcase(str(source)):
            raise ContractFailure(
                "output_inside_source",
                f"The bundle path overlaps source: {source}",
            )


def validate_freeze_sources(args, repo, output):
    errors = []
    source_roots = []
    if repo:
        source_roots.append(repo)
    if args.tree_root:
        source_roots.append(args.tree_root)
    if args.contract_root:
        source_roots.append(args.contract_root)
    output_outside_repo(repo, output)
    if args.tree_root:
        tree_repo = git_top_level(args.tree_root)
        if tree_repo is not None and (
            repo is None or tree_repo.resolve() != repo.resolve()
        ):
            output_outside_repo(tree_repo, output)
    ensure_output_outside_sources(output, source_roots)

    if args.patch:
        supplied_patch = Path(args.patch)
        patch_path = supplied_patch.resolve()
        if supplied_patch.is_symlink() or not patch_path.is_file():
            raise ContractFailure("patch_missing", f"Patch is not a regular file: {patch_path}")
    if args.tree_root:
        tree_root = Path(args.tree_root)
        if tree_root.is_symlink() or not tree_root.resolve().is_dir():
            raise ContractFailure(
                "tree_root_invalid",
                f"Tree root is not a regular directory: {args.tree_root}",
            )
    for path in args.requirements + args.standards:
        supplied_source = Path(path)
        source = supplied_source.resolve()
        if supplied_source.is_symlink() or not source.is_file():
            errors.append(
                ContractFailure(
                    "manifest_input_missing",
                    f"Missing regular input file: {source}",
                )
            )
            continue
        try:
            source.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            errors.append(
                ContractFailure(
                    "manifest_input_invalid",
                    f"Cannot read UTF-8 manifest input: {source}",
                )
            )
    if args.contract_root:
        try:
            contract, contract_errors = collect_preflight(
                Path(args.contract_root).resolve(),
                upstream_values=args.upstream,
                upstream_normalized_hashes=args.upstream_sha,
                upstream_exact_hashes=args.upstream_exact_sha,
                upstream_sizes=args.upstream_size,
            )
        except ContractFailure as exc:
            errors.append(exc)
            return errors, None
        errors.extend(contract_errors)
        return errors, contract
    return errors, None


def validate_required_inputs(contract, args, checks):
    if not contract:
        return
    availability = {
        "patch": bool(args.range_value or args.patch or args.uncommitted),
        "tree": bool(repo_arg(args) or args.tree_root),
        "requirements": bool(args.requirements),
        "standards": bool(args.standards),
        "checks": bool(checks),
        "exclusions": True,
    }
    missing = [
        input_name
        for input_name in contract["required_inputs"]
        if not availability.get(input_name, False)
    ]
    if missing:
        raise ContractFailure(
            "manifest_input_missing",
            f"Required manifest inputs were not supplied: {', '.join(missing)}",
        )


def repo_arg(args):
    if args.repo:
        return args.repo
    if args.uncommitted or args.range_value:
        return Path.cwd()
    return None


def verify_live_uncommitted(repo, scope, patch, exclusions):
    current_head = resolve_commit(repo, "HEAD")
    if current_head != scope["head"]:
        return ["HEAD changed while the uncommitted scope was being frozen."]
    current_scope, current_patch = build_uncommitted_scope(
        repo,
        exclusions=exclusions,
    )
    reasons = []
    if current_patch != patch:
        reasons.append("The uncommitted patch changed while the bundle was being frozen.")
    if current_scope["included_paths"] != scope["included_paths"]:
        reasons.append("The included path set changed while the bundle was being frozen.")
    for source in scope["tree_sources"]:
        live_path = repo.joinpath(*safe_relative_path(source["path"]).parts)
        if not live_path.is_file() or live_path.is_symlink():
            reasons.append(f"An uncommitted source disappeared: {source['path']}")
            continue
        try:
            data = live_path.read_bytes()
        except OSError:
            reasons.append(f"An uncommitted source became unreadable: {source['path']}")
            continue
        if len(data) != source["size_bytes"]:
            reasons.append(f"An uncommitted source size changed: {source['path']}")
        if sha256_bytes(data) != source["sha256"]:
            reasons.append(f"An uncommitted source changed: {source['path']}")
    return reasons


def build_git_range_scope(repo, range_value, bundle=None, exclusions=None):
    exclusions = exclusions or []
    base_ref, head_ref = parse_git_range(range_value)
    base = resolve_commit(repo, base_ref)
    head = resolve_commit(repo, head_ref)
    merge_base = git_output(repo, "merge-base", base, head).stdout.decode("utf-8").strip()
    patch = git_output(
        repo,
        "diff",
        "--binary",
        "--no-ext-diff",
        f"{base}...{head}",
        "--",
    ).stdout
    changed_paths, _ = inspect_patch_paths(patch)
    reject_excluded_patch_paths(changed_paths, exclusions)
    tree_paths = nul_paths(
        git_output(repo, "ls-tree", "-r", "--name-only", "-z", head).stdout
    )
    included_tree_paths = [
        path for path in tree_paths if not is_excluded(path, exclusions)
    ]
    included_paths = sorted(set(included_tree_paths) | set(changed_paths))
    tree_sources = (
        copy_git_tree(repo, head, included_tree_paths, bundle) if bundle else []
    )
    return {
        "kind": "git_range",
        "base": base,
        "head": head,
        "merge_base": merge_base,
        "patch": {
            "path": PATCH_PATH,
            "sha256": sha256_bytes(patch),
            "size_bytes": len(patch),
        },
        "included_paths": included_paths,
        "tree_sources": tree_sources,
    }, patch


def verify_live_git_range(repo, scope, patch, exclusions):
    try:
        current_scope, current_patch = build_git_range_scope(
            repo,
            f"{scope['base']}...{scope['head']}",
            exclusions=exclusions,
        )
    except ContractFailure as exc:
        return [f"The Git-range scope became unreadable: {exc.message}"]

    reasons = []
    if any(
        current_scope[field] != scope[field]
        for field in ("base", "head", "merge_base")
    ):
        reasons.append("The Git-range Git identities changed after the freeze.")
    if current_scope["included_paths"] != scope["included_paths"]:
        reasons.append("The Git-range included paths changed after the freeze.")
    if current_patch != patch:
        reasons.append("The reviewed scope changed after the freeze.")

    head_tree_paths = {
        path
        for path in nul_paths(
            git_output(repo, "ls-tree", "-r", "--name-only", "-z", scope["head"]).stdout
        )
        if not is_excluded(path, exclusions)
    }
    if head_tree_paths != {source["path"] for source in scope["tree_sources"]}:
        reasons.append("The exact head tree path set changed after the freeze.")

    for source in scope["tree_sources"]:
        relative = safe_relative_path(source["path"]).as_posix()
        try:
            data = git_output(repo, "show", f"{scope['head']}:{relative}").stdout
        except ContractFailure:
            reasons.append(f"A Git-range source disappeared: {relative}")
            continue
        if len(data) != source["size_bytes"]:
            reasons.append(f"A Git-range source size changed: {relative}")
        if sha256_bytes(data) != source["sha256"]:
            reasons.append(f"A Git-range source changed: {relative}")
    return reasons


def build_explicit_patch_scope(patch_path, tree_root, bundle, exclusions):
    if patch_path is None:
        raise ContractFailure("patch_missing", "An explicit patch path is required.")
    source = patch_path.resolve()
    if not source.is_file():
        raise ContractFailure("patch_missing", f"Patch is not a readable file: {source}")
    patch = source.read_bytes()
    if not patch:
        raise ContractFailure("patch_empty", "The explicit patch is empty.")
    if tree_root is None:
        raise ContractFailure(
            "tree_required",
            "An explicit patch requires --tree-root for the frozen code bundle.",
        )
    patch_paths, deleted_paths = inspect_patch_paths(patch)
    reject_excluded_patch_paths(patch_paths, exclusions)
    tree_root = tree_root.resolve()
    tree_paths = collect_tree_root_paths(tree_root, exclusions)
    missing = sorted(set(patch_paths) - deleted_paths - set(tree_paths))
    if missing:
        raise ContractFailure(
            "tree_incomplete",
            f"The frozen tree is missing changed paths: {', '.join(missing)}",
        )
    validate_tree_post_image(patch, tree_root, tree_paths)
    _, tree_sources = copy_tree_root(tree_root, bundle, exclusions, tree_paths)
    included_paths = sorted(set(patch_paths) | set(tree_paths))
    return {
        "kind": "explicit_patch",
        "base": None,
        "head": None,
        "merge_base": None,
        "patch": {
            "path": PATCH_PATH,
            "sha256": sha256_bytes(patch),
            "size_bytes": len(patch),
        },
        "included_paths": included_paths,
        "tree_sources": tree_sources,
    }, patch


def build_uncommitted_scope(repo, bundle=None, exclusions=None):
    exclusions = exclusions or []
    head = resolve_commit(repo, "HEAD")
    untracked = nul_paths(
        git_output(repo, "ls-files", "--others", "--exclude-standard", "-z").stdout
    )
    tree_paths = nul_paths(
        git_output(
            repo,
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ).stdout
    )
    patch_parts = [
        git_output(repo, "diff", "--binary", "--no-ext-diff", "HEAD", "--").stdout
    ]
    for value in untracked:
        completed = git_output(
            repo,
            "diff",
            "--no-index",
            "--binary",
            "--",
            "/dev/null",
            value,
            check=False,
        )
        if completed.returncode not in (0, 1):
            raise ContractFailure(
                "git_command_failed",
                f"Could not diff untracked file: {value}",
            )
        patch_parts.append(completed.stdout)
    patch = b"\n".join(part for part in patch_parts if part)
    changed_paths, _ = inspect_patch_paths(patch)
    reject_excluded_patch_paths(changed_paths, exclusions)
    reject_excluded_patch_paths(untracked, exclusions)
    included_tree_paths = [
        path for path in tree_paths if not is_excluded(path, exclusions)
    ]
    included_paths = sorted(set(included_tree_paths) | set(changed_paths) | set(untracked))
    tree_sources = (
        copy_file_sources(repo, included_tree_paths, bundle) if bundle else []
    )
    return {
        "kind": "frozen_uncommitted",
        "base": head,
        "head": head,
        "merge_base": head,
        "patch": {
            "path": PATCH_PATH,
            "sha256": sha256_bytes(patch),
            "size_bytes": len(patch),
        },
        "included_paths": included_paths,
        "tree_sources": tree_sources,
    }, patch


def manifest_input_status(scope, inputs, checks):
    roles = {entry["role"] for entry in inputs}
    return {
        "patch": "included",
        "tree": "included" if scope["tree_sources"] else "not_assessed",
        "requirements": "included" if "requirements" in roles else "not_assessed",
        "standards": "included" if "standards" in roles else "not_assessed",
        "checks": "recorded" if checks else "not_assessed",
        "exclusions": "recorded",
    }


def command_freeze(args):
    output = Path(args.output).resolve()
    repo = resolve_repo_root(Path(args.repo)) if args.repo else None
    exclusions = collect_exclusions(args.exclude)
    exclusion_paths = [entry["path"] for entry in exclusions]
    errors, contract = validate_freeze_sources(args, repo, output)
    if errors:
        return error_payload(errors), 1
    if not args.contract_root:
        raise ContractFailure(
            "contract_root_required",
            "Freeze requires --contract-root with an explicit --upstream resolution.",
        )
    checks = collect_checks(args.check, args.not_run)
    validate_required_inputs(contract, args, checks)

    if args.range_value:
        if repo is None:
            raise ContractFailure("repo_required", "--range requires --repo.")
        scope, patch = build_git_range_scope(
            repo,
            args.range_value,
            output,
            exclusion_paths,
        )
    elif args.patch:
        scope, patch = build_explicit_patch_scope(
            Path(args.patch),
            Path(args.tree_root) if args.tree_root else None,
            output,
            exclusion_paths,
        )
    else:
        if repo is None:
            raise ContractFailure("repo_required", "--uncommitted requires --repo.")
        scope, patch = build_uncommitted_scope(repo, output, exclusion_paths)

    if not patch:
        raise ContractFailure("patch_empty", "The frozen scope produced an empty patch.")
    inputs = []
    inputs.extend(collect_inputs(args.requirements, "requirements", output))
    inputs.extend(collect_inputs(args.standards, "standards", output))
    input_status = manifest_input_status(scope, inputs, checks)
    manifest = {
        "contract_version": CONTRACT_VERSION,
        "scope": scope,
        "inputs": inputs,
        "input_status": input_status,
        "checks": checks,
        "exclusions": exclusions,
        "input_registry": sorted(REQUIRED_INPUTS),
    }
    if contract:
        unresolved = [
            input_name
            for input_name in contract["required_inputs"]
            if input_status.get(input_name) in {None, "not_assessed"}
        ]
        if unresolved:
            raise ContractFailure(
                "manifest_input_missing",
                f"Unresolved required manifest inputs: {', '.join(unresolved)}",
            )
        manifest["contract"] = contract

    if args.uncommitted:
        live_reasons = verify_live_uncommitted(
            repo,
            scope,
            patch,
            exclusion_paths,
        )
        if live_reasons:
            return {"status": "stale", "reasons": live_reasons}, 1

    write_bundle_file(output, PATCH_PATH, patch)
    manifest_bytes = canonical_json_bytes(manifest)
    manifest_sha256 = sha256_bytes(manifest_bytes)
    attestation = {
        "contract_version": CONTRACT_VERSION,
        "manifest_sha256": manifest_sha256,
        "patch_sha256": scope["patch"]["sha256"],
        "patch_size_bytes": scope["patch"]["size_bytes"],
        "included_paths": scope["included_paths"],
    }
    (output / "manifest.json").write_bytes(manifest_bytes)
    (output / "attestation.json").write_bytes(canonical_json_bytes(attestation))
    return {
        "status": "frozen",
        "bundle": str(output),
        "manifest_sha256": manifest_sha256,
        "patch_sha256": scope["patch"]["sha256"],
        "patch_size_bytes": scope["patch"]["size_bytes"],
        "scope_sha256": scope_sha256(scope),
        "included_paths": scope["included_paths"],
    }, 0


def bundle_require_fields(payload, fields, label):
    if not isinstance(payload, dict) or not set(fields) <= set(payload):
        raise ContractFailure(
            "bundle_invalid",
            f"{label} is missing required fields: {', '.join(sorted(fields))}",
        )


def bundle_require_text(payload, field, label):
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContractFailure(
            "bundle_invalid",
            f"{label}.{field} must be a non-empty string.",
        )
    return value


def bundle_require_hash(payload, field, label):
    value = bundle_require_text(payload, field, label)
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ContractFailure(
            "bundle_invalid",
            f"{label}.{field} must be an exact SHA-256.",
        )
    return value


def bundle_require_size(payload, field, label, positive=False):
    value = payload.get(field)
    minimum = 1 if positive else 0
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractFailure(
            "bundle_invalid",
            f"{label}.{field} must be a non-negative integer.",
        )
    return value


def bundle_require_relative_path(payload, field, label):
    value = bundle_require_text(payload, field, label)
    try:
        return safe_relative_path(value).as_posix()
    except ContractFailure as exc:
        raise ContractFailure(
            "bundle_invalid",
            f"{label}.{field} is unsafe: {value}",
        ) from exc


def validate_manifest_scope(scope):
    if not isinstance(scope, dict):
        raise ContractFailure("bundle_invalid", "Manifest scope must be an object.")
    kind = scope.get("kind")
    if kind not in {"git_range", "explicit_patch", "frozen_uncommitted"}:
        raise ContractFailure("bundle_invalid", "Manifest scope.kind is unsupported.")
    for field in ("base", "head", "merge_base"):
        if field not in scope:
            raise ContractFailure(
                "bundle_invalid",
                f"Manifest scope is missing {field} for {kind}.",
            )
    if kind == "explicit_patch":
        if any(scope[field] is not None for field in ("base", "head", "merge_base")):
            raise ContractFailure(
                "bundle_invalid",
                "Explicit-patch Git identities must be null.",
            )
    else:
        for field in ("base", "head", "merge_base"):
            bundle_require_text(scope, field, "scope")

    patch = scope.get("patch")
    bundle_require_fields(patch, {"path", "sha256", "size_bytes"}, "scope.patch")
    bundle_require_relative_path(patch, "path", "scope.patch")
    bundle_require_hash(patch, "sha256", "scope.patch")
    bundle_require_size(patch, "size_bytes", "scope.patch", positive=True)

    included_paths = scope.get("included_paths")
    if (
        not isinstance(included_paths, list)
        or any(not isinstance(path, str) or not path.strip() for path in included_paths)
        or len(included_paths) != len(set(included_paths))
    ):
        raise ContractFailure(
            "bundle_invalid",
            "Manifest scope.included_paths must contain unique non-empty paths.",
        )
    for path in included_paths:
        try:
            safe_relative_path(path)
        except ContractFailure as exc:
            raise ContractFailure(
                "bundle_invalid",
                f"Manifest included path is unsafe: {path}",
            ) from exc
    if not included_paths:
        raise ContractFailure(
            "bundle_invalid",
            "Manifest scope.included_paths must not be empty.",
        )

    tree_sources = scope.get("tree_sources")
    if not isinstance(tree_sources, list):
        raise ContractFailure(
            "bundle_invalid",
            "Manifest scope.tree_sources must be a list.",
        )
    for source in tree_sources:
        bundle_require_fields(
            source,
            {"path", "snapshot_path", "sha256", "size_bytes"},
            "scope.tree_sources[]",
        )
        bundle_require_relative_path(source, "path", "scope.tree_sources[]")
        bundle_require_relative_path(source, "snapshot_path", "scope.tree_sources[]")
        bundle_require_hash(source, "sha256", "scope.tree_sources[]")
        bundle_require_size(source, "size_bytes", "scope.tree_sources[]")


def validate_manifest_contract(contract):
    bundle_require_fields(
        contract,
        {"tracks", "dependencies", "required_inputs", "pins"},
        "contract",
    )
    if not isinstance(contract["tracks"], list):
        raise ContractFailure("bundle_invalid", "contract.tracks must be a list.")
    for track in contract["tracks"]:
        bundle_require_fields(
            track,
            {"track_id", "adapter", "upstream", "required_inputs"},
            "contract.tracks[]",
        )
        bundle_require_text(track, "track_id", "contract.tracks[]")
        bundle_require_text(track, "adapter", "contract.tracks[]")
        bundle_require_fields(
            track["upstream"],
            {"name", "source"},
            "contract.tracks[].upstream",
        )
        if not isinstance(track["required_inputs"], list):
            raise ContractFailure(
                "bundle_invalid",
                "contract.tracks[].required_inputs must be a list.",
            )
        if (
            any(
                not isinstance(value, str) or value not in REQUIRED_INPUTS
                for value in track["required_inputs"]
            )
            or len(track["required_inputs"]) != len(set(track["required_inputs"]))
        ):
            raise ContractFailure(
                "bundle_invalid",
                "contract.tracks[].required_inputs must contain unique known inputs.",
            )
    expected_required_inputs = []
    for track in contract["tracks"]:
        for input_name in track["required_inputs"]:
            if input_name not in expected_required_inputs:
                expected_required_inputs.append(input_name)
    if contract["required_inputs"] != expected_required_inputs:
        raise ContractFailure(
            "bundle_invalid",
            "contract.required_inputs does not match the routed adapters.",
        )
    pins = contract["pins"]
    bundle_require_fields(
        pins,
        {"routing_table", "adapters", "upstreams"},
        "contract.pins",
    )
    for label, pin in (("routing_table", pins["routing_table"]),):
        bundle_require_fields(
            pin,
            {"path", "sha256", "size_bytes", "normalized_sha256"},
            f"contract.pins.{label}",
        )
        bundle_require_hash(pin, "sha256", f"contract.pins.{label}")
        bundle_require_size(pin, "size_bytes", f"contract.pins.{label}")
    for label in ("adapters", "upstreams"):
        if not isinstance(pins[label], list):
            raise ContractFailure(
                "bundle_invalid",
                f"contract.pins.{label} must be a list.",
            )
        for pin in pins[label]:
            bundle_require_fields(pin, {"sha256", "size_bytes"}, f"contract.pins.{label}[]")
            bundle_require_hash(pin, "sha256", f"contract.pins.{label}[]")
            bundle_require_size(pin, "size_bytes", f"contract.pins.{label}[]")
            if label == "upstreams":
                bundle_require_fields(
                    pin,
                    {"name", "source", "kind", "uri"},
                    "contract.pins.upstreams[]",
                )
                bundle_require_text(pin, "name", "contract.pins.upstreams[]")
                bundle_require_text(pin, "source", "contract.pins.upstreams[]")
                bundle_require_text(pin, "uri", "contract.pins.upstreams[]")
                kind = bundle_require_text(pin, "kind", "contract.pins.upstreams[]")
                if kind not in {
                    "local_file",
                    "local_directory",
                    "remote_uri",
                }:
                    raise ContractFailure(
                        "bundle_invalid",
                        "contract.pins.upstreams[].kind is unsupported.",
                    )


def validate_manifest_input_consistency(manifest):
    scope = manifest["scope"]
    inputs = manifest["inputs"]
    checks = manifest["checks"]
    input_status = manifest["input_status"]
    roles = {entry["role"] for entry in inputs}
    unknown_roles = sorted(roles - {"requirements", "standards"})
    if unknown_roles:
        raise ContractFailure(
            "bundle_invalid",
            f"Manifest inputs use unsupported roles: {', '.join(unknown_roles)}",
        )

    expected_status = manifest_input_status(scope, inputs, checks)
    mismatched = sorted(
        name
        for name in REQUIRED_INPUTS
        if input_status[name] != expected_status[name]
    )
    if mismatched:
        raise ContractFailure(
            "bundle_invalid",
            "Manifest input_status does not match frozen content: "
            f"{', '.join(mismatched)}",
        )

    backing = {
        "patch": True,
        "tree": bool(scope["tree_sources"]),
        "requirements": "requirements" in roles,
        "standards": "standards" in roles,
        "checks": bool(checks),
        "exclusions": isinstance(manifest["exclusions"], list),
    }
    for input_name, state in input_status.items():
        if state == "included" and not backing[input_name]:
            raise ContractFailure(
                "bundle_invalid",
                f"Input status included has no frozen input: {input_name}",
            )
        if state == "recorded" and input_name == "checks" and not checks:
            raise ContractFailure(
                "bundle_invalid",
                "Input status recorded has no check records.",
            )
        if state == "not_assessed" and backing[input_name]:
            raise ContractFailure(
                "bundle_invalid",
                f"Input status not_assessed has frozen input: {input_name}",
            )

    for track in manifest["contract"]["tracks"]:
        for input_name in track["required_inputs"]:
            state = input_status[input_name]
            if input_name == "checks":
                if state != "recorded" or not checks:
                    raise ContractFailure(
                        "bundle_invalid",
                        f"Routed track {track['track_id']} requires check records.",
                    )
            elif input_name == "exclusions":
                if state != "recorded":
                    raise ContractFailure(
                        "bundle_invalid",
                        f"Routed track {track['track_id']} requires exclusions recorded.",
                    )
            elif state != "included":
                raise ContractFailure(
                    "bundle_invalid",
                    f"Routed track {track['track_id']} requires included input: {input_name}",
                )


def validate_manifest_shape(manifest):
    bundle_require_fields(
        manifest,
        {
            "contract_version",
            "scope",
            "inputs",
            "input_status",
            "checks",
            "exclusions",
            "input_registry",
            "contract",
        },
        "manifest",
    )
    validate_manifest_scope(manifest["scope"])

    inputs = manifest["inputs"]
    if not isinstance(inputs, list):
        raise ContractFailure("bundle_invalid", "Manifest inputs must be a list.")
    for entry in inputs:
        bundle_require_fields(
            entry,
            {"path", "role", "sha256", "normalized_sha256", "size_bytes", "snapshot_path"},
            "inputs[]",
        )
        bundle_require_text(entry, "path", "inputs[]")
        bundle_require_text(entry, "role", "inputs[]")
        bundle_require_hash(entry, "sha256", "inputs[]")
        bundle_require_hash(entry, "normalized_sha256", "inputs[]")
        bundle_require_size(entry, "size_bytes", "inputs[]")
        bundle_require_relative_path(entry, "snapshot_path", "inputs[]")

    input_status = manifest["input_status"]
    if not isinstance(input_status, dict):
        raise ContractFailure("bundle_invalid", "Manifest input_status must be an object.")
    if set(input_status) != REQUIRED_INPUTS:
        raise ContractFailure(
            "bundle_invalid",
            "Manifest input_status must cover the input registry exactly.",
        )
    if any(
        not isinstance(value, str)
        or value not in {"included", "recorded", "not_assessed"}
        for value in input_status.values()
    ):
        raise ContractFailure("bundle_invalid", "Manifest input_status has an unknown value.")

    checks = manifest["checks"]
    if not isinstance(checks, list):
        raise ContractFailure("bundle_invalid", "Manifest checks must be a list.")
    for check in checks:
        bundle_require_fields(
            check,
            {"name", "command", "result", "reason"},
            "checks[]",
        )
        bundle_require_text(check, "name", "checks[]")
        if not isinstance(check["command"], str) or not isinstance(check["reason"], str):
            raise ContractFailure(
                "bundle_invalid",
                "Manifest check command and reason must be strings.",
            )
        if (
            not isinstance(check["result"], str)
            or check["result"] not in CHECK_RESULTS | {"not_run"}
        ):
            raise ContractFailure("bundle_invalid", "Manifest check result is unknown.")
        if check["result"] == "not_run" and not check["reason"].strip():
            raise ContractFailure(
                "bundle_invalid",
                "Manifest not_run checks require a non-empty reason.",
            )

    exclusions = manifest["exclusions"]
    if not isinstance(exclusions, list):
        raise ContractFailure("bundle_invalid", "Manifest exclusions must be a list.")
    for entry in exclusions:
        bundle_require_fields(entry, {"path", "reason"}, "exclusions[]")
        bundle_require_text(entry, "path", "exclusions[]")
        bundle_require_text(entry, "reason", "exclusions[]")

    input_registry = manifest["input_registry"]
    if (
        not isinstance(input_registry, list)
        or any(not isinstance(value, str) for value in input_registry)
        or set(input_registry) != REQUIRED_INPUTS
    ):
        raise ContractFailure(
            "bundle_invalid",
            "Manifest input_registry must list the required input categories.",
        )
    validate_manifest_contract(manifest["contract"])
    validate_manifest_input_consistency(manifest)


def load_bundle(bundle):
    manifest_path = bundle / "manifest.json"
    attestation_path = bundle / "attestation.json"
    if not manifest_path.is_file() or not attestation_path.is_file():
        raise ContractFailure("bundle_invalid", "Bundle is missing manifest or attestation.")
    manifest_bytes = manifest_path.read_bytes()
    try:
        manifest = json.loads(manifest_bytes)
        attestation = json.loads(attestation_path.read_bytes())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ContractFailure("bundle_invalid", f"Bundle JSON is malformed: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(attestation, dict):
        raise ContractFailure("bundle_invalid", "Manifest and attestation must be JSON objects.")
    if canonical_json_bytes(manifest) != manifest_bytes:
        raise ContractFailure("bundle_invalid", "Manifest is not canonical JSON.")
    validate_manifest_shape(manifest)
    if set(attestation) != {
        "contract_version",
        "manifest_sha256",
        "patch_sha256",
        "patch_size_bytes",
        "included_paths",
    }:
        raise ContractFailure("bundle_invalid", "Attestation fields are incomplete or unknown.")
    manifest_version = manifest.get("contract_version")
    if (
        isinstance(manifest_version, bool)
        or not isinstance(manifest_version, int)
        or manifest_version != CONTRACT_VERSION
    ):
        raise ContractFailure("bundle_version_mismatch", "Manifest contract_version is unsupported.")
    attestation_version = attestation.get("contract_version")
    if (
        isinstance(attestation_version, bool)
        or not isinstance(attestation_version, int)
        or attestation_version != CONTRACT_VERSION
    ):
        raise ContractFailure("bundle_version_mismatch", "Attestation contract_version is unsupported.")
    if (
        not isinstance(attestation.get("manifest_sha256"), str)
        or not isinstance(attestation.get("patch_sha256"), str)
        or isinstance(attestation.get("patch_size_bytes"), bool)
        or not isinstance(attestation.get("patch_size_bytes"), int)
        or not isinstance(attestation.get("included_paths"), list)
    ):
        raise ContractFailure("bundle_invalid", "Attestation fields have invalid types.")
    return manifest, manifest_bytes, attestation


def verify_bundle_integrity(bundle, manifest):
    reasons = []
    scope = manifest.get("scope", {})
    patch_entry = scope.get("patch", {})
    patch_relative = patch_entry.get("path", "")
    try:
        patch_path = bundle.joinpath(*safe_relative_path(patch_relative).parts)
    except ContractFailure:
        return ["The manifest patch path is unsafe."]
    if not patch_path.is_file():
        return ["The frozen patch is missing."]
    try:
        patch = patch_path.read_bytes()
    except OSError:
        return ["The frozen patch is unreadable."]
    if sha256_bytes(patch) != patch_entry.get("sha256"):
        reasons.append("The frozen patch hash changed.")
    if len(patch) != patch_entry.get("size_bytes"):
        reasons.append("The frozen patch size changed.")

    for source in scope.get("tree_sources", []):
        try:
            path = bundle.joinpath(*safe_relative_path(source["snapshot_path"]).parts)
        except (ContractFailure, KeyError):
            reasons.append("A tree source path is invalid.")
            continue
        if not path.is_file():
            reasons.append(f"Frozen tree source is missing: {source.get('path', '')}")
            continue
        try:
            data = path.read_bytes()
        except OSError:
            reasons.append(f"Frozen tree source is unreadable: {source.get('path', '')}")
            continue
        if sha256_bytes(data) != source.get("sha256") or len(data) != source.get("size_bytes"):
            reasons.append(f"Frozen tree source changed: {source.get('path', '')}")

    for entry in manifest.get("inputs", []):
        try:
            path = bundle.joinpath(*safe_relative_path(entry["snapshot_path"]).parts)
        except (ContractFailure, KeyError):
            reasons.append("A manifest input path is invalid.")
            continue
        if not path.is_file():
            reasons.append(f"Pinned input is missing: {entry.get('path', '')}")
            continue
        try:
            data = path.read_bytes()
        except OSError:
            reasons.append(f"Pinned input is unreadable: {entry.get('path', '')}")
            continue
        if len(data) != entry.get("size_bytes"):
            reasons.append(f"Pinned input size changed: {entry.get('path', '')}")
        if sha256_bytes(data) != entry.get("sha256"):
            reasons.append(f"Pinned input changed: {entry.get('path', '')}")
    return reasons


def verify_manifest_input_sources(manifest):
    reasons = []
    for entry in manifest.get("inputs", []):
        path = Path(entry["path"])
        try:
            data = path.read_bytes()
        except (OSError, ValueError):
            reasons.append(
                f"Original pinned input source is missing or unreadable: {entry['path']}"
            )
            continue
        if len(data) != entry["size_bytes"]:
            reasons.append(f"Original pinned input source size changed: {entry['path']}")
        if sha256_bytes(data) != entry["sha256"]:
            reasons.append(f"Original pinned input source changed: {entry['path']}")
    return reasons


def verify_live_explicit_patch(patch_path, scope):
    try:
        data = Path(patch_path).resolve().read_bytes()
    except (OSError, RuntimeError, ValueError):
        return [f"The explicit patch is missing or unreadable: {patch_path}"]
    reasons = []
    if len(data) != scope["patch"]["size_bytes"]:
        reasons.append("The explicit patch size changed after the freeze.")
    if sha256_bytes(data) != scope["patch"]["sha256"]:
        reasons.append("The explicit patch changed after the freeze.")
    return reasons


def attestation_mismatch_reasons(manifest_bytes, manifest, attestation):
    reasons = []
    scope = manifest.get("scope", {})
    if attestation.get("manifest_sha256") != sha256_bytes(manifest_bytes):
        reasons.append("The manifest digest does not match its attestation.")
    if attestation.get("patch_sha256") != scope.get("patch", {}).get("sha256"):
        reasons.append("The patch attestation does not match the manifest.")
    if attestation.get("patch_size_bytes") != scope.get("patch", {}).get("size_bytes"):
        reasons.append("The patch size attestation does not match the manifest.")
    if attestation.get("included_paths") != scope.get("included_paths"):
        reasons.append("The included-path attestation does not match the manifest.")
    return reasons


def command_verify(args):
    if not args.contract_root:
        raise ContractFailure(
            "contract_root_required",
            "Verify requires --contract-root with an explicit --upstream resolution.",
        )
    if not args.upstream:
        raise ContractFailure(
            "upstream_unresolved",
            "Verify requires the frozen upstream resolution explicitly.",
        )
    bundle = Path(args.bundle).resolve()
    manifest, manifest_bytes, attestation = load_bundle(bundle)
    scope = manifest.get("scope", {})
    kind = scope.get("kind")
    if kind == "frozen_uncommitted" and not args.repo:
        raise ContractFailure(
            "repo_required",
            "Verify requires --repo for a frozen uncommitted scope.",
        )
    if kind == "git_range" and not args.repo:
        raise ContractFailure(
            "repo_required",
            "Verify requires --repo for a Git-range scope.",
        )
    if kind == "explicit_patch" and not args.patch:
        raise ContractFailure(
            "patch_required",
            "Verify requires --patch for an explicit-patch scope.",
        )

    reasons = verify_bundle_integrity(bundle, manifest)
    reasons.extend(verify_manifest_input_sources(manifest))
    reasons.extend(attestation_mismatch_reasons(manifest_bytes, manifest, attestation))

    if args.contract_root:
        contract, errors = collect_preflight(
            Path(args.contract_root).resolve(),
            upstream_values=args.upstream,
            upstream_normalized_hashes=args.upstream_sha,
            upstream_exact_hashes=args.upstream_exact_sha,
            upstream_sizes=args.upstream_size,
        )
        if errors:
            return error_payload(errors), 1
        if manifest.get("contract") != contract:
            reasons.append("The routing, adapter, or upstream pins changed.")

    frozen_patch = None
    try:
        patch_relative = scope["patch"]["path"]
        frozen_patch_path = bundle.joinpath(*safe_relative_path(patch_relative).parts)
        frozen_patch = frozen_patch_path.read_bytes()
    except (ContractFailure, OSError):
        pass

    if kind == "frozen_uncommitted":
        repo = resolve_repo_root(Path(args.repo))
        if frozen_patch is not None:
            reasons.extend(
                verify_live_uncommitted(
                    repo,
                    scope,
                    frozen_patch,
                    [
                        entry["path"]
                        for entry in manifest.get("exclusions", [])
                    ],
                )
            )
    elif kind == "git_range":
        repo = resolve_repo_root(Path(args.repo))
        if frozen_patch is not None:
            reasons.extend(
                verify_live_git_range(
                    repo,
                    scope,
                    frozen_patch,
                    [
                        entry["path"]
                        for entry in manifest.get("exclusions", [])
                    ],
                )
            )
    elif kind == "explicit_patch":
        reasons.extend(
            verify_live_explicit_patch(
                args.patch,
                scope,
            )
        )

    if reasons:
        return {"status": "stale", "reasons": reasons}, 1
    return {
        "status": "current",
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "patch_sha256": scope.get("patch", {}).get("sha256"),
        "scope_sha256": scope_sha256(scope),
        "included_paths": scope.get("included_paths", []),
    }, 0


def require_mapping(payload, fields, code="envelope_invalid"):
    if not isinstance(payload, dict) or set(payload) != set(fields):
        raise ContractFailure(
            code,
            f"Expected exactly these fields: {', '.join(sorted(fields))}",
        )


def require_text(value, field, code="envelope_invalid"):
    if not isinstance(value, str) or not value.strip():
        raise ContractFailure(code, f"{field} must be a non-empty string.")
    return value


def validate_citation(citation):
    require_mapping(citation, {"path", "line", "quote"})
    require_text(citation["path"], "citation.path")
    require_text(citation["quote"], "citation.quote")
    line = citation["line"]
    if isinstance(line, bool) or not isinstance(line, int) or line < 1:
        raise ContractFailure("envelope_invalid", "citation.line must be a positive integer.")


def validate_finding(finding):
    if not isinstance(finding, dict):
        raise ContractFailure("envelope_invalid", "Each finding must be an object.")
    allowed = FINDING_COMMON_FIELDS | FINDING_NATIVE_FIELDS
    unknown = set(finding) - allowed
    if unknown:
        raise ContractFailure(
            "envelope_unknown_field",
            f"Unknown finding fields: {', '.join(sorted(unknown))}",
        )
    missing = FINDING_COMMON_FIELDS - set(finding)
    if missing:
        raise ContractFailure(
            "envelope_invalid",
            f"Finding is missing fields: {', '.join(sorted(missing))}",
        )
    if not isinstance(finding["severity"], str) or finding["severity"] not in SEVERITIES:
        raise ContractFailure("envelope_invalid", "Finding severity must be P0, P1, or P2.")
    for field in (
        "severity_rationale",
        "title",
        "what_this_is",
        "problem",
        "fix",
        "if_we_skip_it",
    ):
        require_text(finding[field], field)
    require_mapping(finding["location"], {"path", "line"})
    require_text(finding["location"]["path"], "location.path")
    line = finding["location"]["line"]
    if isinstance(line, bool) or not isinstance(line, int) or line < 1:
        raise ContractFailure("envelope_invalid", "location.line must be a positive integer.")
    citations = finding["citations"]
    if not isinstance(citations, list) or not citations:
        raise ContractFailure("envelope_invalid", "Every finding needs at least one citation.")
    for citation in citations:
        validate_citation(citation)
    for field in FINDING_NATIVE_FIELDS:
        if field in finding and (
            not isinstance(finding[field], str) or not finding[field].strip()
        ):
            raise ContractFailure("envelope_invalid", f"{field} must be a non-empty string.")


def tree_source_map(manifest):
    sources = {}
    for entry in manifest.get("scope", {}).get("tree_sources", []):
        try:
            path = source_key(entry["path"])
            snapshot = safe_relative_path(entry["snapshot_path"]).as_posix()
        except (ContractFailure, KeyError):
            continue
        sources[path] = {
            "snapshot_path": snapshot,
            "sha256": entry.get("sha256"),
        }
    return sources


def source_key(value):
    return PurePosixPath(value.replace("\\", "/")).as_posix()


def validate_check_record(check, code="envelope_invalid"):
    require_mapping(check, {"name", "result", "reason"}, code)
    require_text(check["name"], "check.name", code)
    result = check["result"]
    if not isinstance(result, str) or result not in {
        "passed",
        "failed",
        "not_run",
        "not_assessed",
    }:
        raise ContractFailure(code, "Unknown check result.")
    if not isinstance(check["reason"], str):
        raise ContractFailure(code, "check.reason must be a string.")
    if result == "not_run" and not check["reason"].strip():
        raise ContractFailure(
            code,
            "check not_run requires a non-empty reason.",
        )


def validate_coverage(coverage, manifest):
    require_mapping(coverage, {"status", "checked", "unchecked", "checks"})
    status = coverage["status"]
    if not isinstance(status, str) or status not in {
        "complete",
        "partial",
        "not_assessed",
        "blocked",
    }:
        raise ContractFailure("envelope_invalid", "Unknown coverage status.")
    if not isinstance(coverage["checked"], list):
        raise ContractFailure("envelope_invalid", "coverage.checked must be a list.")
    if status == "complete" and not coverage["checked"]:
        raise ContractFailure(
            "envelope_invalid",
            "coverage.status complete requires at least one checked source.",
        )
    sources = tree_source_map(manifest)
    for checked in coverage["checked"]:
        require_mapping(checked, {"path", "sha256"})
        path = source_key(require_text(checked["path"], "coverage.checked.path"))
        digest = require_text(checked["sha256"], "coverage.checked.sha256")
        if path not in sources:
            raise ContractFailure(
                "coverage_source_missing",
                f"Checked path is not in the frozen tree: {path}",
            )
        if digest != sources[path]["sha256"]:
            raise ContractFailure(
                "coverage_hash_mismatch",
                f"Checked source hash does not match the frozen tree: {path}",
            )
    if not isinstance(coverage["unchecked"], list):
        raise ContractFailure("envelope_invalid", "coverage.unchecked must be a list.")
    for unchecked in coverage["unchecked"]:
        require_mapping(unchecked, {"path", "reason"})
        require_text(unchecked["path"], "coverage.unchecked.path")
        require_text(unchecked["reason"], "coverage.unchecked.reason")
    if not isinstance(coverage["checks"], list):
        raise ContractFailure("envelope_invalid", "coverage.checks must be a list.")
    for check in coverage["checks"]:
        validate_check_record(check)


def validate_envelope(envelope, manifest, attestation):
    if not isinstance(envelope, dict):
        raise ContractFailure("envelope_invalid", "Envelope must be a JSON object.")
    unknown = set(envelope) - ENVELOPE_FIELDS
    if unknown:
        raise ContractFailure(
            "envelope_unknown_field",
            f"Unknown envelope fields: {', '.join(sorted(unknown))}",
        )
    missing = ENVELOPE_FIELDS - set(envelope)
    if missing:
        raise ContractFailure(
            "envelope_invalid",
            f"Envelope is missing fields: {', '.join(sorted(missing))}",
        )

    version = envelope["contract_version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise ContractFailure("envelope_invalid", "contract_version must be an integer.")
    if version != CONTRACT_VERSION:
        raise ContractFailure(
            "envelope_version_mismatch",
            f"Expected contract_version {CONTRACT_VERSION}, got {version}.",
        )

    require_text(envelope["track_id"], "track_id")
    require_text(envelope["invocation_id"], "invocation_id")
    if envelope["launch_status"] != "launched":
        raise ContractFailure("envelope_invalid", "launch_status must be launched.")
    contract = manifest.get("contract")
    if not isinstance(contract, dict):
        raise ContractFailure(
            "bundle_invalid",
            "The frozen manifest does not pin routing and adapter metadata.",
        )
    routed_ids = {track["track_id"] for track in contract.get("tracks", [])}
    if envelope["track_id"] not in routed_ids:
        raise ContractFailure(
            "track_not_routed",
            f"Track is not routed: {envelope['track_id']}",
        )

    received = envelope["attestation"]
    require_mapping(
        received,
        {
            "manifest_sha256",
            "patch_sha256",
            "patch_size_bytes",
            "included_paths",
        },
    )
    expected = {
        "manifest_sha256": attestation["manifest_sha256"],
        "patch_sha256": attestation["patch_sha256"],
        "patch_size_bytes": attestation["patch_size_bytes"],
        "included_paths": attestation["included_paths"],
    }
    if received != expected:
        raise ContractFailure(
            "attestation_mismatch",
            "Track attestation does not match the frozen manifest and patch.",
        )

    coverage = envelope["coverage"]
    validate_coverage(coverage, manifest)

    if not isinstance(envelope["native"], dict):
        raise ContractFailure("envelope_invalid", "native must be an object.")
    findings = envelope["findings"]
    if not isinstance(findings, list):
        raise ContractFailure("envelope_invalid", "findings must be a list.")
    for finding in findings:
        validate_finding(finding)


def frozen_source_paths(bundle, manifest):
    sources = {}
    for entry in manifest["scope"].get("tree_sources", []):
        snapshot = bundle.joinpath(*safe_relative_path(entry["snapshot_path"]).parts)
        sources[source_key(entry["path"])] = snapshot
        sources[source_key(entry["snapshot_path"])] = snapshot
    for entry in manifest.get("inputs", []):
        snapshot = bundle.joinpath(*safe_relative_path(entry["snapshot_path"]).parts)
        sources[source_key(entry["path"])] = snapshot
        sources[source_key(entry["snapshot_path"])] = snapshot
        sources[Path(entry["path"]).name] = snapshot
    return sources


def validate_frozen_locations(envelope, bundle, manifest):
    tree_sources = tree_source_map(manifest)
    sources = frozen_source_paths(bundle, manifest)
    for finding in envelope["findings"]:
        location = finding["location"]
        location_path = source_key(location["path"])
        tree_entry = tree_sources.get(location_path)
        if tree_entry is None:
            raise ContractFailure(
                "location_source_missing",
                f"Finding location is not in the frozen tree: {location['path']}",
            )
        snapshot = bundle.joinpath(
            *safe_relative_path(tree_entry["snapshot_path"]).parts
        )
        try:
            lines = snapshot.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            raise ContractFailure(
                "location_source_missing",
                f"Cannot read frozen source: {location['path']}",
            ) from exc
        if location["line"] < 1 or location["line"] > len(lines):
            raise ContractFailure(
                "location_mismatch",
                f"Finding location is outside the frozen source: {location['path']}:{location['line']}",
            )

    for finding in envelope["findings"]:
        for citation in finding["citations"]:
            citation_path = source_key(citation["path"])
            snapshot = sources.get(citation_path)
            if snapshot is None:
                raise ContractFailure(
                    "citation_source_missing",
                    f"Citation source is not in the frozen bundle: {citation['path']}",
                )
            try:
                lines = snapshot.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError) as exc:
                raise ContractFailure(
                    "citation_source_missing",
                    f"Cannot read citation source: {citation['path']}",
                ) from exc
            index = citation["line"] - 1
            if index >= len(lines):
                raise ContractFailure(
                    "citation_mismatch",
                    f"Citation line is outside the frozen source: {citation['path']}:{citation['line']}",
                )
            if lines[index] != citation["quote"]:
                raise ContractFailure(
                    "citation_mismatch",
                    f"Citation quote does not match the frozen source: {citation['path']}:{citation['line']}",
                )


def track_request_sha256(manifest, attestation, track_id):
    return sha256_bytes(
        canonical_json_bytes(
            {
                "track_id": track_id,
                "manifest": manifest,
                "attestation": attestation,
            }
        )
    )


def validate_run_failure(failure):
    require_mapping(failure, {"class", "evidence"}, "run_invalid")
    failure_class = require_text(failure["class"], "failure.class", "run_invalid")
    if failure_class not in RUN_FAILURE_CLASSES:
        raise ContractFailure(
            "run_invalid",
            f"Unknown failure class: {failure_class}",
        )
    evidence = failure["evidence"]
    if failure_class in TRANSIENT_FAILURE_CLASSES:
        require_mapping(evidence, TRANSIENT_EVIDENCE_FIELDS, "recovery_invalid")
        if evidence["source"] != "host":
            raise ContractFailure(
                "recovery_invalid",
                "Transient failure evidence must identify the host as its source.",
            )
        expected_phase = failure_class.split("_", 1)[1]
        if evidence["phase"] != expected_phase:
            raise ContractFailure(
                "recovery_invalid",
                f"{failure_class} requires phase {expected_phase}.",
            )
        require_text(
            evidence["detail"],
            "failure.evidence.detail",
            "recovery_invalid",
        )
    else:
        require_text(evidence, "failure.evidence", "run_invalid")


def validate_run_attempt(attempt, expected_request_sha):
    if not isinstance(attempt, dict):
        raise ContractFailure("run_invalid", "Each track attempt must be an object.")
    status = attempt.get("status")
    if not isinstance(status, str) or status not in {"completed", "failed"}:
        raise ContractFailure(
            "run_invalid",
            "Track attempt status must be completed or failed.",
        )
    fields = set(RUN_ATTEMPT_FIELDS)
    fields.add("envelope" if status == "completed" else "failure")
    if "recovery" in attempt:
        fields.add("recovery")
    require_mapping(attempt, fields, "run_invalid")
    require_text(attempt["invocation_id"], "attempt.invocation_id", "run_invalid")
    request_sha = require_text(
        attempt["request_sha256"],
        "attempt.request_sha256",
        "run_invalid",
    )
    if not re.fullmatch(r"[0-9a-f]{64}", request_sha):
        raise ContractFailure(
            "run_invalid",
            "attempt.request_sha256 must be a lowercase SHA-256.",
        )
    if request_sha != expected_request_sha:
        raise ContractFailure(
            "request_digest_mismatch",
            "attempt.request_sha256 does not match the frozen track request digest.",
        )
    launch_status = attempt["launch_status"]
    if (
        not isinstance(launch_status, str)
        or launch_status not in {"launched", "not_launched"}
    ):
        raise ContractFailure(
            "run_invalid",
            "attempt.launch_status must be launched or not_launched.",
        )
    if status == "completed":
        if launch_status != "launched":
            raise ContractFailure(
                "run_invalid",
                "A completed track attempt must record launch_status launched.",
            )
        require_text(attempt["envelope"], "attempt.envelope", "run_invalid")
    else:
        validate_run_failure(attempt["failure"])
        failure_class = attempt["failure"]["class"]
        if failure_class == "launch_failure" and launch_status != "not_launched":
            raise ContractFailure(
                "run_invalid",
                "launch_failure requires launch_status not_launched.",
            )
        if failure_class != "launch_failure" and launch_status != "launched":
            raise ContractFailure(
                "run_invalid",
                f"{failure_class} requires launch_status launched.",
            )
    if "recovery" in attempt:
        recovery = attempt["recovery"]
        require_mapping(recovery, RUN_RECOVERY_FIELDS, "recovery_invalid")
        require_text(
            recovery["of_invocation_id"],
            "recovery.of_invocation_id",
            "recovery_invalid",
        )
        if recovery["analysis_reused"] is not False:
            raise ContractFailure(
                "recovery_invalid",
                "A recovery attempt must not reuse failed-attempt analysis.",
            )


def validate_run_track(track):
    require_mapping(track, RUN_TRACK_FIELDS, "run_invalid")
    track_id = require_text(track["track_id"], "track.track_id", "run_invalid")
    attempts = track["attempts"]
    if not isinstance(attempts, list):
        raise ContractFailure("run_invalid", "track.attempts must be a list.")
    return track_id


def load_run_envelope(bundle, manifest, attestation, run_dir, attempt, track_id):
    path = resolve_relative_under(
        run_dir,
        attempt["envelope"],
        "invalid_result",
        "Track report",
    )
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ContractFailure(
            "invalid_result",
            f"Cannot read track report {attempt['envelope']}: {exc}",
        ) from exc
    if not data.strip():
        raise ContractFailure(
            "invalid_result",
            f"Track report is blank: {attempt['envelope']}",
        )
    try:
        envelope = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractFailure(
            "invalid_result",
            f"Track report is malformed or truncated: {attempt['envelope']}",
        ) from exc
    try:
        validate_envelope(envelope, manifest, attestation)
        validate_frozen_locations(envelope, bundle, manifest)
    except ContractFailure as exc:
        if exc.code == "attestation_mismatch":
            raise ContractFailure(
                "scope_mismatch",
                f"Track report scope does not match the frozen bundle: {exc.message}",
            ) from exc
        raise ContractFailure(
            "invalid_result",
            f"Track report is unverifiable: {exc.message}",
        ) from exc
    if envelope["track_id"] != track_id:
        raise ContractFailure(
            "invalid_result",
            f"Track report {attempt['envelope']} belongs to {envelope['track_id']}, not {track_id}.",
        )
    if envelope["invocation_id"] != attempt["invocation_id"]:
        raise ContractFailure(
            "invalid_result",
            "Track report invocation_id does not match its attempt.",
        )
    return envelope


def failure_from_attempt(attempt, failure, track_id, index, preserve_metadata=False):
    launch_status = attempt.get("launch_status") if isinstance(attempt, dict) else None
    if not isinstance(launch_status, str) or launch_status not in {
        "launched",
        "not_launched",
    }:
        launch_status = "not_launched"
    result = {
        "invocation_id": f"{track_id}-invalid-{index}",
        "status": "failed",
        "launch_status": launch_status,
        "failure": failure,
    }
    if preserve_metadata and isinstance(attempt, dict):
        for field in ("invocation_id", "request_sha256", "recovery"):
            if field in attempt:
                result[field] = attempt[field]
    return result


def evaluate_run_track(track, bundle, manifest, attestation, run_dir):
    if len(track["attempts"]) > 2:
        return failed_track_result(
            track,
            f"Track {track['track_id']} has more than one recovery attempt.",
        ), None
    effective = []
    envelope = None
    expected_request_sha = track_request_sha256(
        manifest,
        attestation,
        track["track_id"],
    )
    for index, attempt in enumerate(track["attempts"], start=1):
        try:
            validate_run_attempt(attempt, expected_request_sha)
        except ContractFailure as exc:
            effective.append(
                failure_from_attempt(
                    attempt,
                    {"class": "invalid_result", "evidence": exc.message},
                    track["track_id"],
                    index,
                )
            )
            envelope = None
            continue
        if attempt["status"] == "failed":
            effective.append(dict(attempt))
            continue
        try:
            envelope = load_run_envelope(
                bundle,
                manifest,
                attestation,
                run_dir,
                attempt,
                track["track_id"],
            )
            effective.append(dict(attempt))
        except ContractFailure as exc:
            failure_class = (
                "scope_mismatch" if exc.code == "scope_mismatch" else "invalid_result"
            )
            effective.append(
                failure_from_attempt(
                    attempt,
                    {"class": failure_class, "evidence": exc.message},
                    track["track_id"],
                    index,
                    preserve_metadata=True,
                )
            )
            envelope = None

    recovery_error = None
    if len(effective) == 2:
        first, second = effective
        if "recovery" not in second:
            recovery_error = (
                f"Track {track['track_id']} has an implicit retry "
                "without a recovery record."
            )
        elif first["status"] != "failed" or (
            failure := first.get("failure")
        ) is None or failure["class"] not in TRANSIENT_FAILURE_CLASSES:
            recovery_error = (
                "Recovery is allowed only after an evidenced transient runtime "
                "or transport failure."
            )
        else:
            recovery = second["recovery"]
            if recovery["of_invocation_id"] != first["invocation_id"]:
                recovery_error = "Recovery does not reference the failed invocation."
            elif second["request_sha256"] != first["request_sha256"]:
                recovery_error = "Recovery did not use the same frozen request."
            elif second["invocation_id"] == first["invocation_id"]:
                recovery_error = "Recovery must use a new invocation ID."
    elif len(effective) == 1 and "recovery" in effective[0]:
        recovery_error = "The first track attempt cannot be a recovery."

    if recovery_error is not None:
        effective[-1] = failure_from_attempt(
            effective[-1],
            {"class": "invalid_result", "evidence": recovery_error},
            track["track_id"],
            len(effective),
            preserve_metadata=True,
        )
        envelope = None

    if not effective:
        return {
            "track_id": track["track_id"],
            "status": "missing",
            "launch_status": "not_launched",
            "coverage_status": "not_assessed",
            "finding_count": 0,
            "attempts": [],
        }, None

    final = effective[-1]
    if final["status"] == "completed" and envelope is None:
        return {
            "track_id": track["track_id"],
            "status": "failed",
            "launch_status": final["launch_status"],
            "coverage_status": "not_assessed",
            "finding_count": 0,
            "attempts": effective,
        }, None
    return {
        "track_id": track["track_id"],
        "status": final["status"],
        "launch_status": final["launch_status"],
        "coverage_status": (
            envelope["coverage"]["status"] if envelope is not None else "not_assessed"
        ),
        "finding_count": len(envelope["findings"]) if envelope is not None else 0,
        "attempts": effective,
    }, envelope


def failed_track_result(track, message):
    return {
        "track_id": track["track_id"],
        "status": "failed",
        "launch_status": "not_launched",
        "coverage_status": "not_assessed",
        "finding_count": 0,
        "attempts": [
            {
                "invocation_id": f"{track['track_id']}-invalid",
                "status": "failed",
                "launch_status": "not_launched",
                "failure": {"class": "invalid_result", "evidence": message},
            }
        ],
    }


def validate_run_partial(
    partial,
    completed_ids,
    expected_blocked,
    run_path,
):
    require_mapping(partial, RUN_PARTIAL_FIELDS, "partial_approval_invalid")
    approval = partial["approval"]
    require_mapping(approval, RUN_APPROVAL_FIELDS, "partial_approval_invalid")
    if approval["source"] != "user":
        raise ContractFailure(
            "partial_approval_invalid",
            "Partial mode requires an explicit post-block user approval source.",
        )
    require_text(
        approval["evidence"],
        "partial.approval.evidence",
        "partial_approval_invalid",
    )
    blocked_result = partial["blocked_result"]
    require_mapping(
        blocked_result,
        RUN_BLOCKED_RESULT_FIELDS,
        "partial_blocked_result_invalid",
    )
    blocked_relative = require_text(
        blocked_result["path"],
        "partial.blocked_result.path",
        "partial_blocked_result_invalid",
    )
    run_dir = run_path.parent.resolve()
    blocked_path = resolve_relative_under(
        run_dir,
        blocked_relative,
        "partial_blocked_result_invalid",
        "The blocked result artifact",
    )
    try:
        same_file = os.path.samefile(blocked_path, run_path)
    except OSError:
        same_file = False
    if same_file:
        raise ContractFailure(
            "partial_blocked_result_invalid",
            "Partial approval cannot reference the current run or a hard link to it.",
        )
    digest = require_text(
        blocked_result["sha256"],
        "partial.blocked_result.sha256",
        "partial_blocked_result_invalid",
    )
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ContractFailure(
            "partial_blocked_result_invalid",
            "partial.blocked_result.sha256 must be a lowercase SHA-256.",
        )
    try:
        blocked_bytes = blocked_path.read_bytes()
    except OSError as exc:
        raise ContractFailure(
            "partial_blocked_result_invalid",
            f"Cannot read the blocked result artifact: {exc}",
        ) from exc
    if sha256_bytes(blocked_bytes) != digest:
        raise ContractFailure(
            "partial_blocked_result_invalid",
            "The blocked result artifact digest does not match.",
        )
    try:
        blocked = json.loads(blocked_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractFailure(
            "partial_blocked_result_invalid",
            "The blocked result artifact is not valid JSON.",
        ) from exc
    required_fields = RUN_RESULT_FIELDS | {"rendered"}
    allowed_fields = required_fields | {"errors"}
    if (
        not isinstance(blocked, dict)
        or not required_fields <= set(blocked)
        or set(blocked) - allowed_fields
    ):
        raise ContractFailure(
            "partial_blocked_result_invalid",
            "The blocked result artifact does not have the complete validate-run result schema.",
        )
    require_text(
        blocked["rendered"],
        "partial.blocked_result.rendered",
        "partial_blocked_result_invalid",
    )
    if "errors" in blocked:
        errors = blocked["errors"]
        if (
            not isinstance(errors, list)
            or any(
                not isinstance(error, dict)
                or set(error) != {"code", "message"}
                or not isinstance(error["code"], str)
                or not error["code"].strip()
                or not isinstance(error["message"], str)
                or not error["message"].strip()
                for error in errors
            )
        ):
            raise ContractFailure(
                "partial_blocked_result_invalid",
                "The blocked result errors are malformed.",
            )
    for field in RUN_RESULT_FIELDS:
        if canonical_json_bytes(blocked[field]) != canonical_json_bytes(
            expected_blocked[field]
        ):
            raise ContractFailure(
                (
                    "partial_gap_mismatch"
                    if field == "missing_tracks"
                    else "partial_blocked_result_invalid"
                ),
                f"The blocked result {field} does not match this run.",
            )
    expected_errors = expected_blocked.get("errors", [])
    if canonical_json_bytes(blocked.get("errors", [])) != canonical_json_bytes(
        expected_errors
    ):
        raise ContractFailure(
            "partial_blocked_result_invalid",
            "The blocked result errors do not match this run.",
        )
    canonical_blocked = {
        field: value for field, value in blocked.items() if field != "rendered"
    }
    if blocked["rendered"] != render_run(canonical_blocked):
        raise ContractFailure(
            "partial_blocked_result_invalid",
            "The blocked result rendered output is not the canonical render of this run.",
        )
    missing_track_ids = partial["missing_track_ids"]
    if (
        not isinstance(missing_track_ids, list)
        or not missing_track_ids
        or any(not isinstance(item, str) or not item.strip() for item in missing_track_ids)
        or len(missing_track_ids) != len(set(missing_track_ids))
    ):
        raise ContractFailure(
            "partial_approval_invalid",
            "partial.missing_track_ids must be a non-empty list of unique track IDs.",
        )
    missing_ids = expected_blocked["missing_tracks"]
    if set(missing_track_ids) != set(missing_ids):
        raise ContractFailure(
            "partial_gap_mismatch",
            "Partial mode does not match the actual missing tracks.",
        )
    require_text(
        partial["reduced_independence"],
        "partial.reduced_independence",
        "partial_approval_invalid",
    )
    if len(completed_ids) != 1:
        raise ContractFailure(
            "partial_requires_one_completed_track",
            "One-track partial mode requires exactly one completed track.",
        )
    return digest


def validate_run_record(run, bundle, manifest, attestation, run_path):
    if not isinstance(run, dict):
        raise ContractFailure("run_invalid", "Review run must be a JSON object.")
    unknown = set(run) - RUN_FIELDS
    if unknown:
        raise ContractFailure(
            "run_unknown_field",
            f"Unknown review run fields: {', '.join(sorted(unknown))}",
        )
    missing = RUN_FIELDS - set(run)
    if missing:
        raise ContractFailure(
            "run_invalid",
            f"Review run is missing fields: {', '.join(sorted(missing))}",
        )
    version = run["contract_version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise ContractFailure("run_invalid", "contract_version must be an integer.")
    if version != CONTRACT_VERSION:
        raise ContractFailure(
            "run_version_mismatch",
            f"Expected contract_version {CONTRACT_VERSION}, got {version}.",
        )
    if not isinstance(run["tracks"], list):
        raise ContractFailure("run_invalid", "tracks must be a list.")
    run_errors = []
    valid_checks = []
    checks = run["checks"]
    if not isinstance(checks, list):
        run_errors.append(
            {
                "code": "run_invalid",
                "message": "checks must be a list.",
            }
        )
    else:
        for check in checks:
            try:
                validate_check_record(check, "run_invalid")
            except ContractFailure as exc:
                run_errors.append({"code": exc.code, "message": exc.message})
                continue
            valid_checks.append(check)
    check_names = {check["name"] for check in valid_checks}
    if not check_names & CAPABILITY_CHECKS:
        run_errors.append(
            {
                "code": "capability_check_missing",
                "message": "Run checks must record at least one host capability check.",
            }
        )

    contract = manifest.get("contract")
    if not isinstance(contract, dict):
        raise ContractFailure(
            "bundle_invalid",
            "The frozen manifest does not pin routing and adapter metadata.",
        )
    routed_ids = [track["track_id"] for track in contract.get("tracks", [])]
    track_candidates = {track_id: [] for track_id in routed_ids}
    for index, track in enumerate(run["tracks"], start=1):
        if not isinstance(track, dict):
            run_errors.append(
                {
                    "code": "run_invalid",
                    "message": f"Track result {index} must be an object.",
                }
            )
            continue
        track_id = track.get("track_id")
        if not isinstance(track_id, str) or not track_id.strip():
            run_errors.append(
                {
                    "code": "run_invalid",
                    "message": f"Track result {index} must identify its routed track.",
                }
            )
            continue
        if track_id not in track_candidates:
            run_errors.append(
                {
                    "code": "track_not_routed",
                    "message": f"Track is not routed: {track_id}",
                }
            )
            continue
        if track_candidates[track_id]:
            run_errors.append(
                {
                    "code": "run_invalid",
                    "message": f"Duplicate track result: {track_id}",
                }
            )
        track_candidates[track_id].append(track)

    track_results = []
    completed_reports = []
    run_dir = run_path.parent
    for track_id in routed_ids:
        candidates = track_candidates[track_id] or [
            {"track_id": track_id, "attempts": []}
        ]
        selected = None
        for track in candidates:
            try:
                validate_run_track(track)
            except ContractFailure as exc:
                run_errors.append({"code": exc.code, "message": exc.message})
                if selected is None:
                    selected = (
                        failed_track_result({"track_id": track_id}, exc.message),
                        None,
                    )
                continue
            try:
                result, envelope = evaluate_run_track(
                    track, bundle, manifest, attestation, run_dir
                )
            except ContractFailure as exc:
                result, envelope = failed_track_result(track, exc.message), None
            if selected is None or envelope is not None:
                selected = (result, envelope)
                if envelope is not None:
                    break
        result, envelope = selected
        track_results.append(result)
        if envelope is not None:
            completed_reports.append(envelope)

    invocation_ids = []
    recovery_count = 0
    for result in track_results:
        for attempt in result["attempts"]:
            invocation_ids.append(attempt["invocation_id"])
            if "recovery" in attempt:
                recovery_count += 1
    if len(invocation_ids) != len(set(invocation_ids)):
        run_errors.append(
            {
                "code": "run_invalid",
                "message": "Invocation IDs must be unique across the review run.",
            }
        )
    if recovery_count > 1:
        run_errors.append(
            {
                "code": "recovery_limit",
                "message": "One review run may perform at most one recovery invocation.",
            }
        )
    if recovery_count and "recovery_capability" not in check_names:
        run_errors.append(
            {
                "code": "recovery_capability_check_missing",
                "message": "Recovery requires a recorded recovery_capability check.",
            }
        )

    completed_ids = [
        result["track_id"]
        for result in track_results
        if result["status"] == "completed"
    ]
    missing_ids = [
        result["track_id"]
        for result in track_results
        if result["status"] != "completed"
    ]
    if not missing_ids and "independence_capability" not in check_names:
        run_errors.append(
            {
                "code": "independence_capability_check_missing",
                "message": "A complete run requires a recorded independence_capability check.",
            }
        )
    capability_blocked = any(
        check["name"] in CAPABILITY_CHECKS
        and check["result"] not in {"passed", "not_run"}
        for check in valid_checks
    )
    coverage = []
    for result in track_results:
        entry = {
            "track_id": result["track_id"],
            "status": result["coverage_status"],
        }
        if result["status"] != "completed":
            entry["reason"] = "Required review track did not complete."
        elif result["coverage_status"] == "blocked":
            entry["reason"] = "Completed track did not verify the frozen requirements."
        coverage.append(entry)
    coverage_blocked = any(
        result["status"] == "completed"
        and result["coverage_status"] == "blocked"
        for result in track_results
    )
    if coverage_blocked:
        run_errors.append(
            {
                "code": "coverage_blocked",
                "message": (
                    "A completed review track reported blocked frozen-requirement "
                    "coverage."
                ),
            }
        )
    partial = run["partial"]
    partial_result = None
    if partial is not None:
        expected_blocked = {
            "status": "blocked",
            "tracks": track_results,
            "completed_reports": completed_reports,
            "missing_tracks": missing_ids,
            "coverage": coverage,
            "checks": valid_checks,
            "partial": None,
        }
        if run_errors:
            expected_blocked["errors"] = [dict(error) for error in run_errors]
        try:
            blocked_result_sha256 = validate_run_partial(
                partial,
                completed_ids,
                expected_blocked,
                run_path,
            )
        except ContractFailure as exc:
            run_errors.append({"code": exc.code, "message": exc.message})
        else:
            partial_result = {
                "approved": True,
                "approved_after_block": True,
                "approval_source": partial["approval"]["source"],
                "approval_evidence": partial["approval"]["evidence"],
                "blocked_result_sha256": blocked_result_sha256,
                "missing_tracks": missing_ids,
                "reduced_independence": partial["reduced_independence"],
                "coverage": coverage,
                "completed_reports": [
                    {
                        "track_id": envelope["track_id"],
                        "invocation_id": envelope["invocation_id"],
                    }
                    for envelope in completed_reports
                ],
            }
    if run_errors or coverage_blocked:
        status = "blocked"
    elif partial_result is not None:
        status = "blocked" if capability_blocked else "partial"
    elif not missing_ids and not capability_blocked:
        status = "complete"
    else:
        status = "blocked"
    result = {
        "status": status,
        "tracks": track_results,
        "completed_reports": completed_reports,
        "missing_tracks": missing_ids,
        "coverage": coverage,
        "checks": valid_checks,
        "partial": partial_result,
    }
    if run_errors:
        result["errors"] = run_errors
    return result


def render_envelope(envelope, heading="# Parallel Code Review"):
    lines = [
        heading,
        "",
        f"Track: `{envelope['track_id']}`",
        f"Invocation: `{envelope['invocation_id']}`",
        f"Launch status: `{envelope['launch_status']}`",
        f"Manifest: `{envelope['attestation']['manifest_sha256']}`",
        f"Patch: `{envelope['attestation']['patch_sha256']}`",
        f"Coverage: `{envelope['coverage']['status']}`",
        "",
        "## Unchecked",
        "",
    ]
    if envelope["coverage"]["unchecked"]:
        lines.extend(
            f"- `{entry['path']}` — {entry['reason']}"
            for entry in envelope["coverage"]["unchecked"]
        )
    else:
        lines.append("None.")
    lines.extend(["", "## Checks", ""])
    if envelope["coverage"]["checks"]:
        for check in envelope["coverage"]["checks"]:
            reason = f" — {check['reason']}" if check["reason"] else ""
            lines.append(f"- `{check['name']}`: `{check['result']}`{reason}")
    else:
        lines.append("None.")
    lines.extend(
        [
        "",
        "## Native report",
        "",
        "```json",
        json.dumps(envelope["native"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Findings",
        ]
    )
    if not envelope["findings"]:
        lines.append("")
        lines.append("No findings.")
    for index, finding in enumerate(envelope["findings"], start=1):
        location = finding["location"]
        lines.extend(
            [
                "",
                f"### {index}. {finding['title']}",
                f"`{location['path']}:{location['line']}`",
                f"Severity: {finding['severity']} — {finding['severity_rationale']}",
                f"What this is: {finding['what_this_is']}",
                f"Problem: {finding['problem']}",
                f"Fix: {finding['fix']}",
                f"If we skip it: {finding['if_we_skip_it']}",
            ]
        )
        if "native_axis" in finding:
            lines.append(f"Native axis: {finding['native_axis']}")
        if "native_id" in finding:
            lines.append(f"Native ID: {finding['native_id']}")
        if "native_severity" in finding:
            lines.append(f"Native severity: {finding['native_severity']}")
        if "native_group" in finding:
            lines.append(f"Native group: {finding['native_group']}")
        lines.append("Citations:")
        for citation in finding["citations"]:
            lines.append(
                f"- `{citation['path']}:{citation['line']}` — {citation['quote']}"
            )
    return "\n".join(lines) + "\n"


def render_run(result):
    lines = ["# Parallel Code Review", "", f"Overall status: `{result['status']}`"]
    if result["status"] == "complete":
        lines.append("All required review tracks returned a current valid report.")
    elif result["status"] == "partial":
        lines.extend(
            [
                "This is a blocked one-track partial review, not a complete parallel review.",
                f"Missing tracks: {', '.join(f'`{track}`' for track in result['missing_tracks'])}",
            ]
        )
    else:
        lines.append("This is not a passing review.")
        if result["missing_tracks"]:
            lines.append(
                f"Missing tracks: {', '.join(f'`{track}`' for track in result['missing_tracks'])}"
            )

    lines.extend(["", "## Track results", ""])
    for track in result["tracks"]:
        lines.append(
            f"- `{track['track_id']}`: `{track['status']}`; "
            f"launch `{track['launch_status']}`; "
            f"coverage `{track['coverage_status']}`; "
            f"findings {track['finding_count']}"
        )
        for attempt in track["attempts"]:
            if attempt["status"] == "failed":
                failure = attempt["failure"]
                lines.append(
                    f"  - `{attempt['invocation_id']}` failed as "
                    f"`{failure['class']}`: {failure['evidence']}"
                )
            if "recovery" in attempt:
                lines.append(
                    f"  - `{attempt['invocation_id']}` is one bounded recovery "
                    f"of `{attempt['recovery']['of_invocation_id']}` with recorded "
                    "`analysis_reused: false` (not independently verified)."
                )

    if result.get("errors"):
        lines.extend(["", "## Run errors", ""])
        for error in result["errors"]:
            lines.append(f"- `{error['code']}`: {error['message']}")

    lines.extend(["", "## Coverage", ""])
    for coverage in result["coverage"]:
        reason = f" — {coverage['reason']}" if "reason" in coverage else ""
        lines.append(f"- `{coverage['track_id']}`: `{coverage['status']}`{reason}")

    lines.extend(["", "## Host checks", ""])
    if result["checks"]:
        for check in result["checks"]:
            reason = f" — {check['reason']}" if check["reason"] else ""
            lines.append(f"- `{check['name']}`: `{check['result']}`{reason}")
    else:
        lines.append("None recorded.")

    if result["partial"] is not None:
        partial = result["partial"]
        lines.extend(
            [
                "",
                "## Partial mode",
                "",
                "Explicit approval: `approved after blocked result`",
                f"Approval source: {partial['approval_source']}",
                f"Approval evidence: {partial['approval_evidence']}",
                f"Blocked result SHA-256: `{partial['blocked_result_sha256']}`",
                f"Reduced independence: {partial['reduced_independence']}",
                "Coverage:",
            ]
        )
        for coverage in partial["coverage"]:
            reason = f" — {coverage['reason']}" if "reason" in coverage else ""
            lines.append(f"- `{coverage['track_id']}`: `{coverage['status']}`{reason}")
        lines.append("The original completed reports follow without truncation.")

    if result["completed_reports"]:
        lines.extend(["", "## Completed track reports"])
        for envelope in result["completed_reports"]:
            lines.extend(
                [
                    "",
                    render_envelope(
                        envelope,
                        heading=f"## Track report: `{envelope['track_id']}`",
                    ).rstrip(),
                ]
            )
    return "\n".join(lines) + "\n"


def load_current_review_bundle(args):
    if not args.contract_root:
        raise ContractFailure(
            "contract_root_required",
            "Review validation requires --contract-root with an explicit --upstream resolution.",
        )
    if not args.upstream:
        raise ContractFailure(
            "upstream_unresolved",
            "Review validation requires the frozen upstream resolution explicitly.",
        )
    bundle = Path(args.bundle).resolve()
    manifest, manifest_bytes, attestation = load_bundle(bundle)
    reasons = verify_bundle_integrity(bundle, manifest)
    reasons.extend(attestation_mismatch_reasons(manifest_bytes, manifest, attestation))
    if reasons:
        return None, {"status": "blocked", "reasons": reasons}, 1

    contract, errors = collect_preflight(
        Path(args.contract_root).resolve(),
        upstream_values=args.upstream,
        upstream_normalized_hashes=args.upstream_sha,
        upstream_exact_hashes=args.upstream_exact_sha,
        upstream_sizes=args.upstream_size,
    )
    if errors:
        return None, error_payload(errors), 1
    if manifest.get("contract") != contract:
        raise ContractFailure(
            "bundle_stale",
            "The routing table, adapter, or upstream resolution changed after the freeze.",
        )
    return (bundle, manifest, attestation), None, 0


def command_validate_envelope(args):
    loaded, blocked, exit_code = load_current_review_bundle(args)
    if blocked is not None:
        return blocked, exit_code
    bundle, manifest, attestation = loaded

    envelope_path = Path(args.envelope).resolve()
    if not envelope_path.is_file():
        raise ContractFailure("envelope_missing", f"Envelope is missing: {envelope_path}")
    try:
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractFailure("envelope_invalid", f"Cannot read envelope: {exc}") from exc
    validate_envelope(envelope, manifest, attestation)
    validate_frozen_locations(envelope, bundle, manifest)
    return {
        "status": "valid",
        "track_id": envelope["track_id"],
        "findings": envelope["findings"],
        "rendered": render_envelope(envelope),
    }, 0


def command_validate_run(args):
    loaded, blocked, exit_code = load_current_review_bundle(args)
    if blocked is not None:
        return blocked, exit_code
    bundle, manifest, attestation = loaded

    run_path = Path(args.run).resolve()
    if not run_path.is_file():
        raise ContractFailure("run_missing", f"Review run is missing: {run_path}")
    try:
        run = json.loads(run_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractFailure("run_invalid", f"Cannot read review run: {exc}") from exc
    result = validate_run_record(
        run,
        bundle,
        manifest,
        attestation,
        run_path,
    )
    result["rendered"] = render_run(result)
    return result, 0 if result["status"] == "complete" else 1


def command_preflight(args):
    skill_root = Path(args.skill_root).resolve()
    result, errors = collect_preflight(
        skill_root,
        upstream_values=args.upstream,
        upstream_normalized_hashes=args.upstream_sha,
        upstream_exact_hashes=args.upstream_exact_sha,
        upstream_sizes=args.upstream_size,
    )
    if errors:
        return error_payload(errors), 1
    return result, 0


def add_upstream_arguments(parser):
    parser.add_argument(
        "--upstream",
        "--upstream-uri",
        "--upstream-pin",
        dest="upstream",
        action="append",
        default=[],
        metavar="NAME=PATH_OR_URI",
        help="Coordinator-resolved upstream skill source.",
    )
    parser.add_argument(
        "--upstream-sha",
        "--upstream-hash",
        dest="upstream_sha",
        action="append",
        default=[],
        metavar="NAME=SHA256",
        help="Normalized text SHA-256 for a coordinator-resolved upstream.",
    )
    parser.add_argument(
        "--upstream-exact-sha",
        dest="upstream_exact_sha",
        action="append",
        default=[],
        metavar="NAME=SHA256",
        help="Exact-byte SHA-256 for a coordinator-resolved upstream URI.",
    )
    parser.add_argument(
        "--upstream-size",
        dest="upstream_size",
        action="append",
        default=[],
        metavar="NAME=BYTES",
        help="Exact-byte size for a coordinator-resolved upstream URI.",
    )


def build_parser():
    parser = argparse.ArgumentParser(description="Validate parallel review contract artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight", help="Validate routing and adapter metadata.")
    preflight.add_argument(
        "--skill-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    add_upstream_arguments(preflight)
    preflight.set_defaults(handler=command_preflight)

    freeze = subparsers.add_parser("freeze", help="Create an immutable review bundle.")
    freeze.add_argument("--repo")
    freeze.add_argument("--output", required=True)
    scope = freeze.add_mutually_exclusive_group(required=True)
    scope.add_argument("--range", dest="range_value")
    scope.add_argument("--patch")
    scope.add_argument("--uncommitted", action="store_true")
    freeze.add_argument("--tree-root")
    freeze.add_argument("--requirements", action="append", default=[])
    freeze.add_argument("--standards", action="append", default=[])
    freeze.add_argument("--check", action="append", default=[])
    freeze.add_argument("--not-run", action="append", default=[])
    freeze.add_argument("--exclude", action="append", default=[])
    freeze.add_argument("--contract-root")
    add_upstream_arguments(freeze)
    freeze.set_defaults(handler=command_freeze)

    verify = subparsers.add_parser("verify", help="Verify a frozen bundle and attestation.")
    verify.add_argument("--bundle", required=True)
    verify.add_argument("--repo")
    verify.add_argument("--patch")
    verify.add_argument("--contract-root")
    add_upstream_arguments(verify)
    verify.set_defaults(handler=command_verify)

    envelope = subparsers.add_parser(
        "validate-envelope",
        help="Validate and render one track's common report envelope.",
    )
    envelope.add_argument("--bundle", required=True)
    envelope.add_argument("--envelope", required=True)
    envelope.add_argument("--contract-root")
    add_upstream_arguments(envelope)
    envelope.set_defaults(handler=command_validate_envelope)

    run = subparsers.add_parser(
        "validate-run",
        help="Validate and render one coordinator review run.",
    )
    run.add_argument("--bundle", required=True)
    run.add_argument("--run", required=True)
    run.add_argument("--contract-root")
    add_upstream_arguments(run)
    run.set_defaults(handler=command_validate_run)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload, exit_code = args.handler(args)
    except ContractFailure as exc:
        payload, exit_code = error_payload([exc]), 1
    except (KeyError, TypeError, ValueError) as exc:
        payload, exit_code = error_payload(
            [
                ContractFailure(
                    "bundle_invalid",
                    f"Bundle data is malformed: {exc}",
                )
            ]
        ), 1
    except OSError as exc:
        payload, exit_code = error_payload(
            [ContractFailure("io_error", str(exc))]
        ), 1
    print(json.dumps(payload, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
