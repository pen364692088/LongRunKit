#!/bin/bash
# agent_run.sh - Unified Runner for Agentic Engineering
# 
# Usage:
#   ./scripts/agent_run.sh [command] [args...]
#   SEED=42 ./scripts/agent_run.sh [command]
#
# Outputs:
#   - Terminal: 30-80 line summary
#   - reports/full.log: Complete execution log
#   - reports/summary.json: Structured summary
#   - reports/run_meta.json: Run metadata

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORTS_DIR="$REPO_ROOT/reports"
MAX_TERMINAL_LINES=60

# Initialize reports directory
mkdir -p "$REPORTS_DIR"

# Generate run ID
RUN_ID="run-$(date +%Y%m%d-%H%M%S)-$${RANDOM:-$$}"

# Log files
FULL_LOG="$REPORTS_DIR/full.log"
SUMMARY_JSON="$REPORTS_DIR/summary.json"
META_JSON="$REPORTS_DIR/run_meta.json"

# Capture start time
START_TIME=$(date +%s)
START_TIMESTAMP=$(date -Iseconds)

# Seed handling
SEED="${SEED:-$(date +%s)}"

# Command to run
COMMAND="${*:-echo 'No command specified'}"

# Function: Log to file only
log_file() {
    echo "$1" >> "$FULL_LOG"
}

# Function: Generate metadata JSON
generate_meta() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    local git_commit=""
    local git_branch=""
    
    cd "$REPO_ROOT"
    git_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    
    cat > "$META_JSON" << METADATA
{
  "run_id": "$RUN_ID",
  "timestamp": "$START_TIMESTAMP",
  "duration_seconds": $duration,
  "seed": $SEED,
  "command": "$COMMAND",
  "git": {
    "commit": "$git_commit",
    "branch": "$git_branch"
  },
  "environment": {
    "shell": "${SHELL:-unknown}",
    "pwd": "$REPO_ROOT"
  }
}
METADATA
}

# Function: Generate summary JSON
generate_summary() {
    local status="$1"
    local tests_passed="${2:-0}"
    local tests_failed="${3:-0}"
    
    cat > "$SUMMARY_JSON" << SUMMARY
{
  "run_id": "$RUN_ID",
  "status": "$status",
  "tests": {
    "passed": $tests_passed,
    "failed": $tests_failed,
    "total": $((tests_passed + tests_failed))
  },
  "files_modified": [],
  "next_steps": []
}
SUMMARY
}

# Initialize log file
echo "=== Agentic Engineering Run Log ===" > "$FULL_LOG"
echo "Run ID: $RUN_ID" >> "$FULL_LOG"
echo "Timestamp: $START_TIMESTAMP" >> "$FULL_LOG"
echo "Command: $COMMAND" >> "$FULL_LOG"
echo "Seed: $SEED" >> "$FULL_LOG"
echo "---" >> "$FULL_LOG"

# Header for terminal
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Agentic Engineering Runner"
echo "  Run ID: $RUN_ID"
echo "  Seed: $SEED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Execute command and capture output
log_file "Executing: $COMMAND"
log_file ""

# Run command and capture output
TEMP_OUTPUT=$(mktemp)
if eval "$COMMAND" 2>&1 | tee "$TEMP_OUTPUT" >> "$FULL_LOG"; then
    EXIT_CODE=0
    STATUS="success"
else
    EXIT_CODE=$?
    STATUS="failed"
fi

# Generate summary for terminal (limited lines)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Show last N lines of output
TAIL_LINES=$(wc -l < "$TEMP_OUTPUT")
if [ "$TAIL_LINES" -gt "$MAX_TERMINAL_LINES" ]; then
    echo "  (Output truncated. Full log: reports/full.log)"
    echo "  Showing last $MAX_TERMINAL_LINES of $TAIL_LINES lines:"
    echo ""
    tail -n "$MAX_TERMINAL_LINES" "$TEMP_OUTPUT"
else
    cat "$TEMP_OUTPUT"
fi

# Cleanup
rm -f "$TEMP_OUTPUT"

# Finalize
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Status: $STATUS"
echo "  Exit Code: $EXIT_CODE"
echo "  Full Log: reports/full.log"
echo "  Metadata: reports/run_meta.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Generate metadata and summary
generate_meta
generate_summary "$STATUS"

# Update STATUS.md if present
if [ -f "$REPO_ROOT/docs/STATUS.md" ]; then
    # Append run info
    echo "" >> "$REPO_ROOT/docs/STATUS.md"
    echo "## Run: $RUN_ID" >> "$REPO_ROOT/docs/STATUS.md"
    echo "- Status: $STATUS" >> "$REPO_ROOT/docs/STATUS.md"
    echo "- Command: $COMMAND" >> "$REPO_ROOT/docs/STATUS.md"
    echo "- Seed: $SEED" >> "$REPO_ROOT/docs/STATUS.md"
fi

exit $EXIT_CODE
