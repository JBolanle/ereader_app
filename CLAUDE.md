# E-Reader Application

A comprehensive e-reader application in Python, built for learning modern Python development practices while creating production-quality software.

## Project Overview

This project serves dual purposes:
1. **Learning**: Master modern Python development, testing, and architecture
2. **Practical**: Build a working e-reader I can actually use

## Tech Stack

- **Package Manager**: uv (required for all dependency operations)
- **UI Framework**: TBD (evaluate tkinter, PyQt6, or textual first)
- **Python Version**: 3.11+
- **Testing**: pytest with async support
- **Linting**: ruff
- **Type Checking**: mypy (optional, introduce later)

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

## Development Workflow

1. All work happens on feature branches
2. Issues track all tasks
3. Code review before merging (use /reviewer)
4. Use conventional commits

## Learning Goals

- [ ] Understand async/await deeply (not just copy patterns)
- [ ] Be able to write PyQt/UI code from scratch
- [ ] Understand EPUB format well enough to explain it
- [ ] Learn proper Python packaging for distribution
- [ ] Master pytest and testing patterns

## Off-Limits for Delegation

These things I must implement myself (for learning):
- Core book parsing logic
- Main UI controller
- Any "interesting" algorithms
- First implementation of each major component

## Current Sprint

- [x] Project initialization
- [ ] UI framework decision (deferred - learning parsing first)
- [x] Started EPUB parsing learning
  - [x] Understand EPUB structure (ZIP-based format)
  - [x] ZIP file handling with Python's zipfile module
  - [x] Basic XML parsing with ElementTree
  - [x] Navigate from container.xml to content.opf
  - [ ] Extract metadata from content.opf
  - [ ] Extract spine (reading order)
  - [ ] Read actual chapter content
- [ ] Core architecture setup
- [ ] EPUB rendering MVP

## Decisions Log

Record architectural decisions here as they're made:

| Date | Decision | Reasoning | Doc Link |
|------|----------|-----------|----------|
| 2025-12-01 | XML Parser: ElementTree | Standard library, sufficient for EPUBs, better for learning fundamentals | - |
| 2025-12-01 | Learning approach: Parse before UI | Understand EPUB format deeply before building interface | - |
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

## Quick Reference: Commands

### Development Workflow

| Situation | Command |
|-----------|---------|
| What should I build next? | `/pm` |
| How should this be architected? | `/architect` |
| Explain this concept to me | `/mentor` or `/study` |
| I'm stuck, small nudge please | `/hint` |
| Help me debug (teach, don't fix) | `/debug` |
| Do this for me (boilerplate) | `/developer` |
| Is my code good? | `/reviewer` |
| Test my understanding | `/quiz` |
| End of session summary | `/wrapup` |
| Run a full feature cycle | `/sprint` |

### Git Operations

| Situation | Command |
|-----------|---------|
| Start new work | `/branch` |
| Where am I? What's my state? | `/status` |
| Save my work with good message | `/commit` |
| What changed? | `/diff` |
| Explore history | `/log` |
| Open a pull request | `/pr` |
| Sync with remote / handle merges | `/sync` |
| Temporarily save work | `/stash` |
| Fix a git mistake | `/undo` |

## Other Notes
- IMPORTANT: Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP
tools to resolve library id and get library docs without me having to explicitly ask.