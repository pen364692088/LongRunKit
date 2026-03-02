# Heartbeat vs Isolated Cron

## Summary
- **Heartbeat:** high observability, higher token cost.
- **Isolated Cron:** lower cost, better for unattended long jobs.

## Comparison

| Dimension | Heartbeat | Isolated Cron |
|---|---|---|
| Cost per interval | Higher (full agent turn each check) | Lower (separate background loop) |
| In-chat visibility | Immediate | Indirect via status/logs |
| Best use case | Interactive debug/supervision | Routine background execution |
| Failure recovery | Good if human watching | Requires strict checkpoint discipline |
| Scale to many tasks | Poor-medium | Good |

## Decision Rule
1. If human must intervene frequently within minutes -> Heartbeat.
2. Otherwise -> Isolated Cron + milestone checkpoints.

## Safety Guardrails
- Enforce `run-once` before any unattended schedule.
- Keep authoritative state in `TASK.md` + `memory/` + `logs/`.
- Use `longrun status` as source of truth for health.
