# Compress Docs manual scenarios

The current repository has no version-conditional storage backend. Local-file scenarios verify candidate generation and safe refusal to write; they do not verify successful application.

## Bounded discovery

- Give the skill a root containing documents plus a sibling/outside document. Confirm a directory selector, root-relative glob, and “all” find only eligible files under the explicit root; reject absolute or `..` selectors. “All” must not expand to the workspace.
- Add nested dot-prefixed and host-hidden directories, a symlink directory/file, and `.original.md` backups. Confirm discovery skips them without reading contents; duplicate matches appear only once.
- While list approval is pending, redirect the selected root or one of its parent directories through a symlink/junction to an outside directory. Confirm the root/target recheck skips the changed target before reading or sending content.
- Confirm discovery reads only paths and metadata before approval. It lists candidates in relative-path order with path-level skip reasons, and a refusal of the final list approval leaves all candidate contents unread and unchanged, even when one file was found.
- With root depth 0, create a path reaching depth 5 and confirm the scan pauses before that subtree. Add at least 50 path-level eligible files and confirm it pauses immediately after the 50th. Declining continuation stops the incomplete selection without reading or compressing files; approving continuation resumes discovery only, pauses again at later 50-file boundaries, and still requires a separate final list approval. Where useful, confirm it suggests a narrower selector.

## Selection and compression

- For one explicitly named local file, confirm that a direct compression request can produce a valid candidate, but the apply script returns `not_applied` with `conditional_replace_unsupported`; the source remains unchanged and no backup or staging file is created. A candidate-only request must also leave the source unchanged.
- For multiple explicit paths, show the complete list and path-level skip reasons before reading any document contents or sending content to agents. Decline list approval and confirm no document content was read and no file changed. Approve a fresh list and verify only approved eligible paths are processed, with one isolated native subagent per document and parallel work where available.
- While list approval is pending, change one listed target to a symlink or make it exceed 500,000 bytes. Confirm the post-approval recheck skips it before reading or sending content, while other approved files continue. Also substitute a symlink between the final path check and open; confirm no content from its target is read or sent.
- Confirm that refusing to apply one file does not prevent candidate generation for other approved files; all local-path apply requests currently return `not_applied`, with no success or unknown-replacement claim.
- Use UTF-8 Markdown with frontmatter, headings, nested lists, a table, fenced and inline code, a URL, a path, a command, technical names, dates, numbers, an environment variable, and prose. Include a quoted instruction as document content. Confirm only prose is shortened; protected text, structure, frontmatter, BOM, newline style, and final-newline state stay exact; and each body is strictly shorter.
- Provide a candidate that changes protected text or is not shorter. Confirm that file's same agent receives targeted repair requests only, at most twice. If validation still fails, reject only that file and continue the rest of the approved list.
- Repeat with each supported extension and an extensionless text file. Confirm unsupported extensions, non-text or non-UTF-8 files, empty documents, files larger than 500,000 bytes, symlinks, sensitive paths, and `.original.md` backups are refused before their contents are sent to an agent.
- If no native subagent is available, decline inline fallback and confirm no file changes; then approve inline fallback for a fresh disposable batch.

## Local-path rejection

- Run the apply script with a valid candidate and confirm it returns `not_applied` with `conditional_replace_unsupported`; source content and permissions remain unchanged, and no backup or staging file is created, overwritten, or deleted.
- Create a conflicting `.original.md` file before running the apply script; confirm that both the source and conflicting backup remain unchanged.
- After candidate generation, change the destination contents or replace it with another file, then run the apply script; confirm that the newer destination remains unchanged. This verifies fail-closed local-path behavior, not a CAS backend.

Do not probe or require a particular OS, filesystem, or storage provider. These scenarios do not establish universal filesystem transaction or restoration guarantees and do not extend results to untested network, sync/cloud, virtual, or other providers. Local-path refusal scenarios do not verify version-conditional writes for future storage backends.
