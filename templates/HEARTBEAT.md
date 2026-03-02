# Heartbeat Rules for Long-Running Tasks

## Protocol
1. **Always read TASK.md first** - Get current state and next_action
2. **Check DoD completion** - If all items checked, mark phase=done and stop
3. **Execute next_action** - If DoD not complete, run the specified action
4. **Update TASK.md** - Record results, evidence, and new next_action
5. **Handle blockers** - If blocked, output: `BLOCKED: [specific need]`

## Output Rules
- **Long outputs**: Write to `logs/[timestamp]-[action].txt`, summarize in conversation
- **Evidence**: Update TASK.md with file paths, not content
- **Progress**: Mark completed DoD items, update phase
- **Blockers**: Be specific about what's needed to unblock

## Cost Control
- **Default**: Respond `HEARTBEAT_OK` if no action needed
- **Active work**: Only execute when next_action is clear
- **Avoid loops**: Don't repeat failed actions without new information

## Health Checks
- Repository exists and accessible
- Required files (TASK.md) present and readable
- Logs directory writable
- Git status clean (optional, for checkpoint commits)

If any health check fails: `ALERT: [specific issue]`
