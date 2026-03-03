# DECISIONS.md - Key Trade-offs and Decisions

## 2026-03-02: Initial Framework Design

### Decision 1: Test Layering Strategy
**Choice**: Three-tier testing (smoke/fast/full)
**Rationale**: 
- Smoke (10-30s): Every iteration, catches obvious breakage
- Fast (1-3min): Pre-commit, validates core functionality
- Full: CI/merge gates, comprehensive coverage
**Alternatives Considered**: Single test suite, two-tier
**Trade-off**: More test targets = more maintenance, but faster feedback loops

### Decision 2: Runner Output Strategy
**Choice**: 30-80 line terminal summary + full log to file
**Rationale**: 
- Prevents terminal spam
- Preserves full context for debugging
- Structured JSON for automation
**Alternatives Considered**: Full output to terminal, silent mode only
**Trade-off**: Requires file reading for details, but cleaner UX

### Decision 3: Parallel Work via Git Worktree
**Choice**: One worktree per agent/feature
**Rationale**:
- Isolated working directories
- No file conflicts
- Easy merge/integration
**Alternatives Considered**: Branch-only, copy repo
**Trade-off**: More disk space, but safer parallelism

### Decision 4: Oracle/Golden Diff Strategy
**Choice**: Oracle diff with degradation fallback
**Rationale**:
- Compare against known-good output
- If oracle missing, generate fresh baseline
- Store in reports/oracle/
**Alternatives Considered**: Snapshot testing, manual comparison
**Trade-off**: Requires oracle maintenance, but catches regressions

### Decision 5: Role Separation
**Choice**: 5 distinct roles (planner, implementer, verifier, scribe, merger)
**Rationale**:
- Clear responsibility boundaries
- Enables parallel specialization
- Single-person can wear multiple hats
**Alternatives Considered**: 3 roles, 7 roles
**Trade-off**: More coordination overhead, but clearer ownership

### Decision 6: Seed Support for Reproducibility
**Choice**: SEED environment variable captured in run_meta.json
**Rationale**:
- Deterministic test runs
- Debuggable failures
- Comparable across runs
**Alternatives Considered**: Random only, fixed seed only
**Trade-off**: Requires seed management, but enables reproducibility

## Oracle Degradation Strategy
1. **Primary**: Compare against existing oracle (reports/oracle/*.expected)
2. **Fallback**: If oracle missing, generate new baseline with warning
3. **Fresh**: `make oracle-update` to regenerate all oracles
4. **CI**: Fail if oracle missing (forces explicit baseline)

## No Heavy Dependencies
- Shell scripts (bash) for runner
- Make for test orchestration
- Python optional for complex tests
- No Docker/Kubernetes required for core functionality
