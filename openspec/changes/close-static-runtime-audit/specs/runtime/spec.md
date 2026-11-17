## ADDED Requirements

### Requirement: Due schedule acquisition is not deferred by content refresh
A permitted due launch-schedule acquisition SHALL precede optional content-only rebuilding in the same prepare invocation, while recovery, quota and inflight serialization continue to deny unsafe calls. Metadata cadence remains independent.

#### Scenario: Due schedule or constrained request
- **WHEN** an accepted launch expires with no successor and schedule acquisition is due, with either permission or a pending recovery, quota or inflight constraint
- **THEN** the same prepare invocation attempts the permitted request, and a constrained invocation makes no new provider call.

### Requirement: Metadata executing source matches tracked bytes
The metadata collector SHALL bind its declared revision to its five tracked executing source files before constructing publisher authority or reserving provider capacity, including files hidden by Git index hints.

#### Scenario: Hidden source modification
- **WHEN** an executing metadata source differs from HEAD under assume-unchanged or skip-worktree
- **THEN** the collector refuses before publisher or provider side effects.

### Requirement: Current selected state remains accurate
Current trusted snapshots SHALL retain freshness, selected-launch rollover, at-most-once quiet-aware reminders, and clock operation without per-frame network or Storage access. Current reminder rows and their consumed ledger remain authoritative; unsupported snapshot shapes SHALL fail closed.

#### Scenario: Context advances and reminders resume
- **WHEN** a selected context becomes stale, rolls over, or its reminder callback repeats
- **THEN** the selected successor has its own original freshness and no consumed eligible reminder is repeated.
