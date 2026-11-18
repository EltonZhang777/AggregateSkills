### Navigation-only issue cache (optional)

This repository explicitly opts into a navigation-only issue cache.

The cache may contain only issue summary metadata, its source, and a read timestamp. It may shorten discovery. It is never authoritative for writes, assignment, labels, closure, or verification. Read the tracker directly before any of those actions and whenever the timestamp is missing, stale, or the issue state is disputed.

Invalidate the entry when its source changes, the repository changes, the issue summary schema changes, or the cached state cannot be reconciled with a direct read. A missing cache entry means only that navigation metadata is unavailable; it does not mean the issue is absent.

This template defines a convention only. It does not provide, require, or claim a cache runtime.
