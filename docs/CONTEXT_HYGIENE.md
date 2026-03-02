# Context Hygiene Guidelines

## Principles
1. **Chat history is a BUFFER, not storage** - Critical details belong in files
2. **Write ahead, then respond** - Update state before answering
3. **Log long outputs** - Keep conversation light, files heavy
4. **Checkpoint frequently** - Create recovery points often

## When to Write to Files
- **Corrections**: "It's X, not Y" → SESSION-STATE.md
- **Decisions**: "Let's do X" → DECISIONS.md
- **Preferences**: User likes/dislikes → USER.md
- **Specific values**: Numbers, dates, IDs → TASK.md
- **Draft changes**: Edits in progress → TASK.md

## File Organization
```
memory/YYYY-MM-DD.md    # Daily checkpoints and progress
logs/[timestamp]-*.txt   # Long outputs (test runs, builds, etc.)
TASK.md                  # Current task state and next actions
DECISIONS.md             # Important decisions with rationale
SESSION-STATE.md         # Active working memory (WAL target)
```

## Compaction Recovery
1. **Read working buffer** - Get danger-zone exchanges
2. **Read SESSION-STATE.md** - Restore active task context
3. **Read daily notes** - Recent progress and decisions
4. **Extract and continue** - Don't ask "where were we?"

## Output Guidelines
- **Conversations**: Keep summaries, not raw data
- **Evidence**: Point to files, not include content
- **Progress**: Update checkmarks, not descriptions
- **Blockers**: Be specific and actionable

## Cost Optimization
- **Use isolated cron** for predictable, linear progress
- **Reserve heartbeat** for complex context-dependent tasks
- **Prune aggressively** - Old tool results should be cleared
- **Compact early** - Don't wait for forced compaction

## Anti-Patterns
- ❌ Asking "what were we discussing?" (read buffer first)
- ❌ Including long logs in conversation (use files)
- ❌ Repeating failed actions without new info
- ❌ Relying solely on automatic memory flush

## Recovery Checklist
- [ ] Read `memory/working-buffer.md`
- [ ] Read `SESSION-STATE.md`
- [ ] Check `TASK.md` for current phase
- [ ] Verify `logs/` for recent outputs
- [ ] Continue from last checkpoint
