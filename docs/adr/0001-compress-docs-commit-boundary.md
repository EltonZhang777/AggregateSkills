# ADR 0001: Compress Docs commit boundary and storage scope

Status: Superseded by ADR-0002.

Accepted: the workflow supports only Windows hosts targeting locally attached NTFS volumes, and declares that matrix supported only after the revised manual acceptance scenarios pass. The successful atomic replacement is the commit point: failures before it must leave the source unchanged; after it, readback I/O failure is reported as “已提交但未验证” and a successful mismatching readback as “已提交但验证不符”. Neither post-commit state triggers rollback; preserve and report the verified original backup because rollback can fail and cannot provide a portable transaction guarantee.
