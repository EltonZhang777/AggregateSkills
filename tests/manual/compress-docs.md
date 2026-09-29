# Compress Docs manual scenarios

Run at the user-facing Skill boundary on each intended Agent Skills host with disposable files on an ordinary local writable filesystem. Cover selection through each file's final outcome. Files are independent: one file's failure does not undo another file's successful replacement.

## Storage scope

Do not probe or require a particular OS, filesystem, or storage provider, and do not reject a path solely because that information is unavailable. The workflow is best-effort and makes no universal filesystem transaction or restoration guarantee. Run these checks on ordinary local filesystems; do not extend the result to untested network, sync/cloud, virtual, or other providers.

## Selection and compression

- Test one path, multiple explicit paths, glob selection, and directory discovery. Keep discovery within the user-specified root. Exclude hidden directories and `.original.md` backups.
- For recursive discovery, pause at relative depth 5 or the 50th eligible document and ask before continuing. After continuation, finish discovery, show the complete candidate list, and ask separately before compression.
- Use a UTF-8 Markdown file with frontmatter, headings, nested lists, a table, fenced and inline code, a URL, a path, a command, technical names, dates, numbers, an environment variable, and prose. Include a quoted instruction as document content. Confirm only prose is shortened; protected text and structure stay exact; and the body is strictly shorter.
- Confirm each file is handled independently by an isolated, non-interactive native subagent where available. If unavailable, decline inline fallback and confirm no write; then approve inline fallback on a disposable copy and verify it still requires write approval.
- Before any write, show the source and adjacent original-backup paths and request approval. Decline and confirm no write. Approve on a fresh run; verify the original backup before replacement, stage the candidate in the source directory, and invoke the host's replace operation.
- Repeat with each supported extension and an extensionless text file. Confirm unsupported extensions, non-text or non-UTF-8 files, empty documents, files larger than 500,000 bytes, symlinks, sensitive paths, and backup files are refused before sending their contents to an agent.

## Candidate validation

Provide a candidate that changes a protected command or is not shorter. Confirm the same agent receives targeted repair requests only, at most twice. If validation still fails, confirm the candidate is rejected without changing the source. Where no native subagent is available, confirm inline compression requires explicit approval.

## File-operation outcomes

- Create a conflicting original backup and confirm neither it nor the source is overwritten. Change the source before replacement and confirm the write is refused. Simulate staging failure and confirm the source is unchanged.
- On an ordinary local filesystem, confirm a successful replace return is reported as success and the retained backup path is reported. The workflow does not read the source back after replacement or automatically roll back.
- Make the replace operation report an error. Confirm the result is reported as “替换结果不确定”, the original backup remains available and its path is reported, and the source is not claimed to be unchanged. Do not attempt rollback.
- In a batch, confirm a failed file does not undo another file's successful replacement and that each file receives its own result.
