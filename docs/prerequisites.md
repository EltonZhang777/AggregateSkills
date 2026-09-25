# Agent Skills prerequisites

Install this repository with the general Agent Skills command in the [README](../README.md). Install all prerequisites below before you use the corresponding skill. Versions are not pinned.

<!-- prerequisite-list:start -->
### Agent Skills

| Skill | Source | Install | Required by |
| --- | --- | --- | --- |
| caveman-commit | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | npx skills@latest add JuliusBrussee/caveman --skill=caveman-commit | spec-implement-loop |
| code-review | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=code-review | review-duo, spec-implement-loop |
| domain-modeling | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=domain-modeling | requirements-to-spec-tickets, spec-implement-loop |
| grill-with-docs | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=grill-with-docs | requirements-to-spec-tickets, spec-implement-loop |
| grilling | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=grilling | requirements-to-spec-tickets, spec-implement-loop |
| implement | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=implement | spec-implement-loop |
| ponytail-review | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | npx skills@latest add DietrichGebert/ponytail --skill=ponytail-review | spec-implement-loop |
| setup-matt-pocock-skills | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=setup-matt-pocock-skills | requirements-to-spec-tickets, spec-implement-loop |
| tdd | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=tdd | spec-implement-loop |
| to-spec | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=to-spec | requirements-to-spec-tickets, spec-implement-loop |
| to-tickets | [mattpocock/skills](https://github.com/mattpocock/skills) | npx skills@latest add mattpocock/skills --skill=to-tickets | requirements-to-spec-tickets, spec-implement-loop |

### MCPs

None currently.

### Other runtime tools

| Tool | Source | Install | Required by |
| --- | --- | --- | --- |
| SkillRoute CLI | [SkillRoute CLI project](https://github.com/erichare/skillroute) | uv tool install skillroute; Prepare a local catalog using the SkillRoute documentation | skill-scout |
<!-- prerequisite-list:end -->

## Runtime checks

Use Skill Scout to check runtime prerequisites. If it reports a missing skill, tool, or local catalog, stop and follow the matching source and install instructions above. This guide does not inspect your environment, download, install, or index dependencies.

## Keep this guide current

Each repository skill declares its prerequisites in the prerequisites value in its SKILL.md metadata. Update that declaration when adding a skill or changing a dependency, source, or install instruction. Then update the checked list above and run:

    python -B tests/test_prerequisite_guide.py

The check reads every repository skill declaration, rejects conflicting or duplicate entries, and compares the complete guide list. The README links here instead of copying the list.
