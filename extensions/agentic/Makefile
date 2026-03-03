# Makefile - Agentic Engineering Test Layering
#
# Usage:
#   make test-smoke    # 10-30s, every iteration
#   make test-fast     # 1-3min, pre-commit (supports SAMPLE=1% or SAMPLE=10%)
#   make test-full     # Comprehensive, CI/merge gates
#   make test-all      # Run all tests
#   make oracle-update # Update oracle baselines

.PHONY: test-smoke test-fast test-full test-all oracle-update clean help

# Default target
help:
	@echo "Agentic Engineering Test Commands:"
	@echo "  make test-smoke    - Quick validation (10-30s)"
	@echo "  make test-fast     - Pre-commit tests (1-3min), use SAMPLE=1%"
	@echo "  make test-full     - Comprehensive CI tests"
	@echo "  make test-all      - Run all tests"
	@echo "  make oracle-update - Regenerate oracle baselines"
	@echo "  make clean         - Clean reports"

# Smoke tests - fastest, run every iteration
test-smoke:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Running Smoke Tests (10-30s)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@./tests/test_smoke.sh

# Fast tests - pre-commit, supports sampling
test-fast:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Running Fast Tests (1-3min)"
	@if [ -n "$(SAMPLE)" ]; then echo "  Sample: $(SAMPLE)"; fi
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@SAMPLE=$(or $(SAMPLE),) ./tests/test_fast.sh

# Full tests - comprehensive, for CI
test-full:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Running Full Tests"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@./tests/test_full.sh

# Run all tests
test-all: test-smoke test-fast test-full
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  All Tests Complete"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Update oracle baselines
oracle-update:
	@echo "Updating oracle baselines..."
	@mkdir -p reports/oracle
	@./scripts/oracle_diff.sh --update

# Clean reports
clean:
	@rm -f reports/full.log reports/summary.json reports/run_meta.json
	@rm -rf reports/oracle/*.actual
	@echo "Reports cleaned."
