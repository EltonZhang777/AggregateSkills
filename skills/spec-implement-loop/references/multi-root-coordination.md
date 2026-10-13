# Multi-root coordination

Use this reference only when read-only intake and deduplication in the [main skill](../SKILL.md) leave more than one distinct root. The main skill remains authoritative for shared procedures, including graph planning, lifecycle, worker-pool limits, ticket execution, integration, review, checkpoints, status synchronization, and recovery.

- Preserve each root's source and keep its queue independent unless an explicit dependency joins the roots.
- Fill available worker slots from eligible queues in dependency order, then supplied root order (and issue number where applicable).
- A blocker pauses only its dependent work; continue other roots when they have ready tickets.
