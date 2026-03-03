# PARALLEL_WORK.md - Parallel Work Strategy

## Overview

This document defines how multiple agents can work on the same repository simultaneously without conflicts.

## Strategy: Git Worktree + Ownership

### Core Principle
**One worktree per agent/feature = Isolated working directory**

### Worktree Model

```
AgenticEngineering/           # Main repo (bare or shared)
├── .git/
├── worktrees/
│   ├── agent-planner/        # Planner's worktree
│   ├── agent-implementer/    # Implementer's worktree
│   └── agent-verifier/       # Verifier's worktree
└── docs/                     # Shared docs (read-only for most)
```

### Branch Naming Convention

```
<role>/<feature-or-task-id>

Examples:
- planner/us-1234-design
- implementer/us-1234-impl
- verifier/us-1234-test
- scribe/us-1234-docs
- merger/us-1234-integration
```

## Ownership Rules

### Directory Ownership Matrix

| Directory | Planner | Implementer | Verifier | Scribe | Merger |
|-----------|---------|-------------|----------|--------|--------|
| docs/ | ✏️ Write | 📖 Read | 📖 Read | ✏️ Write | 📖 Read |
| src/ | 📖 Read | ✏️ Write | 📖 Read | 📖 Read | 📖 Read |
| tests/ | 📖 Read | 📖 Read | ✏️ Write | 📖 Read | 📖 Read |
| agents/ | 📖 Read | 📖 Read | 📖 Read | ✏️ Write | 📖 Read |
| reports/ | ✏️ Write | ✏️ Write | ✏️ Write | ✏️ Write | ✏️ Write |
| scripts/ | 📖 Read | ✏️ Write | 📖 Read | 📖 Read | ✏️ Write |

Legend:
- ✏️ Write: Can modify files
- 📖 Read: Read-only access

### Conflict Resolution

1. **Same directory, different files**: Proceed in parallel
2. **Same file**: Second agent waits or takes different approach
3. **Overlapping changes**: Merger resolves

## Worktree Commands

### Create a new worktree

```bash
./scripts/worktree_new.sh <role> <task-id>

# Example:
./scripts/worktree_new.sh implementer us-1234-api
```

### List worktrees

```bash
git worktree list
```

### Remove a worktree

```bash
git worktree remove worktrees/agent-<role>
```

## Oracle Diff Mechanism

### Purpose
Compare output against known-good baselines to detect regressions.

### How It Works

1. **Baseline Generation**: Run with `--update` flag
2. **Comparison**: Run normally, compare against baseline
3. **Report**: Pass/fail with diff output

### Oracle File Structure

```
reports/oracle/
├── smoke-tests.expected      # Expected smoke test output
├── fast-tests.expected       # Expected fast test output
├── summary-template.expected # Expected summary structure
└── *.actual                  # Actual output (for diff)
```

### Degradation Strategy

1. **Primary**: Compare against existing `.expected` files
2. **Fallback**: If missing, generate new baseline with warning
3. **CI Mode**: Fail if oracle missing (forces explicit baseline)
4. **Update**: `make oracle-update` regenerates all baselines

### Running Oracle Diff

```bash
# Compare against baselines
./scripts/oracle_diff.sh

# Update baselines
./scripts/oracle_diff.sh --update
```

## Parallel Workflow Example

### Scenario: Implement feature US-1234

1. **Planner** creates design in `planner/us-1234-design`
   - Updates docs/STATUS.md, docs/TODO.md
   - Creates design doc
   
2. **Implementer** picks up in `implementer/us-1234-impl`
   - Implements in src/
   - Creates tests/ placeholders

3. **Verifier** tests in `verifier/us-1234-test`
   - Writes tests in tests/
   - Runs oracle diff
   
4. **Scribe** documents in `scribe/us-1234-docs`
   - Updates docs/
   - Creates handoff notes

5. **Merger** integrates in `merger/us-1234-integration`
   - Reviews all branches
   - Merges to main
   - Runs full test suite

## Best Practices

1. **Communicate via docs**: Use STATUS.md for coordination
2. **Atomic commits**: Small, focused changes
3. **Test before push**: Run at least smoke tests
4. **Update TODO.md**: Mark progress publicly
5. **Handoff properly**: Use HANDOFF.md template

## Anti-Patterns

❌ Multiple agents editing same file simultaneously
❌ Skipping worktree isolation
❌ Not updating STATUS.md
❌ Merging without running full tests
❌ Ignoring oracle diff failures
