#!/bin/bash
# oracle_diff.sh - Compare outputs against known-good baselines
#
# Usage:
#   ./scripts/oracle_diff.sh           # Compare against baselines
#   ./scripts/oracle_diff.sh --update  # Update baselines
#   ./scripts/oracle_diff.sh --check   # Exit code only (for CI)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ORACLE_DIR="$REPO_ROOT/reports/oracle"

# Parse arguments
MODE="compare"
for arg in "$@"; do
    case "$arg" in
        --update) MODE="update" ;;
        --check) MODE="check" ;;
        --help) 
            echo "Usage: $0 [--update|--check]"
            echo ""
            echo "Modes:"
            echo "  (default)  Compare against baselines"
            echo "  --update   Update/reate baselines"
            echo "  --check    Exit code only (for CI)"
            exit 0
            ;;
    esac
done

# Ensure oracle directory exists
mkdir -p "$ORACLE_DIR"

# Define what to check
declare -A CHECKS
CHECKS["smoke-tests"]="make test-smoke 2>&1 | tail -20"
CHECKS["fast-tests"]="make test-fast 2>&1 | tail -20"
CHECKS["summary-template"]="cat $REPO_ROOT/reports/summary.json"

# Function: Compare or update
process_check() {
    local name="$1"
    local cmd="$2"
    local expected="$ORACLE_DIR/${name}.expected"
    local actual="$ORACLE_DIR/${name}.actual"
    
    case "$MODE" in
        update)
            echo "Updating: $name"
            eval "$cmd" > "$expected"
            echo "  → $expected"
            ;;
        compare|check)
            if [ ! -f "$expected" ]; then
                if [ "$MODE" = "check" ]; then
                    echo "ERROR: Missing oracle baseline: $expected"
                    return 1
                fi
                echo "WARNING: Missing oracle baseline: $expected"
                echo "Creating new baseline..."
                eval "$cmd" > "$expected"
            fi
            
            eval "$cmd" > "$actual"
            
            if diff -q "$expected" "$actual" > /dev/null 2>&1; then
                if [ "$MODE" = "compare" ]; then
                    echo "✓ $name: PASSED"
                fi
                return 0
            else
                if [ "$MODE" = "compare" ]; then
                    echo "✗ $name: FAILED"
                    echo "--- Expected"
                    echo "+++ Actual"
                    diff -u "$expected" "$actual" | head -20
                fi
                return 1
            fi
            ;;
    esac
}

# Main
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Oracle Diff: $MODE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

EXIT_CODE=0

for name in "${!CHECKS[@]}"; do
    if ! process_check "$name" "${CHECKS[$name]}"; then
        EXIT_CODE=1
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

case "$MODE" in
    update)
        echo "Baselines updated."
        ;;
    compare|check)
        if [ $EXIT_CODE -eq 0 ]; then
            echo "All oracle checks passed."
        else
            echo "Some oracle checks failed."
            [ "$MODE" = "compare" ] && echo "Run with --update to update baselines."
        fi
        ;;
esac

exit $EXIT_CODE
