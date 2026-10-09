# ADR 0004: Self-contained skill package resources

Each skill package carries the supporting documents, fixed references, and manifest inputs it needs, and package-internal file references resolve within that package. Documents read at runtime from the repository receiving a task, such as its root `AGENTS.md`, remain external context inputs; this keeps installed skills independent of fixed files in the source repository while preserving target-specific guidance.
