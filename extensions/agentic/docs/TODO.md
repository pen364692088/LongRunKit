# TODO.md - Agentic Engineering Micro-Tasks

## Phase 1: Foundation (可并行)
- [x] Create directory structure (docs/, scripts/, agents/, reports/, tests/)
- [x] Initialize docs/STATUS.md
- [x] Initialize docs/DECISIONS.md
- [x] Initialize docs/HANDOFF.md
- [x] Create docs/TODO.md (this file)

## Phase 2: Runner & Reports (串行)
- [x] Create scripts/agent_run.sh with logging strategy
- [x] Create reports/summary.json template
- [x] Create reports/run_meta.json template
- [x] Create reports/full.log placeholder

## Phase 3: Test Layering (可并行部分)
- [x] Create Makefile with test-smoke target
- [x] Create Makefile with test-fast target (with sampling)
- [x] Create Makefile with test-full target
- [x] Create tests/test_smoke.sh
- [x] Create tests/test_fast.sh
- [x] Create tests/test_full.sh

## Phase 4: Parallel Scaffold (可并行)
- [x] Create docs/PARALLEL_WORK.md
- [x] Create scripts/worktree_new.sh
- [x] Create scripts/oracle_diff.sh
- [x] Define ownership rules

## Phase 5: Role Templates (可并行)
- [x] Create docs/ROLES.md
- [x] Create agents/planner.md
- [x] Create agents/implementer.md
- [x] Create agents/verifier.md
- [x] Create agents/scribe.md
- [x] Create agents/merger.md

## Phase 6: CI Integration (串行)
- [x] Create .github/workflows/ci.yml
- [x] Wire smoke/fast tests into CI
- [x] Create reports/completion.json

## Summary
- Total tasks: 24
- Parallelizable groups: 3 (Phase 1, Phase 3 partial, Phase 4+5)
- Sequential dependencies: Phase 2 → Phase 6
