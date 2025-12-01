# PR (Pull Request)

Help me open a well-documented pull request.

## Pre-PR Checklist

Before opening, verify:

```bash
# Are we on a feature branch (not main)?
git branch --show-current

# Is everything committed?
git status

# Do tests pass?
uv run pytest

# Does linting pass?
uv run ruff check src/
```

If any checks fail, help me fix them first.

## Gather Information

```bash
# What commits are we including?
git log main..HEAD --oneline

# What files changed?
git diff main --stat

# What's the actual diff? (for summary)
git diff main
```

## Find Related Items

- Is there a spec in `docs/specs/` for this feature?
- Are there related GitHub issues to close?
- Is there a review in `docs/reviews/` to reference?

## PR Title

Format: `type(scope): description`

Same as commit messages but can be slightly more descriptive.

Examples:
- `feat(epub): Add EPUB file parsing and chapter navigation`
- `fix(ui): Prevent crash when opening corrupted files`

## PR Description Template

```markdown
## Summary
[2-3 sentences: what does this PR do and why?]

## Changes
- [Bullet list of main changes]
- [Keep it high-level, not every file]

## Related Issues
Closes #[issue number]

## Spec
[Link to docs/specs/[feature].md if applicable]

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing performed
- [ ] All tests passing

## Screenshots
[If UI changes, add before/after screenshots]

## Notes for Reviewers
[Anything specific to look at? Concerns? Questions?]
```

## Create the PR

```bash
gh pr create --title "[title]" --body "[body]"
```

Or for interactive:
```bash
gh pr create
```

## After Creating

Provide the PR link and suggest:
- Who should review (if team project)
- Any follow-up tasks
- Update CLAUDE.md's Current Sprint if needed
