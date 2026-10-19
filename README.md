# AggregateSkills

AggregateSkills is a collection of reusable agent skills for documentation, planning, code review, and delivery workflows. Each skill's `SKILL.md` explains when and how to use it.

## Getting the code

```sh
git clone https://github.com/EltonZhang777/AggregateSkills.git
```

## Prerequisites

The install command uses [`npx`](https://nodejs.org/), provided by npm. This repository does not pin a Node.js version. Individual skills may document additional requirements in their guides.

## Install and use

```sh
npx skills@latest add EltonZhang777/AggregateSkills
```

After installation, follow your coding agent's skill workflow to activate a skill.

## Skill catalog

- [compress-docs](skills/compress-docs/SKILL.md) compresses approved documents into candidates and applies them through version-conditional storage backends.
- [conventional-git-messages](skills/conventional-git-messages/SKILL.md) drafts concise commit, pull request, and issue text without performing Git or GitHub operations.
- [grill-duo](skills/grill-duo/SKILL.md) coordinates an independent reviewer during a multi-round grilling session.
- [grill-duo-with-docs](skills/grill-duo-with-docs/SKILL.md) records confirmed project terms and decisions during two-agent grilling.
- [pr-and-merge](skills/pr-and-merge/SKILL.md) prepares GitHub pull requests and merges only after approval for each pull request.
- [prune-worktrees-and-branches](skills/prune-worktrees-and-branches/SKILL.md) previews cleanup candidates and removes only approved worktrees or eligible branches.
- [requirements-to-spec-tickets](skills/requirements-to-spec-tickets/SKILL.md) turns ideas into clarified specs and independently scoped implementation tickets.
- [review-duo](skills/review-duo/SKILL.md) runs a strict code review across independent review axes.
- [skill-scout](skills/skill-scout/SKILL.md) finds and compares skills, with optional discovery through a local SkillRoute catalog.
- [spec-implement-loop](skills/spec-implement-loop/SKILL.md) carries an explicitly approved spec or ticket tree through implementation, verification, and bounded review remediation.

## Develop and test

This repository contains skill guides and supporting scripts, not a runnable application; it has no application development server. Automated tests use Python's standard-library `unittest` and are located in [tests/](tests/). Check the test files for the cases and setup they cover; this repository does not document a single test command.

Before making changes, read the repository guidance in [AGENTS.md](AGENTS.md) and the [domain guide](docs/agents/domain.md).

## Contribute

Use [GitHub Issues](https://github.com/EltonZhang777/AggregateSkills/issues) to report bugs or propose work; issues are this repository's tracker. The canonical triage labels are `needs-triage` (awaiting maintainer review), `needs-info` (waiting for reporter information), `ready-for-agent` (specified and ready for an agent), `ready-for-human` (requires human implementation), and `wontfix` (will not be actioned). See the [triage label guide](docs/agents/triage-labels.md) and [issue tracker guide](docs/agents/issue-tracker.md).

## License

This project is licensed under the [MIT License](LICENSE). Adapted upstream material is identified in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
