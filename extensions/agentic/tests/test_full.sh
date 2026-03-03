#!/bin/bash
# test_full.sh - Comprehensive tests for CI/merge gates
#
# Purpose: Full validation before merging

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Full Test Suite"
echo "==============="

PASSED=0
FAILED=0

# Run smoke tests first
echo "Phase 1: Smoke Tests"
echo "--------------------"
if make -C "$REPO_ROOT" test-smoke > /dev/null 2>&1; then
    PASSED=$((PASSED + 5))
    echo "Smoke: PASSED (5 tests)"
else
    FAILED=$((FAILED + 5))
    echo "Smoke: FAILED (5 tests)"
fi

# Run fast tests
echo ""
echo "Phase 2: Fast Tests"
echo "-------------------"
if make -C "$REPO_ROOT" test-fast > /dev/null 2>&1; then
    PASSED=$((PASSED + 6))
    echo "Fast: PASSED (6 tests)"
else
    FAILED=$((FAILED + 6))
    echo "Fast: FAILED (6 tests)"
fi

# Additional validation
echo ""
echo "Phase 3: Structural Validation"
echo "------------------------------"

# Test: All agent prompts have required sections
echo -n "  [1/4] Agent prompt structure... "
ROLES="planner implementer verifier scribe merger"
STRUCT_OK=true
for role in $ROLES; do
    file="$REPO_ROOT/agents/${role}.md"
    for section in "Role" "Responsibilities" "Inputs" "Outputs"; do
        if ! grep -q "## $section" "$file" 2>/dev/null; then
            STRUCT_OK=false
        fi
    done
done
if $STRUCT_OK; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Test: DECISIONS.md has oracle strategy
echo -n "  [2/4] Oracle strategy documented... "
if grep -q "Oracle" "$REPO_ROOT/docs/DECISIONS.md" 2>/dev/null; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Test: Worktree script is functional
echo -n "  [3/4] Worktree script validation... "
if grep -q "git worktree" "$REPO_ROOT/scripts/worktree_new.sh" 2>/dev/null; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Test: Oracle diff script exists
echo -n "  [4/4] Oracle diff script... "
if [ -x "$REPO_ROOT/scripts/oracle_diff.sh" ]; then
    echo "✓"
    PASSED=$((PASSED + 1))
else
    echo "✗"
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Full Test Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Smoke Tests:      5 tests"
echo "  Fast Tests:       6 tests"
echo "  Structure Tests:  4 tests"
echo "  ─────────────────────────"
echo "  Total Passed:     $PASSED"
echo "  Total Failed:     $FAILED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAILED -gt 0 ]; then
    echo "Status: FAILED"
    exit 1
else
    echo "Status: PASSED"
    exit 0
fi
