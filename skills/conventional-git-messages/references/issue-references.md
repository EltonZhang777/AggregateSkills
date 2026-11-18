# Issue and pull request references

- Preserve every supplied issue or pull request reference in its reference block: commit messages accept issue and pull request references, and pull request descriptions accept issue references.
- For each supplied issue reference, use `closes #N` only when the change resolves that issue and it should close on merge; use `refs #N` for other related issues.
- Use only issue numbers supplied in context; never invent references.
