# Agent Skills prerequisites

Install this repository with the general Agent Skills command in the [README](../README.md). This guide indexes each skill's direct requirements. Install unconditional requirements before use; apply a conditional requirement only when its `When` condition is true. Any one alternative in a `One of` entry satisfies that requirement. A full commit in the source link pins the audited package snapshot, and its install command uses that same tree URL; other entries use their source's default version.

<!-- prerequisite-list:start -->
### Agent Skills

| Skill | Source | Install | When | Required by |
| --- | --- | --- | --- | --- |
| One of: `/show-me` or `/archify` | `/show-me`: [humanlayer/skills](https://github.com/humanlayer/skills/tree/ca7c8088db69e315a8b2deea43820270457f8f3c/plugins/show-me/skills/show-me); `/archify`: [tt-a1i/archify](https://github.com/tt-a1i/archify/tree/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify) | `/show-me`: npx skills@latest add https://github.com/humanlayer/skills/tree/ca7c8088db69e315a8b2deea43820270457f8f3c/plugins/show-me/skills/show-me; `/archify`: npx skills@latest add https://github.com/tt-a1i/archify/tree/73aaa0696e8f72c232ea710e6fa94fd953f3e773/archify | When either exact-source visual skill is available; if neither is available, use the concise plain-text fallback. | `/spec-implement-loop` |
| `/code-review` | [mattpocock/skills](https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/code-review) | npx skills@latest add https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/code-review | Always | `/review-duo`, `/spec-implement-loop` |
| `/codebase-design` | [mattpocock/skills](https://github.com/mattpocock/skills/tree/6fd947921b935b7e1e69293a200400f0fdd5c15f/skills/engineering/codebase-design) | npx skills@latest add https://github.com/mattpocock/skills/tree/6fd947921b935b7e1e69293a200400f0fdd5c15f/skills/engineering/codebase-design | When the shape of the test interface itself is in question; use it as vocabulary only. | `/spec-implement-loop` |
| `/conventional-git-messages` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/conventional-git-messages) | npx skills@latest add https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/conventional-git-messages | Always | `/spec-implement-loop` |
| `/conventional-git-messages` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/conventional-git-messages) | npx skills@latest add https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/conventional-git-messages | When drafting or materially updating a pull request title or body. | `/pr-and-merge` |
| `/domain-modeling` | [mattpocock/skills](https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/domain-modeling) | npx skills@latest add https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/domain-modeling | Always | `/grill-duo-with-docs` |
| `/grill-duo-with-docs` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/grill-duo-with-docs) | npx skills@latest add https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/grill-duo-with-docs | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/grill-duo` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills/tree/9fff1921337c513baefe67a938320f2a1a2b5b98/skills/grill-duo) | npx skills@latest add https://github.com/EltonZhang777/AggregateSkills/tree/9fff1921337c513baefe67a938320f2a1a2b5b98/skills/grill-duo | Always | `/grill-duo-with-docs` |
| `/grilling` | [mattpocock/skills](https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/productivity/grilling) | npx skills@latest add https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/productivity/grilling | Always | `/grill-duo` |
| `/implement` | [mattpocock/skills](https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/implement) | npx skills@latest add https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/implement | Always | `/spec-implement-loop` |
| `/ponytail-review` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail/tree/552acd5efd0aeae2583a12efe39373d2f076f25e/skills/ponytail-review) | npx skills@latest add https://github.com/DietrichGebert/ponytail/tree/552acd5efd0aeae2583a12efe39373d2f076f25e/skills/ponytail-review | Always | `/spec-implement-loop` |
| `/resolving-merge-conflicts` | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=resolving-merge-conflicts | When resolving a conflict during an approved pull request merge. | `/pr-and-merge` |
| `/setup-matt-pocock-skills` | [mattpocock/skills](https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/setup-matt-pocock-skills) | npx skills@latest add https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/setup-matt-pocock-skills | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/skill-scout` | [EltonZhang777/AggregateSkills](https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/skill-scout) | npx skills@latest add https://github.com/EltonZhang777/AggregateSkills/tree/2f1fac4afa920c71bcf15866dbb9fd8704e7371a/skills/skill-scout | When a requested diagram requires skill discovery. | `/conventional-git-messages` |
| `/tdd` | [mattpocock/skills](https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/tdd) | npx skills@latest add https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/tdd | Always | `/spec-implement-loop` |
| `/to-spec` | [mattpocock/skills](https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/to-spec) | npx skills@latest add https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/to-spec | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |
| `/to-tickets` | [mattpocock/skills](https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/to-tickets) | npx skills@latest add https://github.com/mattpocock/skills/tree/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/to-tickets | Always | `/requirements-to-spec-tickets`, `/spec-implement-loop` |

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

Each repository skill records its direct prerequisites as JSON in the `metadata.prerequisites` field. The object has `skills`, `mcps`, and `tools` arrays; the guide does not expand them transitively. A prerequisite is identified by its `name` and `source` pair. Published skill sources use `owner/repository` and default to `npx skills@latest add <source> --skill=<name>`. A skill entry may include `source_url` to link directly to an HTTPS path in the declared GitHub repository; the guide uses it instead of the repository-root link. For a pinned snapshot, use a commit-based GitHub tree URL for both `source_url` and `install`. MCP and tool sources are HTTP(S) project URLs with explicit install or setup steps. Omit `when` for requirements that always apply, or set it to explain a condition. Use `one_of` with at least two same-category prerequisites when any one option is sufficient. Tool entries also include `install` and `setup` instructions. When a skill's publisher source is not declared, use a null source and state the missing install information instead of inventing it.

This guide is an installation and reference index. Each skill's own instructions must be self-contained and must not require that skill to consult this guide at runtime.

## Runtime checks

Use `/skill-scout` to check skill prerequisites against the host inventory. Check whether command-line tools are available and authenticated using the host environment; if a required tool is unavailable, follow its install and setup instructions above. This guide does not inspect your environment, download, install, or index dependencies.

## Keep this guide current

Each repository skill declares its direct prerequisites as JSON in the metadata.prerequisites field of its SKILL.md frontmatter. Update that declaration when adding a skill or changing a dependency, source, or install instruction. Then update the checked list above and run:

    python -B tests/test_prerequisite_guide.py

The check validates every repository skill declaration, rejects invalid, conflicting, or duplicate entries, and compares the complete guide list. The README links here instead of copying the list.
