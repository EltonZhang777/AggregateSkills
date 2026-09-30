# Compress Docs manual scenarios

Run the user-facing skill on each intended Agent Skills host with disposable files on an ordinary local writable filesystem. Cover explicit files plus directory, glob, and all-under-root discovery.

## Bounded discovery

- Give the skill a root containing documents plus a sibling/outside document. Confirm a directory selector, root-relative glob, and “all” find only eligible files under the explicit root; reject absolute or `..` selectors. “All” must not expand to the workspace.
- Add nested dot-prefixed and host-hidden directories, a symlink directory/file, and `.original.md` backups. Confirm discovery skips them without reading contents; duplicate matches appear only once.
- While list approval is pending, redirect the selected root or one of its parent directories through a symlink/junction to an outside directory. Confirm the root/target recheck skips the changed target before reading or sending content.
- After a discovered candidate is approved and prepared, redirect its root or a parent to an outside directory before application. Confirm the apply script reports `not_applied`, creates no outside backup, and does not replace the outside file.
- Confirm discovery reads only paths and metadata before approval. It lists candidates in relative-path order with path-level skip reasons, and a refusal of the final list approval leaves all candidate contents unread and unchanged, even when one file was found.
- With root depth 0, create a path reaching depth 5 and confirm the scan pauses before that subtree. Add at least 50 path-level eligible files and confirm it pauses immediately after the 50th. Declining continuation stops the incomplete selection without reading or compressing files; approving continuation resumes discovery only, pauses again at later 50-file boundaries, and still requires a separate final list approval. Where useful, confirm it suggests a narrower selector.

## Selection and compression

- For one explicitly named file, confirm a direct compression request can apply a valid candidate without a list or per-file write approval. A candidate-only request must leave the source untouched.
- For multiple explicit paths, show the complete list and path-level skip reasons before reading any document contents or sending content to agents. Decline list approval and confirm no document content was read and no file changed. Approve a fresh list and verify only approved eligible paths are processed, with one isolated native subagent per document and parallel work where available.
- While list approval is pending, change one listed target to a symlink or make it exceed 500,000 bytes. Confirm the post-approval recheck skips it before reading or sending content, while other approved files continue. Also substitute a symlink between the final path check and open; confirm no content from its target is read or sent.
- Confirm a failed or rejected file does not stop another approved file from succeeding. If one replacement is unknown, keep that file's backup and report its state while other files continue independently.
- Use UTF-8 Markdown with frontmatter, headings, nested lists, a table, fenced and inline code, a URL, a path, a command, technical names, dates, numbers, an environment variable, and prose. Include a quoted instruction as document content. Confirm only prose is shortened; protected text, structure, frontmatter, BOM, newline style, and final-newline state stay exact; and each body is strictly shorter.
- Provide a candidate that changes protected text or is not shorter. Confirm that file's same agent receives targeted repair requests only, at most twice. If validation still fails, reject only that file and continue the rest of the approved list.
- Repeat with each supported extension and an extensionless text file. Confirm unsupported extensions, non-text or non-UTF-8 files, empty documents, files larger than 500,000 bytes, symlinks, sensitive paths, and `.original.md` backups are refused before their contents are sent to an agent.
- If no native subagent is available, decline inline fallback and confirm no file changes; then approve inline fallback for a fresh disposable batch.

## File-operation outcomes

- Create a conflicting original backup and confirm neither it nor the source is overwritten. Change a source before backup creation and confirm that file is not replaced. Change it after backup verification but before replacement and confirm replacement stops while the backup remains. Simulate staging failure and confirm the original source bytes remain and the verified backup is retained.
- On an ordinary local filesystem, confirm a successful replace return is reported as success and the exact original backup path is reported. The workflow does not read the source back after replacement.
- Make the replace operation report an error after applying the replacement. Confirm the result is “替换结果不确定”, the original backup remains available and its path is reported, no readback or rollback is attempted, and the source is not claimed to be unchanged.

Do not probe or require a particular OS, filesystem, or storage provider. These scenarios do not establish universal filesystem transaction or restoration guarantees and do not extend results to untested network, sync/cloud, virtual, or other providers.
