# Sync

Help me sync my local repository with GitHub.

## Assess the Situation First

```bash
# What branch am I on?
git branch --show-current

# Do I have uncommitted changes?
git status

# Fetch latest from remote (doesn't change local files)
git fetch origin

# How does my branch compare to remote?
git status -sb

# Check GitHub repo status
gh repo sync --dry-run 2>/dev/null || echo "Not a fork or already synced"
```

## Common Scenarios

### Scenario 1: Update main with latest from GitHub

```bash
git checkout main
git pull origin main
```

Or using gh for a fork:
```bash
gh repo sync
```

Then if I was on a feature branch:
```bash
git checkout [my-branch]
git merge main  # or rebase
```

### Scenario 2: My feature branch is behind main

Options:
1. **Merge main into your branch** (simpler, creates merge commit)
   ```bash
   git merge main
   ```

2. **Rebase onto main** (cleaner history, rewrites commits)
   ```bash
   git rebase main
   ```

Explain the tradeoffs and ask which I prefer.

### Scenario 3: Push my commits to GitHub

```bash
git push origin [branch-name]
```

If it's a new branch:
```bash
git push -u origin [branch-name]
```

### Scenario 4: Remote has changes I don't have (same branch)

```bash
git pull origin [branch-name]
```

If there are conflicts, help me through them.

### Scenario 5: Sync a Forked Repository

```bash
# Sync fork with upstream
gh repo sync

# Or specify upstream
gh repo sync --source owner/repo
```

## Handling Merge Conflicts

If conflicts occur:

1. Show which files have conflicts:
   ```bash
   git status
   ```

2. Explain the conflict markers:
   ```
   <<<<<<< HEAD
   your changes
   =======
   their changes
   >>>>>>> branch-name
   ```

3. Guide me through resolving each file

4. Complete the merge:
   ```bash
   git add [resolved-files]
   git commit  # for merge
   # or
   git rebase --continue  # for rebase
   ```

## If Things Go Wrong

### Undo a merge that hasn't been committed
```bash
git merge --abort
```

### Undo a rebase in progress
```bash
git rebase --abort
```

### I accidentally committed to main
```bash
git reset --soft HEAD~1  # Undo commit, keep changes
git checkout -b feature/[name]  # Move to new branch
git checkout main
git reset --hard origin/main  # Reset main to remote
```

## Check PR Status After Syncing

```bash
# See if your PR needs attention
gh pr status

# Check CI status on your PR
gh pr checks
```

## Explain What Happened

After syncing, summarize:
- What changed
- Any conflicts resolved
- Current state
