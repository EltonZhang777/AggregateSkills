# Agent Skills prerequisites

Install this repository with the general Agent Skills command in the [README](../README.md). This guide indexes each skill's direct requirements. Install unconditional requirements before use; apply a conditional requirement only when its `When` condition is true. Any one alternative in a `One of` entry satisfies that requirement. Versions are not pinned.

<!-- prerequisite-list:start -->
### Agent Skills

| Skill | Source | Install | When | Required by |
| --- | --- | --- | --- | --- |
| One of: `/show-me` or `/archify` | `/show-me`: Publisher source not declared; `/archify`: Publisher source not declared | `/show-me`: The local skill file is readable, but it declares no publisher or portable install source.; `/archify`: The local skill file names author tt-a1i but declares no publisher URL or portable install source. | For every commit explanation and the final summary. | `/spec-implement-loop` |
| `/code-review` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=code-review | Always | `/review-duo`, `/spec-implement-loop` |
| `/conventional-git-messages` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills) | npx skills@latest add EltonZhang777/AggregateSkills --skill=conventional-git-messages | Always | `/pr-and-merge`, `/spec-implement-loop` |
| `/domain-modeling` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=domain-modeling | Always | `/grill-duo-with-docs`, `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/grill-duo-with-docs` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=grill-duo-with-docs | Always | `/spec-implement-loop` |
| `/grill-duo` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills) | npx skills@latest add EltonZhang777/AggregateSkills --skill=grill-duo | Always | `/grill-duo-with-docs` |
| `/grill-with-docs` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=grill-with-docs | Always | `/requirements-to-spec-tickets` |
| `/grilling` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=grilling | Always | `/grill-duo`, `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/implement` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=implement | Always | `/spec-implement-loop` |
| `/ponytail-review` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | npx skills@latest add DietrichGebert/ponytail --skill=ponytail-review | Always | `/spec-implement-loop` |
| `/resolving-merge-conflicts` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=resolving-merge-conflicts | Always | `/pr-and-merge` |
| `/setup-matt-pocock-skills` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=setup-matt-pocock-skills | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/tdd` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=tdd | Always | `/spec-implement-loop` |
| `/to-spec` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=to-spec | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/to-tickets` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=to-tickets | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |

### MCPs

None currently.

### Other runtime tools

| Tool | Source | Install / setup | When | Required by |
| --- | --- | --- | --- | --- |
| GitHub CLI (gh) | [GitHub CLI (gh) project](https://cli.github.com/) | Install from https://cli.github.com/; Authenticate with `gh auth login`; for GitHub Enterprise, use `gh auth login --hostname <host>`. | Always | `/pr-and-merge` |
| GitHub CLI (gh) | [GitHub CLI (gh) project](https://cli.github.com/) | Install from https://cli.github.com/; Authenticate with `gh auth login`; for GitHub Enterprise, use `gh auth login --hostname <host>`. | When checking GitHub remotes for pull requests, protection, or default-branch state. | `/prune-worktrees-and-branches` |
| GitHub CLI (gh) | [GitHub CLI (gh) project](https://cli.github.com/) | Install from https://cli.github.com/; Authenticate with `gh auth login`; for GitHub Enterprise, use `gh auth login --hostname <host>`. | When using GitHub issue tracking. | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| SkillRoute CLI | [SkillRoute CLI project](https://github.com/erichare/skillroute) | uv tool install skillroute; Prepare a local catalog using the SkillRoute documentation | Always | `/skill-scout` |
<!-- prerequisite-list:end -->

## Declaration format

Each repository skill records its direct prerequisites as JSON in the `metadata.prerequisites` field. The object has `skills`, `mcps`, and `tools` arrays; the guide does not expand them transitively. A prerequisite is identified by its `name` and `source` pair. Published skill sources use `owner/repository` and default to `npx skills@latest add <source> --skill=<name>`; MCP and tool sources are HTTP(S) project URLs with explicit install or setup steps. Omit `when` for requirements that always apply, or set it to explain a condition. Use `one_of` with at least two same-category prerequisites when any one option is sufficient. Tool entries also include `install` and `setup` instructions. When a skill's publisher source is not declared, use a null source and state the missing install information instead of inventing it.

This guide is an installation and reference index. Each skill's own instructions must be self-contained and must not require that skill to consult this guide at runtime.

## Runtime checks

Use `/skill-scout` to check runtime prerequisites. If it reports a missing skill, tool, or local catalog, stop and follow the matching source and install instructions above. This guide does not inspect your environment, download, install, or index dependencies.

## Keep this guide current

Each repository skill declares its direct prerequisites as JSON in the metadata.prerequisites field of its SKILL.md frontmatter. Update that declaration when adding a skill or changing a dependency, source, or install instruction. Then update the checked list above and run:

    python -B tests/test_prerequisite_guide.py

The check validates every repository skill declaration, rejects invalid, conflicting, or duplicate entries, and compares the complete guide list. The README links here instead of copying the list.
