# OpenClaw Configuration Recommendations for LongRunKit

## Goals
- Keep long tasks recoverable across compaction/truncation
- Minimize token burn from monitoring loops
- Preserve deterministic evidence trail in repo artifacts

## Recommended Baseline

```yaml
openclaw:
  compaction:
    enabled: true
    strategy: conservative

  contextPruning:
    enabled: true
    ttlMinutes: 180   # treat as best-effort

  memoryFlush:
    thresholdTokens: 120000

longrun:
  checkpoint:
    onMilestone: true
    minIntervalMinutes: 15
  execution:
    defaultMode: isolated-cron
```

## Operational Rules
1. Never depend on chat context as source of truth.
2. Checkpoint at every milestone (not token-boundary guesses).
3. Save long command output in `logs/`, not chat.
4. Use `longrun run-once` before enabling unattended cron loops.

## Mode Selection
- Default: **isolated-cron** for routine/background work.
- Use heartbeat only for short interactive diagnosis windows.

## Validation Checklist
- [ ] `longrun init` completed
- [ ] `TASK.md` has executable **Next Action**
- [ ] `longrun run-once` produced `logs/run-once_*.log`
- [ ] `longrun checkpoint` updated `memory/YYYY-MM-DD.md`
- [ ] `longrun status` reflects current state
