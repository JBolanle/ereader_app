# Log

Help me explore the git history.

## Quick Views

### Recent commits (simple)
```bash
git log --oneline -20
```

### Recent commits with graph (shows branches)
```bash
git log --oneline --graph --all -20
```

### Detailed recent history
```bash
git log -5
```

---

## Specific Queries

### What changed in a specific commit?
```bash
git show [commit-hash]
```

### What commits affected a specific file?
```bash
git log --oneline -- [file-path]
```

### What changed in a file over time?
```bash
git log -p -- [file-path]
```

### Who changed each line of a file? (blame)
```bash
git blame [file-path]
```

### What commits are on this branch but not main?
```bash
git log main..HEAD --oneline
```

### What commits are on main but not this branch?
```bash
git log HEAD..main --oneline
```

---

## Search Commits

### Find commits by message
```bash
git log --grep="search term" --oneline
```

### Find commits that changed specific code
```bash
git log -S "function_name" --oneline
```

### Find commits by author
```bash
git log --author="name" --oneline
```

### Find commits in date range
```bash
git log --since="2024-01-01" --until="2024-01-31" --oneline
```

---

## Pretty Formats

### Compact with date and author
```bash
git log --pretty=format:"%h %ad %s (%an)" --date=short -20
```

### Graph view of all branches
```bash
git log --graph --oneline --all --decorate
```

---

## Understanding the Output

### Commit Hash
The `abc1234` at the start is the commit's unique ID. You only need the first 7 characters usually.

### HEAD
`HEAD` points to your current position (usually the latest commit on your branch).

### Branch/Tag Labels
`(main)`, `(origin/main)`, `(tag: v1.0)` show where branches and tags point.

### Merge Commits
Commits with two parents show where branches were merged.

---

## What Are You Looking For?

Tell me what you want to find in the history:
- A specific change?
- When something was introduced?
- What happened on a branch?
- Who made a change?

I'll help you find it.
