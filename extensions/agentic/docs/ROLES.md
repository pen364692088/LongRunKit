# ROLES.md - Agent Role Definitions

## Overview

Agentic Engineering defines 5 specialized roles for complex task execution. Each role has clear responsibilities, inputs, and outputs.

## Role Summary

| Role | Focus | Key Output |
|------|-------|------------|
| Planner | Design & Breakdown | Plan, TODO, Decisions |
| Implementer | Code & Build | Working Code, Tests |
| Verifier | Quality & Validation | Test Results, Audit |
| Scribe | Documentation | Docs, Handoffs |
| Merger | Integration | Merged Code, Release |

---

## Planner

### Purpose
Break down complex tasks into executable plans with clear acceptance criteria.

### Responsibilities
- Analyze requirements and constraints
- Decompose into atomic tasks
- Define acceptance criteria for each task
- Identify dependencies and risks
- Create and maintain docs/TODO.md

### Inputs
- Requirements document or user request
- Current docs/STATUS.md
- Historical context from memory/

### Outputs
- docs/TODO.md (updated with tasks)
- Design documents (if needed)
- Risk assessment
- Acceptance criteria

### When to Use
- New feature design
- Bug investigation
- Architecture decisions
- Breaking down large tasks

### Anti-Patterns
- ❌ Skipping acceptance criteria
- ❌ Vague task descriptions
- ❌ Not checking existing patterns

---

## Implementer

### Purpose
Execute tasks and produce working code.

### Responsibilities
- Write code following design
- Create/update tests
- Run smoke and fast tests locally
- Update docs/STATUS.md with progress
- Flag blockers immediately

### Inputs
- Task from docs/TODO.md
- Design from Planner
- Existing codebase

### Outputs
- Working code in src/
- Tests in tests/
- Updated docs/STATUS.md
- Git commits with clear messages

### When to Use
- Implementing a task from TODO
- Fixing a bug
- Adding a feature
- Refactoring

### Anti-Patterns
- ❌ Writing code without tests
- ❌ Skipping smoke tests
- ❌ Large, unfocused commits
- ❌ Not updating STATUS.md

---

## Verifier

### Purpose
Ensure quality through testing and auditing.

### Responsibilities
- Run all test levels (smoke, fast, full)
- Verify acceptance criteria
- Check code quality and patterns
- Run oracle diff checks
- Document test results

### Inputs
- Code from Implementer
- Acceptance criteria from Planner
- Test suite

### Outputs
- Test results in reports/
- Audit findings
- Pass/fail determination
- Bug reports (if found)

### When to Use
- After implementation
- Before merge
- Regression testing
- Quality audits

### Anti-Patterns
- ❌ Skipping full tests
- ❌ Ignoring failing tests
- ❌ Not documenting results

---

## Scribe

### Purpose
Document decisions, processes, and handoffs.

### Responsibilities
- Update docs/ (STATUS, DECISIONS, HANDOFF)
- Create session summaries
- Document decisions and rationale
- Maintain memory/ files
- Create user-facing documentation

### Inputs
- Work from other roles
- Decisions made
- Session notes

### Outputs
- Updated docs/STATUS.md
- Updated docs/DECISIONS.md
- docs/HANDOFF.md (when needed)
- memory/ daily logs
- User documentation

### When to Use
- After completing tasks
- When decisions are made
- Session wrap-up
- Knowledge transfer

### Anti-Patterns
- ❌ Not recording decisions
- ❌ Outdated STATUS.md
- ❌ Missing handoff notes

---

## Merger

### Purpose
Integrate work from multiple agents into cohesive release.

### Responsibilities
- Review all branches/PRs
- Run full test suite
- Resolve merge conflicts
- Ensure all acceptance criteria met
- Create release notes

### Inputs
- Completed work from all roles
- Test results from Verifier
- Documentation from Scribe

### Outputs
- Merged code in main
- Release notes
- Final reports/completion.json
- Tagged release

### When to Use
- After all tasks complete
- Before release
- Integration testing

### Anti-Patterns
- ❌ Merging without full tests
- ❌ Ignoring test failures
- ❌ Not updating changelog

---

## Role Coordination

### Typical Flow

```
Planner → Implementer → Verifier → Scribe → Merger
   ↓          ↓            ↓         ↓         ↓
 TODO.md    Code        Tests     Docs     Release
```

### Parallel Work

Roles can work in parallel using worktrees:
- Planner + Scribe: Design + Document concurrently
- Multiple Implementers: Different features
- Verifier + Scribe: Test + Document

### Handoff Protocol

1. Update docs/STATUS.md
2. Fill docs/HANDOFF.md if needed
3. Run smoke tests
4. Notify next role

## Single-Actor Mode

One person can wear multiple hats:
- Planner → Implementer: Self-assign from TODO
- Implementer → Verifier: Self-test
- Verifier → Scribe: Self-document
- All → Merger: Self-merge

Just update STATUS.md to indicate current role.
