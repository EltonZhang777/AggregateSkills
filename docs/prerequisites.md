# Agent Skills prerequisites

Install this repository with the general Agent Skills command in the [README](../README.md). This guide indexes each skill's direct requirements. Install unconditional requirements before use; apply a conditional requirement only when its `When` condition is true. Any one alternative in a `One of` entry satisfies that requirement. Versions are not pinned.

<!-- prerequisite-list:start -->
### Agent Skills

| Skill | Source | Install | When | Required by |
| --- | --- | --- | --- | --- |
| One of: `/show-me` or `/archify` | `/show-me`: [humanlayer/skills](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md); `/archify`: [tt-a1i/archify](https://github.com/tt-a1i/archify/blob/main/archify/SKILL.md) | `/show-me`: npx skills@latest add https://github.com/humanlayer/skills/tree/main/plugins/show-me/skills/show-me; `/archify`: npx skills@latest add tt-a1i/archify --skill=archify | When either exact-source visual skill is available; if neither is available, use the concise plain-text fallback. | `/spec-implement-loop` |
| `/code-review` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=code-review | Always | `/review-duo`, `/spec-implement-loop` |
| `/conventional-git-messages` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills) | npx skills@latest add EltonZhang777/AggregateSkills --skill=conventional-git-messages | Always | `/spec-implement-loop` |
| `/conventional-git-messages` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills) | npx skills@latest add EltonZhang777/AggregateSkills --skill=conventional-git-messages | When drafting or materially updating a pull request title or body. | `/pr-and-merge` |
| `/domain-modeling` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=domain-modeling | Always | `/grill-duo-with-docs` |
| `/grill-duo-with-docs` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills) | npx skills@latest add EltonZhang777/AggregateSkills --skill=grill-duo-with-docs | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/grill-duo` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills) | npx skills@latest add EltonZhang777/AggregateSkills --skill=grill-duo | Always | `/grill-duo-with-docs` |
| `/grilling` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=grilling | Always | `/grill-duo` |
| `/implement` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=implement | Always | `/spec-implement-loop` |
| `/ponytail-review` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | npx skills@latest add DietrichGebert/ponytail --skill=ponytail-review | Always | `/spec-implement-loop` |
| `/resolving-merge-conflicts` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=resolving-merge-conflicts | When resolving a conflict during an approved pull request merge. | `/pr-and-merge` |
| `/setup-matt-pocock-skills` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=setup-matt-pocock-skills | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/skill-scout` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills) | npx skills@latest add EltonZhang777/AggregateSkills --skill=skill-scout | When a requested diagram requires skill discovery. | `/conventional-git-messages` |
| `/tdd` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=tdd | Always | `/spec-implement-loop` |
| `/to-spec` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=to-spec | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/to-tickets` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=to-tickets | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |

### MCPs

None currently.

### Other runtime tools

| Tool | Source | Install / setup | When | Required by |
| --- | --- | --- | --- | --- |
| Git CLI | [Git CLI project](https://git-scm.com/) | Install Git from https://git-scm.com/downloads; Make `git` available in a command shell at the intended repository. | Always | `/pr-and-merge`, `/prune-worktrees-and-branches`, `/spec-implement-loop` |
| Git CLI | [Git CLI project](https://git-scm.com/) | Install Git from https://git-scm.com/downloads; Make `git` available in a command shell at the intended repository. | When publishing a group with local repository artifacts. | `/requirements-to-spec-tickets` |
| Git CLI | [Git CLI project](https://git-scm.com/) | Install Git from https://git-scm.com/downloads; Make `git` available in a command shell at the intended repository. | When reviewing a Git range or capturing a repository worktree diff. | `/review-duo` |
| GitHub CLI (gh) | [GitHub CLI (gh) project](https://cli.github.com/) | Install from https://cli.github.com/; Authenticate with `gh auth login`; for GitHub Enterprise, use `gh auth login --hostname <host>`. | Always | `/pr-and-merge` |
| GitHub CLI (gh) | [GitHub CLI (gh) project](https://cli.github.com/) | Install from https://cli.github.com/; Authenticate with `gh auth login`; for GitHub Enterprise, use `gh auth login --hostname <host>`. | When checking GitHub remotes for pull requests, protection, or default-branch state. | `/prune-worktrees-and-branches` |
| GitHub CLI (gh) | [GitHub CLI (gh) project](https://cli.github.com/) | Install from https://cli.github.com/; Authenticate with `gh auth login`; for GitHub Enterprise, use `gh auth login --hostname <host>`. | When using GitHub issue tracking. | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| Python 3.8+ interpreter | [Python 3.8+ interpreter project](https://www.python.org/) | Install Python 3.8 or later from https://www.python.org/downloads/ or use a host-provided Python 3.8+ interpreter; Make Python 3.8 or later available to run scripts/apply_candidate.py with its standard library | When applying a validated candidate. | `/compress-docs` |
| SkillRoute CLI | [SkillRoute CLI project](https://github.com/erichare/skillroute) | uv tool install skillroute; Prepare a local catalog using the SkillRoute documentation | When a prerequisite skill is absent from the available skill list or its exact source cannot be verified. | `/conventional-git-messages`, `/grill-duo`, `/grill-duo-with-docs`, `/pr-and-merge`, `/requirements-to-spec-tickets`, `/review-duo`, `/spec-implement-loop` |
| SkillRoute CLI | [SkillRoute CLI project](https://github.com/erichare/skillroute) | uv tool install skillroute; Prepare a local catalog using the SkillRoute documentation | When the user selects SkillRoute local-catalog mode for discovery or routing. | `/skill-scout` |
<!-- prerequisite-list:end -->

## Declaration format

Each repository skill records its direct prerequisites as JSON in the `metadata.prerequisites` field. The object has `skills`, `mcps`, and `tools` arrays; the guide does not expand them transitively. A prerequisite is identified by its `name` and `source` pair. Published skill sources use `owner/repository` and default to `npx skills@latest add <source> --skill=<name>`. A skill entry may include `source_url` to link directly to an HTTPS path in the declared GitHub repository; the guide uses it instead of the repository-root link. MCP and tool sources are HTTP(S) project URLs with explicit install or setup steps. Omit `when` for requirements that always apply, or set it to explain a condition. Use `one_of` with at least two same-category prerequisites when any one option is sufficient. Tool entries also include `install` and `setup` instructions. When a skill's publisher source is not declared, use a null source and state the missing install information instead of inventing it.

This guide is an installation and reference index. Each skill's own instructions must be self-contained and must not require that skill to consult this guide at runtime.

## Runtime checks

Use `/skill-scout` to check skill prerequisites against the host inventory. Check whether command-line tools are available and authenticated using the host environment; if a required tool is unavailable, follow its install and setup instructions above. This guide does not inspect your environment, download, install, or index dependencies.

## Keep this guide current

Each repository skill declares its direct prerequisites as JSON in the metadata.prerequisites field of its SKILL.md frontmatter. Update that declaration when adding a skill or changing a dependency, source, or install instruction. Then update the checked list above and run:

    python -B tests/test_prerequisite_guide.py

The check validates every repository skill declaration, rejects invalid, conflicting, or duplicate entries, and compares the complete guide list. The README links here instead of copying the list.
