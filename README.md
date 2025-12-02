# E-Reader Application

A comprehensive e-reader application in Python, built for learning modern Python development practices while creating production-quality software.

## Status

🚧 **Under Active Development** 🚧

This project serves dual purposes:
1. **Learning**: Master modern Python development, testing, and architecture
2. **Practical**: Build a working e-reader for actual use

### Current Progress

- [x] Core architecture setup (MVC pattern, exception handling)
- [x] Test infrastructure established
- [x] EPUB format understanding (ZIP-based structure, XML parsing)
- [ ] EPUB metadata extraction (in progress)
- [ ] EPUB rendering engine
- [ ] UI framework selection (deferred - learning parsing first)

See [CLAUDE.md](CLAUDE.md) for detailed development context and current sprint.

## 📋 Prerequisites

Before you begin, ensure you have:

- 🐍 **Python 3.11+**: Check with `python --version`
- 📦 **uv**: Install from https://github.com/astral-sh/uv
- 🔧 **git**: Check with `git --version`
- 🐙 **GitHub CLI** (optional): Install from https://cli.github.com
  - Authenticate with: `gh auth login`

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/JBolanle/ereader_app.git
cd ereader_app

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
```

## 💻 Development

### For Contributors

This project follows strict development standards:

- 🏷️ **Type hints** on all functions (required, not optional)
- ✅ **Tests** for every new function
- ⚠️ **Custom exceptions** from `src/ereader/exceptions.py` (no bare `except:`)
- 📝 **Logging** instead of `print()` statements
- 📌 **Conventional commits** for all commit messages

See **[CLAUDE.md](CLAUDE.md)** for comprehensive development guidelines, code standards, and workflow patterns.

### Common Commands

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_models/test_book.py

# Run with coverage
uv run pytest --cov=src/ereader

# Lint code
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check --fix src/

# Type checking (when enabled)
uv run mypy src/
```

### Working with GitHub

```bash
# View issues
gh issue list

# View specific issue
gh issue view [number]

# Check PR status
gh pr status

# Create pull request
gh pr create
```

## 🛠️ Tech Stack

- 🐍 **Language**: Python 3.11+
- 📦 **Package Manager**: uv (required - do not use pip)
- 🏗️ **Architecture**: Model-View-Controller (MVC)
- ✅ **Testing**: pytest with async support
- 🔍 **Linting**: ruff
- 🏷️ **Type Checking**: mypy (to be added)
- 🎨 **UI Framework**: TBD (evaluating tkinter, PyQt6, or textual)

## 📁 Project Structure

```
ereader_app/
├── .claude/commands/    # Custom Claude Code commands
├── docs/
│   ├── specs/           # Feature specifications
│   ├── architecture/    # Architecture decisions and ADRs
│   ├── reviews/         # Code review notes
│   └── sessions/        # Development session logs
├── src/ereader/
│   ├── models/          # Data structures, business logic
│   ├── views/           # UI components (future)
│   ├── controllers/     # Coordination layer (future)
│   ├── utils/           # Shared utilities
│   └── exceptions.py    # Custom exception classes
├── tests/               # Test suite (mirrors src/ structure)
│   ├── test_models/
│   └── conftest.py
├── CLAUDE.md            # Development guide and AI context
├── pyproject.toml       # Project metadata and dependencies
└── README.md            # This file
```

## 🗺️ Features Roadmap

### 🎯 Core (MVP)
- [ ] Open and render EPUB files
- [ ] Page/chapter navigation
- [ ] Reading progress tracking
- [ ] Basic reading themes (light/dark)

### ⭐ Important
- [ ] PDF support
- [ ] Bookmarks
- [ ] Annotations/highlights
- [ ] Library management

### ✨ Nice-to-Have
- [ ] TXT support
- [ ] Search within book
- [ ] Customizable fonts and sizing
- [ ] Reading statistics

### 🔮 Future
- [ ] MOBI support
- [ ] Cloud sync
- [ ] Plugin architecture

## 💡 Development Philosophy

- **Make it work, make it right, make it fast** (in that order)
- **YAGNI**: Don't build features until needed
- **Test-driven when appropriate**: Clear specs → tests first
- **Refactor when patterns emerge**, not before

## 🤝 Contributing

1️⃣ Check [open issues](https://github.com/JBolanle/ereader_app/issues) or create a new one
2️⃣ Create a feature branch: `git checkout -b feature/your-feature`
3️⃣ Read [CLAUDE.md](CLAUDE.md) for code standards and workflow patterns
4️⃣ Make your changes following the code standards
5️⃣ Run tests and linting: `uv run pytest && uv run ruff check src/`
6️⃣ Commit with conventional commits: `feat: add your feature`
7️⃣ Push and create a pull request

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Main development guide (code standards, workflows, architecture)
- **[docs/architecture/](docs/architecture/)** - Architectural decisions and rationale
- **[docs/specs/](docs/specs/)** - Feature specifications and designs

## 📄 License

MIT

---

**Note**: This is an active learning project. Code quality and best practices are prioritized over rapid feature development.
