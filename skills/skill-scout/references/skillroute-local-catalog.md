# SkillRoute local-catalog procedure

## Dependencies

If any dependency is missing, report all missing dependencies, tell the user to install them, and stop the entire workflow. Do not install dependencies automatically.

| Name | Type | Source |
| --- | --- | --- |
| SkillRoute CLI | Tool | https://github.com/erichare/skillroute |

## SkillRoute local-catalog mode

This optional local-catalog mode runs only when the user selects SkillRoute. It reads the local catalog only; it does not use a network backend.

Run the CLI and backend checks before routing:

```text
skillroute --version
skillroute backend status --backend local-token --json
skillroute inspect --json <skill-id>
skillroute search --backend local-token --json <query>
skillroute route --backend local-token --json --repo <repo> <request>
```

Accept JSON only when it parses and has the expected type and required fields: backend status is `ready` with a positive skill count; inspect identifies the requested skill; search returns a list of skill records; route returns candidates and a boolean clarification flag. Missing fields, wrong types, mismatched identity, or malformed output are unusable.

If the CLI, local backend, or catalog is unavailable, return `Unavailable`; do not present the result as evidence that a skill is absent. Give the relevant install or catalog-preparation step, but do not perform it. For temporary resolver or backend errors or unusable output, return an `Unresolved prerequisite` result, identify the exact failed check and recovery condition, and stop. Do not fall back to another discovery source.
