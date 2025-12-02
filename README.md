# E-Reader

A Python-based e-reader application supporting EPUB, PDF, and other formats.

## Status

🚧 **Under Development** 🚧

This project is being built as a learning exercise in modern Python development.

## Features (Planned)

- [ ] EPUB support
- [ ] PDF support
- [ ] Reading progress tracking
- [ ] Bookmarks and annotations
- [ ] Customizable themes
- [ ] Library management

## Development Setup

This project uses [uv](https://github.com/astral-sh/uv) for package management.

```bash
# Clone the repository
git clone https://github.com/JBolanle/ereader_app.git
cd ereader-app

# Install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
```

## Project Structure

```
ereader-app/
├── src/ereader/       # Main application code
│   ├── models/        # Data structures and business logic
│   ├── views/         # UI components
│   ├── controllers/   # Coordination layer
│   └── utils/         # Shared utilities
├── tests/             # Test suite
├── docs/              # Documentation and specs
└── CLAUDE.md          # AI assistant context
```

## License

MIT
