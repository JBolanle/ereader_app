# Project Structure Architecture

## Date
2025-12-01

## Context

Issue #1 requires setting up the foundational directory structure for EPUB parsing. While the basic structure (`src/ereader/models/`, `tests/`) already exists from initial project setup, we need to make architectural decisions about:

1. **Exception organization**: Where and how to define custom exceptions
2. **Test structure**: How to mirror source code in tests
3. **Module initialization**: What goes in `__init__.py` files
4. **Import patterns**: How modules will import from each other

These decisions affect how the codebase will scale as we add more features.

## Current State

```
src/
├── ereader/
│   ├── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── views/
│   │   └── __init__.py
│   ├── controllers/
│   │   └── __init__.py
│   └── utils/
│       └── __init__.py
tests/
├── conftest.py
└── (needs test_models/ directory)
```

**Already configured:**
- pytest setup in `pyproject.toml` (testpaths, asyncio_mode, addopts)
- ruff for linting
- Package metadata and build system

## Options Considered

### Option 1: Centralized Exceptions Module
```
src/ereader/exceptions.py  # All exceptions here
```

**Pros:**
- Single source of truth for all exceptions
- Easy to find and import exceptions
- Prevents circular imports (exceptions at root level)
- Standard Python pattern (e.g., `requests.exceptions`)

**Cons:**
- Could grow large in a big application
- Less modular (all exceptions in one place)

### Option 2: Distributed Exceptions
```
src/ereader/models/exceptions.py  # Model-specific exceptions
src/ereader/views/exceptions.py   # View-specific exceptions
```

**Pros:**
- More modular and localized
- Clear ownership of exceptions

**Cons:**
- Harder to find all exceptions
- Potential for circular imports between modules
- More files to manage
- Harder to share exceptions across layers

### Option 3: Mixed Approach
```
src/ereader/exceptions.py          # Base/shared exceptions
src/ereader/models/exceptions.py   # Model-specific exceptions
```

**Pros:**
- Flexibility for both shared and specific exceptions

**Cons:**
- Ambiguity about where new exceptions should go
- More complex mental model

## Decision

**Choose Option 1: Centralized Exceptions Module**

**Rationale:**
1. **Simplicity**: For a project of this size (e-reader app), a single exceptions file is sufficient
2. **No circular imports**: Exceptions are at the root `ereader` package level, so any submodule can safely import them
3. **Standard pattern**: Follows established Python library patterns (`requests.exceptions`, `django.core.exceptions`)
4. **Easy refactoring**: If it grows too large, we can split it later without breaking public APIs
5. **Clear imports**: `from ereader.exceptions import InvalidEPUBError` is explicit and clear

**Structure:**
```python
# src/ereader/exceptions.py

class EReaderError(Exception):
    """Base exception for all ereader errors."""
    pass

class InvalidEPUBError(EReaderError):
    """Raised when a file is not a valid EPUB."""
    pass

class CorruptedEPUBError(EReaderError):
    """Raised when an EPUB file is damaged or incomplete."""
    pass

class UnsupportedEPUBError(EReaderError):
    """Raised when an EPUB format is not supported."""
    pass
```

**Benefits of base exception:**
- Users can catch all app exceptions with `except EReaderError`
- Follows Python best practices (PEP 8 recommends exception hierarchies)
- Allows for future categorization (e.g., `FileError`, `ParseError` subclasses)

## Test Directory Structure

**Decision: Mirror source structure in tests**

```
tests/
├── conftest.py           # Shared fixtures
├── test_models/
│   ├── __init__.py
│   └── test_epub.py      # Tests for models/epub.py
├── test_views/           # (future)
│   └── __init__.py
├── test_controllers/     # (future)
│   └── __init__.py
└── test_exceptions.py    # Tests for exceptions.py (if needed)
```

**Rationale:**
1. **Discoverability**: Easy to find tests for any source file
2. **Pytest convention**: Standard pattern in Python projects
3. **Scalability**: Structure grows naturally with source code
4. **Test organization**: Related tests stay together

**Import pattern in tests:**
```python
# tests/test_models/test_epub.py
from ereader.models.epub import EPUBBook
from ereader.exceptions import InvalidEPUBError
```

## Module Initialization (`__init__.py`)

**Decision: Minimal initialization, explicit imports**

**For `src/ereader/__init__.py`:**
```python
"""E-Reader application for Python."""

__version__ = "0.1.0"

# Public API exports (add as classes are implemented)
# from ereader.models.epub import EPUBBook
# from ereader.exceptions import InvalidEPUBError, CorruptedEPUBError
```

**For `src/ereader/models/__init__.py`:**
```python
"""Data models for the e-reader application."""

# Explicit exports (add as models are implemented)
# from ereader.models.epub import EPUBBook
```

**For test `__init__.py` files:**
```python
# Empty - pytest doesn't require anything
```

**Rationale:**
1. **Explicit > Implicit**: Don't use `from . import *` — it's unclear what's exported
2. **Delayed exports**: Don't export until classes are stable (avoid breaking changes)
3. **Version tracking**: Keep `__version__` in root `__init__.py`
4. **Docstrings**: Each package gets a brief description
5. **Pytest compatibility**: Empty test `__init__.py` files are fine

## Import Guidelines

To prevent circular imports and maintain clarity:

### ✅ Good Patterns
```python
# Absolute imports from package root
from ereader.exceptions import InvalidEPUBError
from ereader.models.epub import EPUBBook

# Specific imports, not wildcards
from ereader.utils.xml_helpers import parse_with_namespaces
```

### ❌ Avoid
```python
# Relative imports in library code (use in tests only)
from ..exceptions import InvalidEPUBError

# Wildcard imports
from ereader.exceptions import *

# Circular imports (e.g., models importing from controllers)
```

### Import Order (enforced by ruff)
1. Standard library imports
2. Third-party imports
3. Local application imports

## File Structure After Issue #1

```
src/ereader/
├── __init__.py              ✅ Already exists, update with version/docstring
├── exceptions.py            ⭐ CREATE - Custom exception classes
├── models/
│   ├── __init__.py          ✅ Already exists, add docstring
│   └── epub.py              ⏭️  Issue #2 - EPUBBook class
├── controllers/
│   └── __init__.py          ✅ Already exists
├── views/
│   └── __init__.py          ✅ Already exists
└── utils/
    └── __init__.py          ✅ Already exists

tests/
├── conftest.py              ✅ Already exists
├── test_models/             ⭐ CREATE directory
│   ├── __init__.py          ⭐ CREATE (empty)
│   └── test_epub.py         ⏭️  Issue #2 - Tests for EPUBBook
└── test_exceptions.py       ⏭️  Optional - Can test exceptions in test_epub.py
```

## Consequences

### What This Enables
- ✅ Clear namespace for all custom exceptions
- ✅ Consistent test organization that scales with source code
- ✅ Prevention of circular import issues
- ✅ Easy-to-understand import statements
- ✅ Foundation for adding more models without restructuring

### What This Constrains
- 📍 All exceptions must go in `exceptions.py` (unless we refactor later)
- 📍 Test files must mirror source structure
- 📍 Must use absolute imports from `ereader` package root

### What to Watch Out For
- ⚠️ If `exceptions.py` grows beyond ~200 lines, consider splitting
- ⚠️ Don't add cross-imports between models/views/controllers (maintain MVC separation)
- ⚠️ Keep `__init__.py` exports minimal until APIs stabilize

## Implementation Notes

### Issue #1 Checklist

1. **Create `src/ereader/exceptions.py`**
   - Define `EReaderError` base class
   - Define `InvalidEPUBError`, `CorruptedEPUBError`, `UnsupportedEPUBError`
   - Add docstrings for each exception
   - Follow pattern shown in "Decision" section above

2. **Update `src/ereader/__init__.py`**
   - Add version string
   - Add package docstring
   - Prepare commented-out imports for future use

3. **Update `src/ereader/models/__init__.py`**
   - Add module docstring
   - Prepare commented-out imports for future EPUBBook

4. **Create test directory structure**
   - Create `tests/test_models/` directory
   - Create `tests/test_models/__init__.py` (empty)

5. **Verify pytest still works**
   - Run `pytest` to ensure configuration is correct
   - Should pass with 0 tests collected (or existing tests if any)

### Commands for Implementation

```bash
# Create exceptions file
touch src/ereader/exceptions.py

# Create test directory structure
mkdir -p tests/test_models
touch tests/test_models/__init__.py

# Verify pytest configuration
pytest --collect-only
```

### Testing This Structure

After setup, verify with:
```bash
# Check import paths work
python -c "from ereader.exceptions import InvalidEPUBError; print('✓ Imports work')"

# Check pytest discovers test structure
pytest --collect-only

# Check ruff is happy
ruff check src/ tests/
```

## Future Considerations

### When to Refactor Exceptions
- If exceptions grow beyond 200 lines
- If we have >15 exception classes
- If clear categories emerge (e.g., all file I/O exceptions)

Consider creating:
```python
# src/ereader/exceptions/base.py
# src/ereader/exceptions/file_errors.py
# src/ereader/exceptions/parse_errors.py
```

### When to Add Test Utilities
As tests grow, consider adding:
```
tests/
├── fixtures/           # Test EPUB files, sample data
├── utils/              # Test helper functions
└── test_*/             # Actual test modules
```

### Integration with MVC Pattern
- **Models** (data/business logic) can import from `exceptions`
- **Views** (UI) should catch exceptions from models
- **Controllers** (coordination) orchestrate models and views
- Maintain one-way dependencies: Views → Controllers → Models

## References

- [PEP 8 - Programming Recommendations](https://peps.python.org/pep-0008/#programming-recommendations)
- [Real Python - Python Project Structure](https://realpython.com/python-application-layouts/)
- [pytest - Good Integration Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- CLAUDE.md - Architecture Principles section
