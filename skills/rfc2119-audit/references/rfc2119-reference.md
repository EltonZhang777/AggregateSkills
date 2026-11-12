# RFC 2119 vocabulary and application

This document is the normative vocabulary contract for the `rfc2119-audit` skill. It follows [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

This contract is normative for this skill's workflow and advisory when used to review arbitrary audited roots. Before applying another instruction from this skill, the agent MUST read this document.

## RFC 2119 keywords

These uppercase words and phrases have the RFC 2119 meanings shown here:

| Keyword or phrase | Requirement level |
| --- | --- |
| `MUST`, `REQUIRED`, `SHALL` | An absolute requirement. The specified behavior is required. |
| `MUST NOT`, `SHALL NOT` | An absolute prohibition. The specified behavior is forbidden. |
| `SHOULD`, `RECOMMENDED` | A default recommendation. A valid circumstance MAY justify a different choice, but the agent MUST understand and carefully weigh the full implications first. |
| `SHOULD NOT`, `NOT RECOMMENDED` | A default against the specified behavior. A valid circumstance MAY make the behavior acceptable or useful, but the agent MUST understand and carefully weigh the full implications first. |
| `MAY`, `OPTIONAL` | A truly optional choice. The behavior MAY be included or omitted when no other requirement depends on it. |

Capitalization and the exact keyword or phrase determine the requirement level. Bold, code formatting, headings, and table placement have no effect on its meaning.

## Applying the vocabulary

- Authored normative instructions in this skill MUST use the uppercase RFC 2119 vocabulary above. They MUST use the keyword that matches the actual force of the rule and MUST NOT use an informal synonym to express a requirement.
- `MUST` and `MUST NOT` SHOULD be reserved for runtime correctness, API or interoperability constraints, safety, explicit scope boundaries, or another condition that is genuinely absolute. RFC 2119 imperatives MUST NOT be used merely to impose an arbitrary implementation method.
- A `SHOULD` or `SHOULD NOT` rule is not an absolute requirement, but deviation still requires deliberate judgment. The agent MUST understand and weigh the consequences before choosing it.
- Descriptive facts, headings, non-normative explanations, and illustrative example prose MAY omit an RFC 2119 keyword. Examples MUST NOT be rewritten solely to add a requirement-level word when the example is not itself prescribing behavior.
- External documentation, source code, and verbatim quotations MUST retain their original wording. Their wording is not silently normalized to this contract; surrounding skill or audit text MAY identify the material as external or quoted.
- Future changes that add or change normative requirement wording MUST scan the complete installed skill documentation for consistent RFC 2119 usage, including all Markdown under this skill directory.

When applied to an arbitrary audited root, this vocabulary is advisory. The audit reports candidates for manual review and does not decide whether descriptive prose is normative.

## Exception handling

The agent MUST NOT silently deviate from a local `MUST`, `MUST NOT`, `SHOULD`, or `SHOULD NOT` rule. Before implementing such a deviation, the agent MUST:

1. The agent MUST identify the exact rule and requirement level being bypassed.
2. The agent MUST explain the reason, expected benefit, and relevant risks or compatibility impact.
3. The agent MUST ask the user to confirm the exception and wait for confirmation.
4. The agent MUST limit the exception to the confirmed case; the default rule remains in force elsewhere.

Choosing an option explicitly marked `MAY` or `OPTIONAL` is not itself an exception. A user-approved exception does not change the meaning of RFC 2119 keywords or make the exception a new default.
