# E-Reader Application

A comprehensive e-reader application in Python, built for learning modern Python development practices while creating production-quality software.

## Project Overview

This project serves dual purposes:
1. **Learning**: Master modern Python development, testing, and architecture
2. **Practical**: Build a working e-reader I can actually use

**Current Status**: ✅ **MVP COMPLETE** (91% test coverage, 195 tests passing)
- See [MVP Completion Summary](docs/mvp-completion.md) for full implementation history

## Quick Command Reference

### Running Tests & Quality Checks
- **Quick test run**: `/test` (recommended - runs tests + coverage + linting)
- Run all tests: `uv run pytest`
- Run specific test: `uv run pytest tests/test_models/test_book.py`
- Run with coverage: `uv run pytest --cov=src/ereader --cov-report=term-missing`
- Run linter: `uv run ruff check src/`
- Auto-fix linting: `uv run ruff check --fix src/`

### Package Management
- Add dependency: `uv add package-name`
- Add dev dependency: `uv add --dev package-name`
- Update dependencies: `uv sync`
- Run Python script: `uv run python script.py`

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

## Tech Stack

- **Package Manager**: uv (required for all dependency operations)
- **Version Control**: git + GitHub CLI (`gh`) for GitHub integration
- **UI Framework**: PyQt6 (desktop GUI with native HTML rendering)
- **Python Version**: 3.11+
- **Testing**: pytest with pytest-qt for UI testing
- **Linting**: ruff

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
- Handle exceptions at appropriate levels

**Testing:**
- EVERY new function must have at least one test
- Tests go in `tests/` mirroring the `src/` structure
- Run `/test` frequently during development
- Test both happy path and edge cases
- Maintain minimum 80% code coverage (target: 90%+)
- Focus on meaningful coverage, not just hitting percentages

**Code Style:**
- NEVER use `print()` — use logging instead
- ALWAYS run `uv run ruff check src/` before committing
- Follow existing patterns in the codebase
- Use Google-style docstrings for all public functions
- Keep functions focused and small (< 50 lines typically)

**Async Usage:**
- Use async/await for I/O operations that could block UI
- Don't overuse async for CPU-bound operations
- Follow asyncio best practices

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

## Test Coverage Standards

Maintain professional-grade test coverage:

### Coverage Thresholds
- **Minimum**: 80% (enforced in tests)
- **Target**: 90%+ (professional standard)
- **Trend**: Coverage should never decrease without good reason

### What to Test
✅ **Always Test:** User-facing features, data integrity operations, error handling for common scenarios, public APIs, business logic

🟡 **Test When Practical:** Edge cases with moderate probability, uncommon error scenarios, internal helpers in critical paths

⚪ **Document and Defer:** Defensive logging, edge cases with very low probability, code requiring disproportionate test effort

### Professional Standard
- Coverage is a quality metric, not a goal
- Test what matters to users and system integrity
- Document why certain code isn't tested
- Monitor coverage trends (don't let it drop)
- Add tests when bugs are found (test-driven bug fixing)

## Repository Etiquette

### Branch Naming
- Feature work: `feature/short-description`
- Bug fixes: `fix/short-description`
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

### Pull Request Requirements
Before requesting review:
- [ ] `/test` passes (tests + coverage 80%+ + linting)
- [ ] Changes are documented (docstrings, comments)
- [ ] `/code-review` feedback addressed
- [ ] Breaking changes noted in PR description
- [ ] Related issue linked (Closes #123)

## Current Phase: Post-MVP Enhancements

**MVP Completed**: All core features shipped! 🎉
- EPUB rendering with chapter navigation
- Reading progress tracking
- Light/dark themes
- Image support with responsive sizing
- Keyboard navigation
- Chapter caching (memory optimized)

See [MVP Completion Summary](docs/mvp-completion.md) for full implementation details.

### Next Priority Features

**UPDATED PRIORITIES (2025-12-13):** Library Management System promoted to #1 priority based on UX evaluation. This transforms the app from a single-book viewer to a personal reading library.

**Phase 1: Library Foundation** ⭐ TOP PRIORITY
1. [ ] **Library Management System** (See [Library Spec](docs/specs/library-management-system.md))
   - Phase 1: Basic library (import, grid view, persistence)
   - Phase 2: Organization (collections, search, filters, status)
   - Phase 3: Polish (Continue Reading, covers, list view, context menus)

**Phase 2: Reading Enhancements**
2. [ ] Bookmarks feature
3. [ ] Font customization (promoted - reading comfort is core UX)
4. [ ] Search within book

**Phase 3: Content Expansion**
5. [ ] PDF support
6. [ ] Annotations/highlights

**Phase 4: Analytics & Advanced**
7. [ ] Reading statistics
8. [ ] True page-based pagination system (Issue #31)
9. [ ] TXT/MOBI support

**Future:**
10. [ ] Cloud sync
11. [ ] Plugin architecture

## Performance Requirements

- Page renders in <100ms
- Memory usage <200MB for typical books (achieved via LRU caching)
- Smooth scrolling and transitions
- Background page pre-fetching (future enhancement)

## Development Philosophy

- **Make it work, make it right, make it fast** (in that order)
- **YAGNI**: Don't build features or abstractions until needed
- **First implementation**: Simplest thing that works
- **Refactor**: When patterns emerge, not before

## Development Workflow Patterns

### Pattern 1: Explore → Plan → Code → Commit
**Use for:** Non-trivial features, new components, complex refactoring

1. **Explore** - Read relevant code, check specs, investigate with subagents
2. **Plan** - Design approach, document architecture decisions
3. **Code** - Implement following plan, run `/test` frequently
4. **Review & Commit** - Self-review with `/code-review`, commit with `/commit`

### Pattern 2: Test-Driven Development (TDD)
**Use for:** Clear input/output specifications, bug fixes, core algorithms

1. **Write failing tests first** - Cover happy path, edge cases, errors
2. **Implement to pass tests** - Simplest code that works
3. **Refactor with safety** - Improve while keeping tests green

### Pattern 3: UX-First Development (User-Facing Features)
**Use for:** UI components, user workflows, interaction patterns

1. **Design UX first** - Use `/ux` to plan layout, flows, or research conventions
2. **Plan architecture** - Use `/architect` to design technical structure
3. **Implement** - Follow both UX and architecture designs
4. **Evaluate usability** - Use `/ux evaluate` to check implementation
5. **Review and iterate** - Use `/code-review` for code quality

### Using Subagents Effectively
- "Use a subagent to investigate how EPUB spine ordering works"
- Best used early to verify assumptions
- Keeps main context focused on implementation

## Development Workflow

1. All work happens on feature branches (`/branch`)
2. Issues track all tasks — use `gh issue` to manage (`/issues`)
3. Code review before merging (use `/code-review`)
4. PRs created via `gh pr create` (`/pr`)
5. Use conventional commits (`/commit`)

## Learning Goals

**Active Focus:**
- [ ] Understand async/await deeply (not just copy patterns)
- [ ] Complete PyQt widget library mastery
- [ ] Learn proper Python packaging for distribution
- [ ] Advanced mocking patterns in pytest

**Completed:** ✅
- PyQt/UI code from scratch (signals, slots, shortcuts, responsive design)
- EPUB format structure
- Professional pytest patterns (91% coverage, pytest-qt, signal testing)
- Professional Git/GitHub workflow

## Off-Limits for Delegation

These things I must implement myself (for learning):
- Core book parsing logic
- Main UI controller
- Any "interesting" algorithms
- First implementation of each major component

## Key Architectural Decisions

Selected important decisions from MVP (see full log below for complete history):

| Date | Decision | Reasoning |
|------|----------|-----------|
| 2025-12-02 | UI framework: PyQt6 | Learning goals, native HTML rendering for EPUB, professional quality |
| 2025-12-03 | MVC with Protocol abstraction | Controller owns state, views stateless, enables implementation swapping |
| 2025-12-03 | Chapter cache: Custom LRU | Full control, memory tracking, reduced memory 559MB → 150MB |
| 2025-12-04 | pytest-qt for UI testing | Industry standard, reliable signal testing, improved coverage 0% → 88% |

<details>
<summary>Full Decisions Log (Reference)</summary>

| Date | Decision | Reasoning | Doc Link |
|------|----------|-----------|----------|
| 2025-12-01 | XML Parser: ElementTree | Standard library, sufficient for EPUBs, better for learning fundamentals | - |
| 2025-12-01 | Learning approach: Parse before UI | Understand EPUB format deeply before building interface | - |
| 2025-12-01 | Exception organization: Centralized | Single exceptions.py file prevents circular imports, follows Python patterns | docs/architecture/project-structure.md |
| 2025-12-01 | Test structure: Mirror source | tests/test_models/ mirrors src/ereader/models/ for discoverability | docs/architecture/project-structure.md |
| 2025-12-01 | Namespace fallback pattern | EPUBs use either `dc` or `dcterms` for metadata; fallback ensures compatibility | - |
| 2025-12-02 | Encoding fallback: UTF-8 → latin-1 | Try UTF-8 first (modern standard), fall back to latin-1 (never fails) for older EPUBs | - |
| 2025-12-02 | UI framework: PyQt6 | Aligns with learning goals (PyQt/UI from scratch), native HTML rendering for EPUB content, professional quality, marketable skill. Textual TUI deferred to future (Issue #16) | - |
| 2025-12-03 | Rendering widget: QTextBrowser | Lightweight, simpler to learn, sufficient HTML/CSS support for most EPUBs. Can upgrade to QWebEngineView if needed. | docs/architecture/epub-rendering-architecture.md |
| 2025-12-03 | MVC with Protocol abstraction | Controller owns state, views are stateless. Protocol interfaces enable swapping implementations (QTextBrowser → QWebEngineView). | docs/architecture/epub-rendering-architecture.md |
| 2025-12-03 | Synchronous for MVP | No async until performance testing shows need. Simpler for learning, measure first before optimizing. | docs/architecture/epub-rendering-architecture.md |
| 2025-12-03 | Image rendering: Base64 data URLs | Embed images as base64 in HTML for QTextBrowser compatibility. Simpler than QTextDocument resource API, acceptable memory trade-off (~33% larger) for MVP. Can add caching later if needed. | docs/reviews/feature-image-rendering.md |
| 2025-12-03 | Context-aware path resolution | EPUB chapter images are relative to chapter file location, not OPF. Pass chapter_href through resolution chain to handle relative paths correctly. | - |
| 2025-12-03 | Performance profiling with statistical sampling | Sample chapters evenly (e.g., 10 of 100) for balance between thoroughness and speed while getting representative results. | docs/testing/performance-summary.md |
| 2025-12-03 | LRU caching as Priority 1 optimization | Profiling revealed memory growth with images (up to 559MB). LRU cache will cap at ~150MB even for large books. | docs/testing/performance-summary.md |
| 2025-12-03 | Chapter cache: Custom LRU with OrderedDict | Use custom LRU (not functools.lru_cache or external lib) for full control, memory tracking, and debugging. Phased approach: Phase 1=basic LRU (10 chapters), Phase 2=memory monitoring, Phase 3=multi-layer caching. Expected impact: 559MB → 150MB (73% reduction). | docs/architecture/chapter-caching-system.md |
| 2025-12-03 | Phased pagination approach | Phase 1 (MVP): Virtual pagination with scroll-based navigation for quick UX improvement. Phase 2 (Post-MVP): True page-based pagination with stable page numbers and mode toggle. Prioritizes shipping MVP while planning for professional-grade enhancement. | Issue #21, Issue #31 |
| 2025-12-04 | Keyboard navigation: Virtual pagination (Phase 1) | Scroll-based navigation with 50% overlap for arrow keys provides smooth UX while shipping MVP faster. Phase 2 will add true page-based pagination. | Issue #21, Issue #31 |
| 2025-12-04 | Scroll amounts: 50% for arrows, 100% for Page keys | UX research showed 50% overlap preserves reading context while arrows feel responsive. Full page for Page keys follows standard desktop conventions. | docs/architecture/keyboard-navigation-architecture.md |
| 2025-12-04 | Signal connection order: After content load | Connect scrollbar signals after initial content to prevent spurious emissions during initialization. Improves maintainability and initialization clarity. | Code review improvement |
| 2025-12-04 | pytest-qt for UI testing | Migrate from manual Qt testing to pytest-qt for industry-standard UI testing. Benefits: reliable signal testing with qtbot.waitSignal(), automatic widget cleanup, better event loop control, eliminates race conditions. Improved views coverage from 0% to 88%. | docs/testing/pytest-qt-patterns.md |
| 2025-12-04 | Responsive images with CSS | Use CSS max-width: 100% for responsive images instead of JavaScript-based resizing. Simpler implementation, smoother performance, standard web approach works perfectly in QTextBrowser. | PR #33 |
| 2025-12-04 | Reading themes: Direct widget styling | Chose direct theme application in MainWindow over signal-based approach for MVP simplicity. Only 2-3 widgets need theming. Uses QActionGroup for menu radio buttons, QSettings for persistence, WCAG AAA colors. Can refactor to signals if complexity grows. | docs/architecture/reading-themes-architecture.md |

</details>

## File Structure

```
ereader-app/
├── .claude/commands/    # Claude Code custom commands
├── docs/
│   ├── specs/           # Feature specifications
│   ├── architecture/    # Architecture decisions
│   ├── reviews/         # Code review notes
│   ├── sessions/        # Session logs for continuity
│   ├── study/           # Learning materials and study sessions
│   ├── testing/         # Test reports and findings
│   └── mvp-completion.md # MVP implementation history (archive)
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
| `/pm` | Product management and workflow orchestration; guides you through the development lifecycle |
| `/ux` | Design user experiences (UI, workflows, interactions, error handling, research); not just visual design |

### Code Quality & Testing
| Command | Purpose |
|---------|---------|
| `/test` | Run tests with coverage analysis and linting (use frequently!) |
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
- [IMPORTANT] Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.
