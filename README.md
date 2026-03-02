# LongRunKit

Global toolkit for long-running task management across repos.

## Deliverables
- Global CLI: `longrun` (`init`, `checkpoint`, `run-once`, `status`)
- Templates: `TASK.md`, `HEARTBEAT.md`, `DECISIONS.md`, `CONTEXT_HYGIENE.md`
- Per-project generation via `longrun init --project <dir>`
- OpenClaw config recommendations
- Heartbeat vs isolated cron tradeoff docs

## Install

```bash
cd /home/moonlight/Project/Github/MyProject/LongRunKit
chmod +x bin/longrun
./bin/longrun init --project .
```

This also installs a global symlink at `~/.local/bin/longrun`.

## Commands

### 1) init
Generate per-project files and folders.

```bash
longrun init --project /path/to/repo
# optional overwrite existing templates
longrun init --project /path/to/repo --force
```

Generates:
- `TASK.md`
- `HEARTBEAT.md`
- `DECISIONS.md`
- `docs/CONTEXT_HYGIENE.md`
- `memory/`
- `logs/`

### 2) checkpoint

```bash
longrun checkpoint "finished schema migration"
```

Appends to `memory/YYYY-MM-DD.md` with timestamp.

### 3) run-once

```bash
longrun run-once
```

Executes **Next Action** from `TASK.md` exactly once, writes log to `logs/run-once_*.log`.

### 4) status

```bash
longrun status
```

Shows current task metadata, recent logs, and today's checkpoint tail.

## Templates
Located in `templates/`:
- `TASK.md`
- `HEARTBEAT.md`
- `DECISIONS.md`
- `CONTEXT_HYGIENE.md`

## OpenClaw Recommendations
See:
- `docs/OPENCLAW_CONFIG.md`

## Heartbeat vs Isolated Cron
See:
- `docs/HEARTBEAT_VS_ISOLATED_CRON.md`

## Handoff
See:
- `docs/Handoff.md`
