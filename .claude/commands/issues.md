# Issues

Help me manage GitHub issues using the gh CLI.

## View Issues

```bash
# List open issues
gh issue list

# List issues assigned to me
gh issue list --assignee @me

# List issues with a specific label
gh issue list --label "feature"
gh issue list --label "bug"

# List all issues (including closed)
gh issue list --state all

# View a specific issue
gh issue view [number]

# View issue in browser
gh issue view [number] --web
```

## Create Issues

### Interactive (Recommended)
```bash
gh issue create
```

This prompts for title, body, labels, etc.

### With Flags
```bash
gh issue create \
  --title "Issue title" \
  --body "Description of the issue" \
  --label "feature" \
  --assignee @me
```

### From a Template
If the repo has issue templates:
```bash
gh issue create --template "bug_report.md"
```

## Issue Format

### Bug Report
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable.

**Environment**
- OS: [e.g., macOS 14.0]
- Python: [e.g., 3.11]
```

### Feature Request
```markdown
**Is this related to a problem?**
A clear description of the problem.

**Describe the solution**
What you want to happen.

**Alternatives considered**
Other solutions you've thought about.

**Additional context**
Any other information.
```

## Manage Issues

### Assign an issue
```bash
gh issue edit [number] --add-assignee @me
gh issue edit [number] --add-assignee username
```

### Add labels
```bash
gh issue edit [number] --add-label "priority:high"
gh issue edit [number] --add-label "feature","ui"
```

### Add to milestone
```bash
gh issue edit [number] --milestone "v1.0"
```

### Close an issue
```bash
gh issue close [number]

# Close with comment
gh issue close [number] --comment "Fixed in #PR-number"
```

### Reopen an issue
```bash
gh issue reopen [number]
```

## Comment on Issues

```bash
# Add a comment
gh issue comment [number] --body "Your comment here"

# Add comment interactively (opens editor)
gh issue comment [number]
```

## Link Issues to Work

### Start working on an issue
```bash
# Create a branch linked to the issue
gh issue develop [number] --checkout

# Or with custom branch name
gh issue develop [number] --name feature/my-branch --checkout
```

### Reference in commits
```bash
git commit -m "feat: add feature

Refs #12"
```

### Close via commit/PR
```bash
git commit -m "fix: resolve bug

Closes #12"
```

Or in PR description:
```markdown
Closes #12
Fixes #12
Resolves #12
```

## Search Issues

```bash
# Search by text
gh issue list --search "search term"

# Search with filters
gh issue list --search "is:open label:bug author:@me"
```

## View Issue Status in Context

```bash
# See your assigned issues alongside PR status
gh status
```

## Tips

1. **Use labels consistently**: Create a labeling system (priority, type, area)
2. **Link issues to PRs**: Makes tracking easier
3. **Close with context**: When closing, reference the PR or commit that fixed it
4. **Use milestones**: Group related issues for releases

## What Would You Like to Do?

Tell me what you need:
- Create a new issue?
- Find existing issues?
- Update an issue?
- Start working on one?
