# Branch

Help me create a new branch for a task.

## Your Workflow

1. **Ensure we're starting from a clean state**
   ```bash
   git status
   ```
   
   If there are uncommitted changes, ask what to do:
   - Commit them first?
   - Stash them?
   - Discard them?

2. **Make sure main is up to date**
   ```bash
   git checkout main
   git pull origin main
   ```

3. **Create the branch**
   
   Ask what I'm working on, then suggest a branch name following conventions.

## Branch Naming Conventions

```
type/short-description
```

**Types:**
- `feature/` — New functionality
- `fix/` — Bug fixes
- `refactor/` — Code restructuring
- `docs/` — Documentation
- `test/` — Test additions/changes
- `spike/` — Experimental exploration (may be discarded)
- `chore/` — Build, dependencies, config

**Examples:**
- `feature/epub-parsing`
- `fix/page-navigation-crash`
- `refactor/extract-book-protocol`
- `spike/evaluate-pyqt`
- `docs/api-documentation`

## Rules

- Use lowercase
- Use hyphens, not underscores or spaces
- Keep it short but descriptive
- Include issue number if applicable: `feature/12-epub-parsing`

## Creating the Branch

```bash
git checkout -b [branch-name]
```

## After Creating

Confirm the branch was created:
```bash
git branch --show-current
```

Remind me what I'm about to work on and suggest next steps.

## Working on an Issue Directly

If starting work from a GitHub issue, use gh to create and link:

```bash
# View available issues
gh issue list

# Create branch linked to an issue (auto-names branch)
gh issue develop [issue-number] --checkout

# Or create with custom branch name
gh issue develop [issue-number] --name feature/my-branch --checkout
```

This automatically links the branch to the issue on GitHub.

## If I Want to Work on an Existing Branch

```bash
git checkout [branch-name]
git pull origin [branch-name]  # if it exists remotely
```

## View Remote Branches

```bash
gh repo view --web  # Open repo in browser
git branch -r       # List remote branches
```
