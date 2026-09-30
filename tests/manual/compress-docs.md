# Compress Docs manual scenarios

Run the user-facing skill on each intended Agent Skills host with disposable files on an ordinary local writable filesystem. This ticket covers one explicitly named file or a user-approved list of explicitly named files; directory and pattern discovery is covered separately.

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
