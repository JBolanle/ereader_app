# Undo

Help me undo a git mistake.

## First: Don't Panic

Almost everything in git is recoverable. Let's figure out what happened.

## What Are You Trying to Undo?

Ask me to describe the situation, then match it to one of these:

---

### "I want to unstage files (undo git add)"

```bash
# Unstage specific file
git reset HEAD [file]

# Unstage everything
git reset HEAD
```

Your changes are still there, just not staged.

---

### "I want to discard uncommitted changes to a file"

```bash
# Discard changes in specific file (DESTRUCTIVE)
git checkout -- [file]

# Discard all uncommitted changes (DESTRUCTIVE)
git checkout -- .
```

⚠️ **Warning**: This permanently deletes your uncommitted changes.

---

### "I want to undo my last commit but keep the changes"

```bash
git reset --soft HEAD~1
```

The commit is undone, but all changes are staged and ready.

---

### "I want to undo my last commit completely"

```bash
git reset --hard HEAD~1
```

⚠️ **Warning**: This deletes the commit AND the changes.

---

### "I want to fix my last commit message"

```bash
git commit --amend -m "New message"
```

Only do this if you haven't pushed yet.

---

### "I want to add more files to my last commit"

```bash
git add [forgotten-file]
git commit --amend --no-edit
```

Only do this if you haven't pushed yet.

---

### "I committed to the wrong branch"

```bash
# Undo the commit but keep changes
git reset --soft HEAD~1

# Stash the changes
git stash

# Switch to correct branch
git checkout [correct-branch]

# Apply the changes
git stash pop

# Commit on correct branch
git add .
git commit -m "your message"
```

---

### "I want to undo a pushed commit"

Create a new commit that reverses the changes:
```bash
git revert [commit-hash]
```

This is safe because it doesn't rewrite history.

---

### "I accidentally deleted a branch"

If it was recently deleted:
```bash
git reflog  # Find the commit hash
git checkout -b [branch-name] [commit-hash]
```

---

### "I'm in a weird state and don't know what happened"

```bash
git status
git log --oneline -10
git reflog -10
```

Show me the output and I'll help diagnose.

---

## The Nuclear Option (Last Resort)

If everything is truly messed up and you have a remote:

```bash
# Save any changes you want to keep
cp -r . ../backup

# Reset everything to match remote
git fetch origin
git reset --hard origin/main
```

---

## Golden Rule

**If you haven't pushed yet**, you can rewrite history freely.

**If you have pushed**, use `git revert` to undo safely, or coordinate with your team before force-pushing.

---

## What Happened?

Describe your situation and I'll guide you through the right fix.
