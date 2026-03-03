# LongRunKit v2.0

Global toolkit for long-running task management with Agentic Engineering extension.

## What's New in v2.0

- **Agentic Engineering Extension**: Optional multi-agent workflow support
- **Test Layering**: smoke/fast/full test commands
- **Report Generation**: Structured output with summary.json
- **Unified CLI**: One tool for all long-task needs

## Install

```bash
cd /home/moonlight/Project/Github/MyProject/LongRunKit
./bin/longrun init --project .
# This installs global symlink: ~/.local/bin/longrun
```

## Commands

### Core Commands

```bash
# Initialize in a project (basic)
longrun init --project /path/to/repo

# Initialize with Agentic Engineering extension
longrun init --project /path/to/repo --with-agentic

# Save progress checkpoint
longrun checkpoint "completed phase 1"

# Execute next action from TASK.md
longrun run-once

# Show status
longrun status
```

### Agentic Commands (requires --with-agentic)

```bash
# Quick validation (10-30s)
longrun test-smoke

# Pre-commit tests with sampling
longrun test-fast          # 100% of tests
SAMPLE=10 longrun test-fast  # 10% sampling

# Full test suite
longrun test-full

# Run command and generate reports
longrun report "pytest tests/"
```

## Directory Structure

### Basic Init
```
project/
├── TASK.md           # Task tracking
├── HEARTBEAT.md      # Heartbeat checklist
├── DECISIONS.md      # Decision log
├── docs/
│   └── CONTEXT_HYGIENE.md
├── memory/           # Checkpoints
└── logs/             # Run logs
```

### With --with-agentic
```
project/
├── TASK.md
├── HEARTBEAT.md
├── DECISIONS.md
├── docs/
│   ├── STATUS.md
│   ├── TODO.md
│   ├── DECISIONS.md
│   ├── HANDOFF.md
│   ├── PARALLEL_WORK.md
│   └── ROLES.md
├── scripts/
│   ├── agent_run.sh
│   ├── worktree_new.sh
│   └── oracle_diff.sh
├── tests/
│   ├── test_smoke.sh
│   ├── test_fast.sh
│   └── test_full.sh
├── agents/
│   ├── planner.md
│   ├── implementer.md
│   ├── verifier.md
│   ├── scribe.md
│   └── merger.md
├── reports/
├── memory/
├── logs/
└── .github/workflows/ci.yml
```

## Agentic Engineering Features

### Test Layering
- **smoke**: 10-30s, essential validation
- **fast**: 1-3min, pre-commit checks with optional sampling
- **full**: comprehensive suite for CI

### Agent Roles
- **planner.md**: Task breakdown and strategy
- **implementer.md**: Code implementation
- **verifier.md**: Testing and reports
- **scribe.md**: Documentation updates
- **merger.md**: Merge and CI management

### Parallel Work
```bash
# Create isolated worktree for agent
./scripts/worktree_new.sh agent-alpha feature-x

# Oracle diff validation
./scripts/oracle_diff.sh baseline/ current/
```

## Makefile Targets

When initialized with `--with-agentic`:

```bash
make test-smoke   # Quick validation
make test-fast    # Pre-commit (SAMPLE=1|10|100)
make test-full    # Full suite
```

## Integration with OpenClaw

LongRunKit is integrated with the `agentic-engineering` skill. When a long task is detected, the agent automatically:

1. Runs `longrun init --with-agentic` in the project
2. Uses `longrun checkpoint` to save progress
3. Runs `longrun test-smoke` for quick validation
4. Updates `docs/STATUS.md` each iteration

## Templates

Located in `templates/`:
- `TASK.md` - Task tracking template
- `HEARTBEAT.md` - Heartbeat checklist
- `DECISIONS.md` - Decision log template
- `CONTEXT_HYGIENE.md` - Context management guidelines

## Extension Development

Extensions are located in `extensions/`:
```
extensions/
└── agentic/       # Agentic Engineering extension
    ├── scripts/
    ├── tests/
    ├── agents/
    └── docs/
```

## Documentation

- `docs/HEARTBEAT_VS_ISOLATED_CRON.md` - Tradeoff analysis
- `docs/OPENCLAW_CONFIG.md` - Configuration guide
- `docs/Handoff.md` - Session handoff guide

## License

MIT
