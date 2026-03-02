# Handoff.md

## What was built
- Global CLI: `longrun` with `init/checkpoint/run-once/status`
- Template set under `templates/`
- Per-project generation (`longrun init --project <repo>`)
- OpenClaw recommendations doc (`docs/OPENCLAW_CONFIG.md`)
- Heartbeat vs isolated cron tradeoff doc (`docs/HEARTBEAT_VS_ISOLATED_CRON.md`)

## Quick start

```bash
cd /home/moonlight/Project/Github/MyProject/LongRunKit
chmod +x bin/longrun
./bin/longrun init --project /path/to/target-repo
```

If `~/.local/bin` is on PATH, use directly:

```bash
longrun status
```

## Operator workflow
1. `longrun init --project <repo>`
2. Edit `<repo>/TASK.md` and set `**Next Action:**` to one executable command
3. `cd <repo> && longrun run-once`
4. `longrun checkpoint "milestone note"`
5. `longrun status`

## Verification evidence (DoD)
- Verified in 2 repos (see commands/logs in validation section)
- run-once logging confirmed (`logs/run-once_*.log`)
- docs completed (`README.md`, OpenClaw config, cron tradeoff, this handoff)

## Known risks
- `run-once` executes shell from `TASK.md` Next Action; treat TASK.md as trusted input only.
- Requires `bash`, `sed`, `awk`, and write permission in target repo.

## Next improvements (optional)
- Add `longrun doctor` (env/path checks)
- Add JSON output mode for `status`
- Add safe allowlist mode for run-once commands
