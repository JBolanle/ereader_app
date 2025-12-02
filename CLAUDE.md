# E-Reader Application

A comprehensive e-reader application in Python, built for learning modern Python development practices while creating production-quality software.

## Project Overview

This project serves dual purposes:
1. **Learning**: Master modern Python development, testing, and architecture
2. **Practical**: Build a working e-reader I can actually use

## Quick Command Reference

### Running Tests & Quality Checks
- Run all tests: `uv run pytest`
- Run specific test: `uv run pytest tests/test_models/test_book.py`
- Run with coverage: `uv run pytest --cov=src/ereader`
- Run linter: `uv run ruff check src/`
- Auto-fix linting: `uv run ruff check --fix src/`
- Type checking: `uv run mypy src/` (when enabled)

### Package Management
- Add dependency: `uv add package-name`
- Add dev dependency: `uv add --dev package-name`
- Update dependencies: `uv sync`
- Run Python script: `uv run python script.py`
- Run module: `uv run python -m ereader`

### Git Operations (via gh CLI when possible)
- View issue: `gh issue view [number]`
- Create issue: `gh issue create`
- View PR: `gh pr view`
- Create PR: `gh pr create`
- Check status: `gh pr status`

### Development Environment
- Python: 3.11+ required
- Package manager: `uv` (NEVER use pip directly)
- Test framework: pytest
- Linter: ruff
- Type checker: mypy (optional, to be added later)

## Prerequisites

Before starting, ensure you have:
- **Python 3.11+**: `python --version`
- **uv**: Install from https://github.com/astral-sh/uv
- **git**: `git --version`
- **GitHub CLI**: `gh --version` (install from https://cli.github.com)
  - Authenticate with: `gh auth login`

## Tech Stack

- **Package Manager**: uv (required for all dependency operations)
- **Version Control**: git + GitHub CLI (`gh`) for GitHub integration
- **UI Framework**: TBD (evaluate tkinter, PyQt6, or textual first)
- **Python Version**: 3.11+
- **Testing**: pytest with async support
- **Linting**: ruff
- **Type Checking**: mypy (optional, introduce later)

## Important Constraints

CRITICAL - These rules are non-negotiable for code quality:

**Type Safety:**
- ALWAYS add type hints to function signatures (parameters and return types)
- Use `from typing import ...` for complex types
- Type hints are not optional—they're required

**Error Handling:**
- NEVER use bare `except:` clauses
- ALWAYS use custom exceptions from `src/ereader/exceptions.py`
- Log errors with context before raising
- Handle exceptions at appropriate levels (don't catch too early)

**Testing:**
- EVERY new function must have at least one test
- Tests go in `tests/` mirroring the `src/` structure
- Run tests before committing: `uv run pytest`
- Test both happy path and edge cases

**Code Style:**
- NEVER use `print()` — use logging instead
- ALWAYS run `uv run ruff check src/` before committing
- Follow existing patterns in the codebase
- Use Google-style docstrings for all public functions
- Keep functions focused and small (< 50 lines typically)

**Async Usage:**
- Use async/await for I/O operations that could block UI
- Don't overuse async for CPU-bound operations
- Follow asyncio best practices (no blocking calls in async functions)

## Architecture Principles

- **Pattern**: Model-View-Controller (MVC)
- **Abstractions**: Protocol-based interfaces for extensibility
- **Async**: Use for I/O operations that could block the UI
- **Caching**: Lazy loading and LRU caching for performance
- **Simplicity**: Don't over-engineer; refactor when patterns emerge

## Code Standards

- Type hints on all functions and methods
- Docstrings following Google style on all public functions
- PEP 8 compliance (enforced via ruff)
- Comprehensive error handling with custom exceptions
- Logging instead of print statements
- Conventional commits for git messages

## Repository Etiquette

### Branch Naming
- Feature work: `feature/short-description` (e.g., `feature/epub-metadata`)
- Bug fixes: `fix/short-description` (e.g., `fix/memory-leak`)
- Refactoring: `refactor/short-description`
- Documentation: `docs/short-description`

### Commit Messages
Use conventional commits format:
```
type(scope): brief description

[optional body with more details]

[optional footer: Closes #123]
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Good examples:**
- `feat(epub): add metadata extraction from content.opf`
- `fix(ui): prevent crash when book has no cover`
- `test(models): add edge cases for empty chapters`

### Merge Strategy
- Squash and merge for feature branches (cleaner history)
- Keep commits atomic and focused
- One logical change per commit when possible

### Pull Request Requirements
Before requesting review:
- [ ] All tests pass (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check src/`)
- [ ] Changes are documented (docstrings, comments)
- [ ] Breaking changes noted in PR description
- [ ] Related issue linked (Closes #123)

### Code Review Process
- Use `/code-review` for self-review before creating PR
- Address all review comments or explain why not
- Keep PRs focused and reasonably sized
- Update PR description if scope changes

## Target Features (Priority Order)

### Core (MVP)
1. [ ] Open and render EPUB files
2. [ ] Page/chapter navigation
3. [ ] Reading progress tracking
4. [ ] Basic reading themes (light/dark)

### Important
5. [ ] PDF support
6. [ ] Bookmarks
7. [ ] Annotations/highlights
8. [ ] Library management (organize books)

### Nice-to-Have
9. [ ] TXT support
10. [ ] Search within book
11. [ ] Customizable fonts and sizing
12. [ ] Reading statistics

### Future
13. [ ] MOBI support
14. [ ] Cloud sync
15. [ ] Plugin architecture

## Performance Requirements

- Page renders in <100ms
- Memory usage <200MB for typical books
- Smooth scrolling and transitions
- Background page pre-fetching
- Cached page limit: 50 pages

## Development Philosophy

- **Make it work, make it right, make it fast** (in that order)
- **YAGNI**: Don't build features or abstractions until needed
- **First implementation**: Simplest thing that works
- **Refactor**: When patterns emerge, not before

## Development Workflow Patterns

### Pattern 1: Explore → Plan → Code → Commit
**Use for:** Non-trivial features, new components, complex refactoring

1. **Explore (understand first)**
   - Read relevant existing code and understand patterns
   - Check specs in `docs/specs/` if they exist
   - Use subagents for focused investigations: "Use a subagent to investigate how we currently handle X"
   - Ask clarifying questions before proceeding
   - **DO NOT write code yet**

2. **Plan (design the approach)**
   - Create a written plan outlining the approach
   - Consider: What files change? What tests are needed? What patterns to follow?
   - For architectural decisions, document in `docs/architecture/`
   - Review plan before implementation

3. **Code (implement the solution)**
   - Implement following the plan and code standards
   - Run tests frequently during development
   - Commit related changes together

4. **Review & Commit (ensure quality)**
   - Run full test suite and linting
   - Self-review with `/code-review`
   - Write clear conventional commit message
   - Push and create PR when ready

### Pattern 2: Test-Driven Development (TDD)
**Use for:** Clear input/output specifications, bug fixes, core algorithms

1. **Write failing tests first**
   - Write tests for functionality that doesn't exist yet
   - Cover happy path, edge cases, and error conditions
   - Run tests to confirm they fail appropriately
   - Commit tests: `test: add tests for [feature]`

2. **Implement to pass tests**
   - Write simplest code that makes tests pass
   - Run tests after each small change
   - Iterate until all tests pass
   - DO NOT modify tests unless they have bugs

3. **Refactor with safety**
   - Improve code quality while keeping tests green
   - Run tests after each refactor
   - Commit: `feat: implement [feature]`

### Pattern 3: Visual Iteration (UI/UX work)
**Use for:** UI components, layouts, visual features

1. Implement visual feature in code
2. Capture screenshot or observe result
3. Compare against design mock or existing patterns
4. Make incremental adjustments
5. Repeat until result matches expectations
6. Keep iterations small and focused

### Using Subagents Effectively
Subagents preserve main context while investigating specific questions:
- "Use a subagent to investigate how EPUB spine ordering works in our current code"
- "Use a subagent to check if we already have a caching pattern for page rendering"
- Best used early in tasks to verify assumptions
- Keeps main context focused on implementation

### Iterative Improvement
For complex implementations:
1. Get something working first (even if imperfect)
2. Test and identify specific improvements needed
3. Make one targeted improvement at a time
4. Verify each improvement helps
5. Repeat until quality standards met
6. Remember: "First version good, 2-3 iterations much better"

## Development Workflow

1. All work happens on feature branches (`/branch`)
2. Issues track all tasks — use `gh issue` to manage (`/issues`)
3. Code review before merging (use `/code-review`)
4. PRs created via `gh pr create` (`/pr`)
5. Use conventional commits (`/commit`)

## Learning Goals

- [ ] Understand async/await deeply (not just copy patterns)
- [ ] Be able to write PyQt/UI code from scratch
- [x] Understand EPUB format well enough to explain it (structure understood)
- [ ] Learn proper Python packaging for distribution
- [ ] Master pytest and testing patterns
- [x] Professional Git/GitHub workflow (branching, PRs, code review, merging)

## Off-Limits for Delegation

These things I must implement myself (for learning):
- Core book parsing logic
- Main UI controller
- Any "interesting" algorithms
- First implementation of each major component

## Current Sprint

- [x] Project initialization
- [ ] UI framework decision (deferred - learning parsing first)
- [x] EPUB parsing learning (COMPLETED)
  - [x] Understand EPUB structure (ZIP-based format)
  - [x] ZIP file handling with Python's zipfile module
  - [x] Basic XML parsing with ElementTree
  - [x] Navigate from container.xml to content.opf
  - [x] Extract metadata from content.opf (title, author, language)
  - [x] Extract manifest (list of all files)
  - [x] Extract spine (reading order)
  - [x] Read actual chapter content
- [x] Core architecture setup (COMPLETED - Issue #1)
  - [x] Exception module created
  - [x] Test structure established
  - [x] Architecture documented
- [ ] Remaining EPUB tasks
  - [ ] Error handling improvements (Issue #6)
  - [ ] Integration testing with real EPUBs (Issue #7)
- [ ] EPUB rendering MVP

## Decisions Log

Record architectural decisions here as they're made:

| Date | Decision | Reasoning | Doc Link |
|------|----------|-----------|----------|
| 2025-12-01 | XML Parser: ElementTree | Standard library, sufficient for EPUBs, better for learning fundamentals | - |
| 2025-12-01 | Learning approach: Parse before UI | Understand EPUB format deeply before building interface | - |
| 2025-12-01 | Exception organization: Centralized | Single exceptions.py file prevents circular imports, follows Python patterns | docs/architecture/project-structure.md |
| 2025-12-01 | Test structure: Mirror source | tests/test_models/ mirrors src/ereader/models/ for discoverability | docs/architecture/project-structure.md |
| 2025-12-01 | Namespace fallback pattern | EPUBs use either `dc` or `dcterms` for metadata; fallback ensures compatibility | - |
| 2025-12-02 | Encoding fallback: UTF-8 → latin-1 | Try UTF-8 first (modern standard), fall back to latin-1 (never fails) for older EPUBs | - |
| TBD | UI framework | TBD | TBD |

## File Structure

```
ereader-app/
├── .claude/commands/    # Claude Code custom commands
├── docs/
│   ├── specs/           # Feature specifications
│   ├── architecture/    # Architecture decisions
│   ├── reviews/         # Code review notes
│   └── sessions/        # Session logs for continuity
├── src/ereader/
│   ├── models/          # Data structures, business logic
│   ├── views/           # UI components
│   ├── controllers/     # Coordination layer
│   ├── utils/           # Shared utilities
│   └── __init__.py
├── tests/
│   ├── test_models/
│   ├── test_views/
│   ├── test_controllers/
│   └── conftest.py
├── CLAUDE.md            # This file
├── pyproject.toml
└── README.md
```

## Command Reference

### Learning & Teaching
| Command | Purpose |
|---------|---------|
| `/mentor` | Teach concepts while building; get explanations before code |
| `/study` | Deep dive into a specific topic |
| `/quiz` | Test understanding of concepts |
| `/hint` | Get small nudge when stuck (not full solution) |

### Development Workflows
| Command | Purpose |
|---------|---------|
| `/developer` | Implement features with full workflow (issue → code → test → commit) |
| `/sprint` | Run complete feature cycle (plan → implement → review → PR) |
| `/debug` | Debug with teaching approach (help me find the issue) |

### Planning & Architecture
| Command | Purpose |
|---------|---------|
| `/architect` | Make architectural decisions; design component interfaces |
| `/pm` | Product management; prioritize features and plan work |

### Code Quality
| Command | Purpose |
|---------|---------|
| `/code-review` | Review code quality before committing or creating PR |

### Version Control (Git)
| Command | Purpose |
|---------|---------|
| `/branch` | Create new feature branch with proper naming |
| `/commit` | Create commit with conventional commit message |
| `/diff` | Review current changes |
| `/log` | Explore git history |
| `/stash` | Temporarily save uncommitted work |
| `/undo` | Fix git mistakes (wrong commit, wrong branch, etc.) |

### GitHub Integration
| Command | Purpose |
|---------|---------|
| `/gh-status` | Check current git and GitHub status |
| `/pr` | Create pull request with description |
| `/sync` | Sync with remote, handle merges |
| `/issues` | Manage GitHub issues (create, view, update) |
| `/repo` | Repository-level operations |

### Session Management
| Command | Purpose |
|---------|---------|
| `/wrapup` | End of session summary; what was accomplished |

**Tip:** Type `/` in Claude Code to see all available commands with tab-completion.

## Other Notes
- [IMPORTANT] Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP
tools to resolve library id and get library docs without me having to explicitly ask.