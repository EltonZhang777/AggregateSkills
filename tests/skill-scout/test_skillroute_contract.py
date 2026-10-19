"""Exercise the skill-scout SkillRoute seam with an isolated local catalog."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


CLI = shutil.which("skillroute") or "skillroute"


def run_skillroute(
    catalog: Path,
    *args: str,
    executable: str = CLI,
    parse_json: bool = False,
    check: bool = True,
) -> object:
    result = subprocess.run(
        [executable, "--catalog", str(catalog), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check:
        assert result.returncode == 0, result.stderr or result.stdout
    if parse_json:
        return json.loads(result.stdout)
    return result


def route_json(catalog: Path, request: str) -> object:
    return run_skillroute(
        catalog,
        "route",
        "--backend",
        "local-token",
        "--json",
        request,
        parse_json=True,
    )


def write_fixture(root: Path, name: str, description: str) -> None:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
        encoding="utf-8",
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="skill-scout-") as directory:
        root = Path(directory) / "skills"
        catalog = Path(directory) / "catalog.db"
        empty_catalog = Path(directory) / "empty.db"
        ambiguous_root = Path(directory) / "ambiguous"
        ambiguous_catalog = Path(directory) / "ambiguous.db"
        exact_root = Path(directory) / "explicit-only"
        exact_catalog = Path(directory) / "explicit-only.db"
        root.mkdir()
        ambiguous_root.mkdir()
        exact_root.mkdir()

        write_fixture(exact_root, "build-api", "Build and implement a web API")
        run_skillroute(
            exact_catalog,
            "index",
            "--root",
            str(exact_root),
            "--backend",
            "local-token",
        )

        exact_status = run_skillroute(
            exact_catalog,
            "backend",
            "status",
            "--backend",
            "local-token",
            "--json",
            parse_json=True,
        )
        assert exact_status["skill_count"] == 1
        exact = run_skillroute(exact_catalog, "inspect", "--json", "build-api", parse_json=True)
        assert exact["name"] == "build-api"

        write_fixture(ambiguous_root, "api-guide-a", "Help with a web API task")
        write_fixture(ambiguous_root, "api-guide-b", "Help with a web API task")
        run_skillroute(
            ambiguous_catalog,
            "index",
            "--root",
            str(ambiguous_root),
            "--backend",
            "local-token",
        )
        conflict = route_json(ambiguous_catalog, "help with a web API task")
        assert conflict["clarification_needed"]
        assert len(conflict["candidates"]) == 2

        write_fixture(root, "build-api", "Build and implement a web API")
        write_fixture(root, "review-api", "Review a web API implementation")
        write_fixture(root, "test-api", "Write tests for a web API")

        run_skillroute(catalog, "index", "--root", str(root), "--backend", "local-token")

        status = run_skillroute(
            catalog,
            "backend",
            "status",
            "--backend",
            "local-token",
            "--json",
            parse_json=True,
        )
        assert status["status"] == "ready"
        assert status["skill_count"] == 3

        mismatch = route_json(catalog, "review a web API implementation")
        alternative = mismatch["candidates"][0].get("name") or mismatch["candidates"][0].get("skill_id")
        assert alternative == "review-api"
        assert exact["name"] != alternative

        similar = run_skillroute(
            catalog,
            "search",
            "--backend",
            "local-token",
            "--json",
            "--limit",
            "3",
            "web API implementation",
            parse_json=True,
        )
        assert {item["name"] for item in similar} >= {"build-api", "review-api"}

        steps = (
            "build a web API",
            "write tests for a web API",
            "review a web API implementation",
            "write tests for a web API",
        )
        selected = []
        for step in steps:
            routed = route_json(catalog, step)
            assert routed["candidates"]
            candidate = routed["candidates"][0]
            selected.append(candidate.get("name") or candidate.get("skill_id"))

        assert selected == ["build-api", "test-api", "review-api", "test-api"]
        assert list(dict.fromkeys(selected)) == ["build-api", "test-api", "review-api"]

        unknown = route_json(catalog, "xylophone orbital prerequisite")
        assert not unknown["candidates"]
        assert unknown["clarification_needed"]

        empty_status = run_skillroute(
            empty_catalog,
            "backend",
            "status",
            "--backend",
            "local-token",
            "--json",
            parse_json=True,
        )
        assert empty_status["skill_count"] == 0

        empty_route = route_json(empty_catalog, "find a prerequisite skill")
        assert not empty_route["candidates"]
        assert empty_route["clarification_needed"]

        unavailable_catalog = Path(directory) / "unavailable-catalog"
        unavailable_catalog.mkdir()
        unavailable = run_skillroute(
            unavailable_catalog,
            "backend",
            "status",
            "--backend",
            "local-token",
            "--json",
            check=False,
        )
        assert unavailable.returncode != 0

        missing_cli = Path(directory) / "missing-skillroute"
        try:
            run_skillroute(catalog, "--version", executable=str(missing_cli))
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("a missing SkillRoute CLI must fail before fallback")

        missing = run_skillroute(
            catalog,
            "inspect",
            "--json",
            "missing-skill",
            check=False,
        )
        assert missing.returncode != 0
        assert "not found" in (missing.stdout + missing.stderr).lower()

    print("skill-scout SkillRoute seam checks passed")


if __name__ == "__main__":
    main()
