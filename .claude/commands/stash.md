# Stash

Help me manage stashed changes.

## What is Stash?

Stash is like a clipboard for your uncommitted changes. It lets you:
- Temporarily save work in progress
- Switch branches without committing
- Set aside changes to work on something urgent

---

## Common Operations

### Save current changes to stash

```bash
# Stash with auto-generated message
git stash

# Stash with descriptive message (recommended)
git stash push -m "WIP: description of what I was doing"
```

This saves both staged and unstaged changes.

### See what's stashed

```bash
git stash list
```

Output looks like:
```
stash@{0}: On feature/epub: WIP: parsing chapter metadata
stash@{1}: On main: experimenting with caching
```

### Bring back stashed changes

```bash
# Apply most recent stash (keeps it in stash list)
git stash apply

# Apply and remove from stash list
git stash pop

# Apply a specific stash
git stash apply stash@{1}
```

### See what's in a stash

```bash
# Show summary of most recent stash
git stash show

# Show full diff
git stash show -p

# Show specific stash
git stash show stash@{1} -p
```

### Delete stashed changes

```bash
# Delete most recent stash
git stash drop

# Delete specific stash
git stash drop stash@{1}

# Delete ALL stashes (careful!)
git stash clear
```

---

## Common Workflows

### "I need to switch branches but I'm not ready to commit"

```bash
git stash push -m "WIP: what I was working on"
git checkout other-branch
# ... do other work ...
git checkout original-branch
git stash pop
```

### "I want to stash only some files"

```bash
git stash push -m "description" path/to/file1 path/to/file2
```

### "I want to apply my stash to a different branch"

```bash
git stash  # on current branch
git checkout target-branch
git stash pop
```

If there are conflicts, resolve them like a merge.

---

## Best Practices

1. **Always use descriptive messages**: Future you will thank present you
   ```bash
   git stash push -m "WIP: user auth - login form validation incomplete"
   ```

2. **Don't let stashes pile up**: Review and clean old stashes regularly
   ```bash
   git stash list  # Check what's there
   ```

3. **Consider committing instead**: A WIP commit on a branch is often clearer
   ```bash
   git commit -m "WIP: work in progress on X"
   ```
   You can always squash it later.

---

## What Would You Like to Do?

Tell me your situation and I'll help with the right stash commands.
