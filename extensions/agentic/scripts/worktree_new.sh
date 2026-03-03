#!/bin/bash
# worktree_new.sh - Create a new worktree for parallel work
#
# Usage:
#   ./scripts/worktree_new.sh <role> <task-id>
#
# Example:
#   ./scripts/worktree_new.sh implementer us-1234-api

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Arguments
ROLE="${1:-}"
TASK_ID="${2:-}"

# Validation
if [ -z "$ROLE" ] || [ -z "$TASK_ID" ]; then
    echo "Usage: $0 <role> <task-id>"
    echo ""
    echo "Roles: planner, implementer, verifier, scribe, merger"
    echo ""
    echo "Example:"
    echo "  $0 implementer us-1234-api"
    exit 1
fi

# Validate role
case "$ROLE" in
    planner|implementer|verifier|scribe|merger)
        ;;
    *)
        echo "Error: Invalid role '$ROLE'"
        echo "Valid roles: planner, implementer, verifier, scribe, merger"
        exit 1
        ;;
esac

# Configuration
WORKTREE_DIR="$REPO_ROOT/worktrees/agent-$ROLE"
BRANCH_NAME="${ROLE}/${TASK_ID}"

# Check if worktree already exists
if [ -d "$WORKTREE_DIR" ]; then
    echo "Error: Worktree already exists at $WORKTREE_DIR"
    echo "Remove it first with: git worktree remove $WORKTREE_DIR"
    exit 1
fi

# Check if branch already exists
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "Warning: Branch '$BRANCH_NAME' already exists"
    echo "Creating worktree with existing branch..."
fi

# Create worktrees directory if needed
mkdir -p "$REPO_ROOT/worktrees"

# Create the worktree
echo "Creating worktree: $WORKTREE_DIR"
echo "Branch: $BRANCH_NAME"

if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    # Branch exists, just create worktree
    git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
else
    # Create new branch and worktree
    git worktree add -b "$BRANCH_NAME" "$WORKTREE_DIR"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Worktree Created"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Path:   $WORKTREE_DIR"
echo "  Branch: $BRANCH_NAME"
echo "  Role:   $ROLE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To start working:"
echo "  cd $WORKTREE_DIR"
echo ""
echo "To return to main:"
echo "  cd $REPO_ROOT"
echo ""
echo "To remove when done:"
echo "  git worktree remove $WORKTREE_DIR"
