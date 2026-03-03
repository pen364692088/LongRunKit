#!/bin/bash
# test_fast.sh - Pre-commit tests (1-3min)
#
# Purpose: Validate core functionality before commit
# Supports sampling: SAMPLE=1% or SAMPLE=10%

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SAMPLE="${SAMPLE:-}"

echo "Fast Test Suite"
echo "==============="

if [ -n "$SAMPLE" ]; then
    echo "Sampling mode: $SAMPLE"
fi

PASSED=0
FAILED=0

# Test 1: Runner produces valid output
echo -n "  [1/6] Runner output validation... "
cd "$REPO_ROOT"
if ./scripts/agent_run.sh echo "test" > /dev/null 2>&1; then
    if [ -f "reports/summary.json" ] && [ -f "reports/run_meta.json" ]; then
        echo "✓"
        PASSED=$((PASSED + 1))
    else
        echo "✗ (missing output files)"
        FAILED=$((FAILED + 1))
    fi
else
    echo "✗ (runner failed)"
    FAILED=$((FAILED + 1))
fi

# Test 2: Summary JSON is valid
echo -n "  [2/6] Summary JSON validation... "
if command -v python3 > /dev/null 2>&1; then
    if python3 -c "import json; json.load(open('$REPO_ROOT/reports/summary.json'))" 2>/dev/null; then
        echo "✓"
        PASSED=$((PASSED + 1))
    else
        echo "✗ (invalid JSON)"
        FAILED=$((FAILED + 1))
    fi
else
    echo "⊘ (skipped - no python3)"
    PASSED=$((PASSED + 1))
fi

# Test 3: Meta JSON is valid
echo -n "  [3/6] Meta JSON validation... "
if command -v python3 > /dev/null 2>&1; then
    if python3 -c "import json; json.load(open('$REPO_ROOT/reports/run_meta.json'))" 2>/dev/null; then
        echo "✓"
        PASSED=$((PASSED + 1))
    else
        echo "✗ (invalid JSON)"
        FAILED=$((FAILED + 1))
    fi
else
    echo "⊘ (skipped - no python3)"
    PASSED=$((PASSED + 1))
fi

# Test 4: Makefile targets exist
echo -n "  [4/6] Makefile targets... "
MAKEFILE="$REPO_ROOT/Makefile"
TARGETS_OK=true
for target in test-smoke test-fast test-full; do
    if ! grep -q "^${target}:" "$MAKEFILE" 2>/dev/null; then
        TARGETS_OK=false
    fi
done
if $TARGETS_OK; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Test 5: Parallel work documentation
echo -n "  [5/6] Parallel work docs... "
if [ -f "$REPO_ROOT/docs/PARALLEL_WORK.md" ]; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Test 6: Roles documentation
echo -n "  [6/6] Roles documentation... "
if [ -f "$REPO_ROOT/docs/ROLES.md" ]; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo "Fast Tests: $PASSED passed, $FAILED failed"

if [ $FAILED -gt 0 ]; then
    echo "Status: FAILED"
    exit 1
else
    echo "Status: PASSED"
    exit 0
fi
