# Commit

Help me create a well-structured commit following our project standards.

Read CLAUDE.md for project context and Repository Etiquette.

## Before You Start

**CRITICAL - Pre-commit checklist:**
- [ ] Run `/test` to verify all tests pass, coverage meets threshold (80%+), and linting passes
- [ ] Changes are logically one commit (atomic)
- [ ] No debug code, print statements, or personal notes included

## Your Workflow

1. **Check what's staged**
   ```bash
   git status
   git diff --cached
   ```

2. **Verify quality standards (from CLAUDE.md)**
   - All functions have type hints?
   - All public functions have docstrings?
   - Using custom exceptions (not bare except)?
   - Using logging (not print statements)?
   - Following existing code patterns?

3. **Analyze the changes**
   - What type of change is this? (feat, fix, refactor, docs, test, chore)
   - What's the scope? (which component/module)
   - What's a clear, concise summary?
   - Is this ONE logical change or should it be split?

4. **Suggest a commit message**
   
   Follow conventional commits format from CLAUDE.md:
   ```
   type(scope): brief description (imperative mood, <72 chars)
   
   [optional body: explain WHAT and WHY, not HOW]
   
   [optional footer: Closes #123, Breaking changes, etc.]
   ```

5. **Ask for confirmation before committing**

## Commit Types (from CLAUDE.md)

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code change that neither fixes bug nor adds feature
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, tooling, etc.

## Good Commit Message Examples (from CLAUDE.md)

```
feat(epub): add metadata extraction from content.opf

Extracts title, author, and publisher from EPUB package document.
Uses ElementTree to parse OPF XML structure.

Closes #15
```

```
fix(ui): prevent crash when book has no cover

Add defensive check for missing cover image in EPUB.
Display placeholder icon instead of crashing.

Closes #23
```

```
test(models): add edge cases for empty chapters

Cover scenarios where EPUB has empty chapter files.
Ensures graceful handling without exceptions.
```

```
refactor(models): extract common book interface to Protocol

Prepares for adding PDF support by defining shared interface.
No functional changes to EPUB implementation.
```

## Bad Commit Messages (Avoid)

- "Fixed stuff" ❌ (not specific)
- "WIP" ❌ (shouldn't commit WIP to shared branches)
- "asdfasdf" ❌ (meaningless)
- "Updates" ❌ (too vague)
- "Changed some code" ❌ (what code? why?)
- Missing type/scope ❌ (feat, fix, etc.)

## Atomic Commits (from CLAUDE.md)

**One commit = One logical change**

Good atomic commits:
- Can be described in a single sentence
- Can be reverted cleanly if needed
- Pass all tests independently
- Affect related files/functionality

If changes aren't atomic:
```bash
git reset HEAD      # Unstage everything
git add -p          # Interactively stage related changes
git commit          # Commit first logical change
# Repeat for other changes
```

## When Changes Should Be Split

Ask yourself:
- Could I describe this commit in ONE sentence?
- If I revert this commit, would it make sense?
- Are there multiple unrelated fixes/features?
- Do changes affect different components?

If answer is "multiple things", split into separate commits.

## Special Cases

### Bug Fixes
Should include:
- What was broken
- How it's fixed
- How to test the fix

### Breaking Changes
Must include in footer:
```
BREAKING CHANGE: description of what breaks and how to migrate
```

### Closing Issues
Always link related issues:
```
Closes #123
Refs #456
```

## Quality Checklist

Before committing, verify:
- [ ] `/test` passes (tests + coverage 80%+ + linting)
- [ ] Type hints on all new functions
- [ ] Docstrings on all new public functions
- [ ] No print() statements (use logging)
- [ ] No bare except: clauses
- [ ] Changes are atomic and focused
- [ ] Commit message follows conventional format
- [ ] Related issues are referenced

## Remember

Per CLAUDE.md Repository Etiquette:
- Keep commits atomic and focused
- One logical change per commit when possible
- Squash and merge for feature branches (cleaner history)
- Address code review comments in separate commits

Quality commits make code review easier and git history more useful!
