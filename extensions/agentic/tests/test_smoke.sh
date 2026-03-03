#!/bin/bash
# test_smoke.sh - Quick validation tests (10-30s)
#
# Purpose: Catch obvious breakage, run every iteration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Smoke Test Suite"
echo "================"

PASSED=0
FAILED=0

# Test 1: Directory structure exists
echo -n "  [1/5] Directory structure... "
if [ -d "$REPO_ROOT/docs" ] && [ -d "$REPO_ROOT/scripts" ] && [ -d "$REPO_ROOT/agents" ] && [ -d "$REPO_ROOT/reports" ] && [ -d "$REPO_ROOT/tests" ]; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Test 2: Runner script exists and is executable
echo -n "  [2/5] Runner script... "
if [ -x "$REPO_ROOT/scripts/agent_run.sh" ]; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Test 3: Required docs exist
echo -n "  [3/5] Required docs... "
if [ -f "$REPO_ROOT/docs/STATUS.md" ] && [ -f "$REPO_ROOT/docs/TODO.md" ] && [ -f "$REPO_ROOT/docs/DECISIONS.md" ] && [ -f "$REPO_ROOT/docs/HANDOFF.md" ]; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Test 4: Agent role files exist
echo -n "  [4/5] Agent roles... "
ROLES="planner implementer verifier scribe merger"
ROLES_OK=true
for role in $ROLES; do
    if [ ! -f "$REPO_ROOT/agents/${role}.md" ]; then
        ROLES_OK=false
    fi
done
if $ROLES_OK; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Test 5: Worktree script exists
echo -n "  [5/5] Worktree script... "
if [ -x "$REPO_ROOT/scripts/worktree_new.sh" ]; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo "Smoke Tests: $PASSED passed, $FAILED failed"

if [ $FAILED -gt 0 ]; then
    echo "Status: FAILED"
    exit 1
else
    echo "Status: PASSED"
    exit 0
fi
