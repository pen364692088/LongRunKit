# Validation Evidence

## Global CLI check
```bash
~/.local/bin/longrun --version
# => longrun 1.1.1
```

## Repo A verification
Target: `/tmp/lrk-repo-a`

Executed:
- `longrun init --project /tmp/lrk-repo-a`
- Edited `TASK.md` -> `**next_action:** echo repo-a-ok`
- `longrun run-once`
- `longrun checkpoint "repo-a milestone"`
- `longrun status`

Evidence:
- `/tmp/lrk-repo-a/logs/run-once_20260301_193706.log`
- `/tmp/lrk-repo-a/memory/2026-03-01.md`
- `/tmp/lrk-a-status.txt`

## Repo B verification
Target: `/tmp/lrk-repo-b`

Executed:
- `longrun init --project /tmp/lrk-repo-b`
- Edited `TASK.md` -> `**next_action:** echo repo-b-ok`
- `longrun run-once`
- `longrun checkpoint "repo-b milestone"`
- `longrun status`

Evidence:
- `/tmp/lrk-repo-b/logs/run-once_20260301_193707.log`
- `/tmp/lrk-repo-b/memory/2026-03-01.md`
- `/tmp/lrk-b-status.txt`

## DoD mapping
- 2 repos verified: ✅
- run-once logging verified: ✅
- docs complete: ✅ (`README.md`, `docs/OPENCLAW_CONFIG.md`, `docs/HEARTBEAT_VS_ISOLATED_CRON.md`, `docs/Handoff.md`)
- Handoff delivered: ✅
