# Diff

Help me understand what changed.

## Common Diff Commands

### What have I changed but not staged?
```bash
git diff
```

### What have I staged (ready to commit)?
```bash
git diff --cached
```

### What have I changed total (staged + unstaged)?
```bash
git diff HEAD
```

### What's different between my branch and main?
```bash
git diff main
```

### Summary of what changed (files only)
```bash
git diff --stat main
```

---

## Specific Comparisons

### Diff a specific file
```bash
git diff [file-path]
git diff main -- [file-path]
```

### Diff between two commits
```bash
git diff [commit1] [commit2]
```

### Diff between two branches
```bash
git diff branch1..branch2
```

### What changed in the last commit?
```bash
git diff HEAD~1
```

---

## Reading a Diff

```diff
diff --git a/file.py b/file.py
index abc123..def456 100644
--- a/file.py      # Old version
+++ b/file.py      # New version
@@ -10,7 +10,8 @@ def some_function():
     existing line
-    removed line
+    added line
+    another added line
     existing line
```

- Lines starting with `-` were removed (shown in red)
- Lines starting with `+` were added (shown in green)
- Lines with no prefix are context (unchanged)
- `@@ -10,7 +10,8 @@` means: starting at line 10, showing 7 lines old → 8 lines new

---

## Helpful Options

### Word-by-word diff (better for prose)
```bash
git diff --word-diff
```

### Ignore whitespace changes
```bash
git diff -w
```

### Show only names of changed files
```bash
git diff --name-only main
```

### Show names and status (added/modified/deleted)
```bash
git diff --name-status main
```

---

## Review Before Commit

Before committing, I recommend:

```bash
# See what you're about to commit
git diff --cached

# Check you haven't missed anything
git status
```

---

## What Would You Like to Compare?

Tell me what you want to see:
- Your current uncommitted changes?
- What's different from main?
- What a specific commit changed?
- Changes to a particular file?
