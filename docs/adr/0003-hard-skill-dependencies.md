# ADR 0003: Intentional hard skill dependencies

All declared skill dependencies are intentional hard prerequisites, even when a workflow uses a prerequisite only at a particular stage or offers alternatives such as `/show-me` or `/archify`. Treating every declaration as hard simplifies dependency checks; this decision preserves the current declarations, resolution rules, and workflow behavior.
