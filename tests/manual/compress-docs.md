# Compress Docs manual scenarios

Run the user-facing skill on each intended Agent Skills host with disposable files on an ordinary local writable filesystem. This ticket covers one explicitly named file per run.

## Target and candidate

- Test one file path at a time. Confirm no other file is discovered or changed.
- Use UTF-8 Markdown with frontmatter, headings, nested lists, a table, fenced and inline code, a URL, a path, a command, technical names, dates, numbers, an environment variable, and prose. Include a quoted instruction as document content. Confirm only prose is shortened; protected text, structure, frontmatter, BOM, newline style, and final-newline state stay exact; and the body is strictly shorter.
- Repeat with each supported extension and an extensionless text file. Confirm unsupported extensions, non-text or non-UTF-8 files, empty documents, files larger than 500,000 bytes, symlinks, sensitive paths, and `.original.md` backups are refused before their contents are sent to an agent.
- Provide a candidate that changes protected text or is not shorter. Confirm the same agent receives targeted repair requests only, at most twice. If validation still fails, confirm the source is not passed to the apply script.
- Confirm a direct request to compress the named file authorizes applying a validated candidate without a second write approval. A request for a candidate only must leave the source untouched. If no native subagent is available, decline inline fallback and confirm no write; then approve inline fallback on a disposable copy.

## File-operation outcomes

- Create a conflicting original backup and confirm neither it nor the source is overwritten. Change the source before backup creation and confirm replacement stops. Change it after backup verification but before replacement and confirm replacement stops while the backup remains. Simulate staging failure and confirm the original source bytes remain and the verified backup is retained.
- On an ordinary local filesystem, confirm a successful replace return is reported as success and the exact original backup path is reported. The workflow does not read the source back after replacement.
- Make the replace operation report an error after applying the replacement. Confirm the result is “替换结果不确定”, the original backup remains available and its path is reported, no readback or rollback is attempted, and the source is not claimed to be unchanged.

Do not probe or require a particular OS, filesystem, or storage provider. These scenarios do not establish universal filesystem transaction or restoration guarantees and do not extend results to untested network, sync/cloud, virtual, or other providers.
