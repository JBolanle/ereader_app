# Commit

Help me create a well-structured commit.

## Your Workflow

1. **Check what's staged**
   ```bash
   git status
   git diff --cached
   ```

2. **Analyze the changes**
   - What type of change is this? (feat, fix, refactor, docs, test, chore)
   - What's the scope? (which component/module)
   - What's a clear, concise summary?

3. **Suggest a commit message**
   
   Follow conventional commits format:
   ```
   type(scope): short description (imperative mood, <50 chars)
   
   [optional body: explain WHAT and WHY, not HOW]
   
   [optional footer: Closes #issue, Breaking changes, etc.]
   ```

4. **Ask for confirmation before committing**

## Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code change that neither fixes nor adds
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, etc.

## Good Commit Message Examples

```
feat(epub): add chapter navigation

Implement next/previous chapter methods in EPUBBook model.
Navigation wraps around at book boundaries.

Closes #12
```

```
fix(ui): prevent crash on corrupted EPUB files

Add try/except around EPUB parsing with user-friendly error dialog.
```

```
refactor(models): extract common book interface to Protocol

Prepares for adding PDF support by defining shared interface.
```

## Bad Commit Messages (Avoid)

- "Fixed stuff"
- "WIP"
- "asdfasdf"
- "Updates"
- "Changed some code"

## Before Committing, Check

- Are these changes logically one commit, or should they be split?
- Is anything staged that shouldn't be? (debug code, personal notes)
- Have tests been run?

## If Changes Should Be Split

Guide me through:
```bash
git reset HEAD  # Unstage everything
git add -p      # Interactively stage hunks
```

Then commit in logical pieces.
