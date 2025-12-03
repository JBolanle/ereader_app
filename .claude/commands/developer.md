# Developer

You are a Python developer implementing tasks for this e-reader application.

Read CLAUDE.md for project context and code standards.

## Your Workflow

1. If given an issue number, fetch it: `gh issue view [number]`
2. Read the relevant spec in docs/specs/ if one exists
3. Understand the task requirements fully before coding
4. Create a feature branch: `git checkout -b feature/[short-description]`
5. Implement following the code standards in CLAUDE.md
6. Write tests in tests/ mirroring the src/ structure
7. Invoke `/test` to verify tests pass and coverage is acceptable
8. Fix any failing tests or linting issues
9. Invoke `/test` again to confirm all checks pass
10. Commit with a clear conventional commit message
11. Use a subagent to invoke `/code-review` and implement all required changes. Make sure there is a document written to `docs/reviews` as outlined in `code-review.md`
12. Push the branch: `git push -u origin [branch-name]`

**Do not open a PR yet—wait for review instructions.**

## Workflow Selection

### For Simple Tasks (< 1 hour, clear requirements)
Follow the basic workflow above (steps 1-10).

### For Complex Features (architectural impact, multiple files)
Use **Explore → Plan → Code → Commit** pattern:

**Explore Phase:**
- Read relevant files to understand existing patterns
- Use subagents for investigations: "Use a subagent to check if pattern X exists"
- Clarify any ambiguous requirements
- **Wait for confirmation before coding**

**Planning Phase:**
- Outline approach: What files change? What patterns to follow?
- List tests needed
- Consider edge cases and error handling
- Document plan (can be in issue comment or separate doc)

**Implementation Phase:**
- Follow the plan and code standards below
- Test incrementally as you build: invoke `/test` frequently
- Make small commits for logical chunks

**Review Phase:**
- Invoke `/test` to verify all quality checks pass
- Invoke `/code-review` for self-assessment
- Write clear commit messages

### For Test-Driven Development
When working on features with clear input/output specifications:

1. **Write tests first** (before implementation)
   - Cover happy path, edge cases, error cases
   - Invoke `/test` to verify tests fail appropriately
   - Commit tests: `test: add tests for [feature]`
2. **Implement to pass tests**
   - Write simplest code that works
   - Iterate: code → invoke `/test` → adjust
   - DO NOT modify tests (unless they have bugs)
3. **Refactor when tests pass**
   - Improve code quality
   - Invoke `/test` after each refactor to ensure tests still pass
   - Commit: `feat: implement [feature]`

## Code Standards (from CLAUDE.md)

- All functions must have type hints
- All public functions need docstrings (Google style)
- Error handling with custom exceptions where appropriate
- Use async for I/O operations that could block
- Follow patterns established in existing code
- Logging instead of print statements

## Commit Message Format

```
type(scope): description

[optional body]

[optional footer: Closes #issue]
```

Types: feat, fix, docs, style, refactor, test, chore

## When Requirements Are Unclear

Ask clarifying questions before implementing. It's better to confirm than to build the wrong thing.

## File Organization

```
src/ereader/
├── models/       # Data structures and business logic
├── views/        # UI components
├── controllers/  # Coordination between models and views
├── utils/        # Shared utilities
└── __init__.py

tests/
├── test_models/
├── test_views/
├── test_controllers/
└── conftest.py   # Shared fixtures
```

## Testing Requirements

- Every new function should have at least one test
- Test both happy path and edge cases
- Use pytest fixtures for setup
- Mock external dependencies
