# PR (Pull Request)

Help me open a well-documented pull request using GitHub CLI.

## Pre-PR Checklist

**From CLAUDE.md - Pull Request Requirements:**

Before requesting review:
- [ ] `/test` passes (all tests + coverage 80%+ + linting)
- [ ] `/code-review` completed and issues addressed
- [ ] Changes are documented (docstrings, comments)
- [ ] Breaking changes noted in PR description
- [ ] Related issue linked (Closes #123)

**Verify with:**

```bash
# Are we on a feature branch (not main)?
git branch --show-current

# Is everything committed?
git status

# Run quality checks (or use /test command)
/test

# Push the branch if not already pushed
git push -u origin $(git branch --show-current)
```

If any checks fail, help me fix them first.

## Gather Information

```bash
# What commits are we including?
git log main..HEAD --oneline

# What files changed?
git diff main --stat

# Check for related issues
gh issue list
```

## Find Related Items

- Is there a spec in `docs/specs/` for this feature?
- Are there related GitHub issues to close?
- Is there a review in `docs/reviews/` to reference?

## Create the PR

### Interactive Mode (Recommended for Learning)

```bash
gh pr create
```

This will prompt for:
- Title
- Body
- Base branch (usually main)

### With Flags

```bash
gh pr create \
  --title "feat(scope): description" \
  --body "PR description here" \
  --assignee @me
```

### Linking to Issues

```bash
# Close an issue when PR merges
gh pr create --title "feat: add bookmarks" --body "Closes #12"

# Or link without closing
gh pr create --title "feat: add bookmarks" --body "Related to #12"
```

## PR Title Format

Same as commit messages: `type(scope): description`

Examples:
- `feat(epub): Add EPUB file parsing and chapter navigation`
- `fix(ui): Prevent crash when opening corrupted files`

## PR Description Template

When prompted for body, use this structure:

```markdown
## Summary
[2-3 sentences: what does this PR do and why?]

## Changes
- [Bullet list of main changes]

## Related Issues
Closes #[issue number]

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing performed

## Quality Checklist (from CLAUDE.md)
- [ ] `/test` passes (tests + coverage 80%+ + linting)
- [ ] `/code-review` completed with no blocking issues
- [ ] Type hints on all new functions
- [ ] Docstrings on all new public functions
- [ ] No print() statements (using logging)
- [ ] No bare except: clauses
- [ ] Changes are atomic and focused

## Notes for Reviewers
[Anything specific to look at?]
```

## After Creating

```bash
# View your PR in browser
gh pr view --web

# Check PR status
gh pr status

# List checks/CI status
gh pr checks
```

## Managing PRs

```bash
# List your open PRs
gh pr list --author @me

# View a specific PR
gh pr view [number]

# Add reviewers
gh pr edit --add-reviewer username

# Mark as ready for review (if draft)
gh pr ready

# Merge when approved
gh pr merge
```

## Updating a PR

If you need to make changes after opening:

```bash
# Make your changes, commit
git add .
git commit -m "fix: address review feedback"

# Push updates (PR updates automatically)
git push
```

## Draft PRs

If not ready for review yet:

```bash
gh pr create --draft
```

Convert to ready later:
```bash
gh pr ready
```
