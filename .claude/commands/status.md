# Status

Give me a clear picture of where I am in git.

## Check Everything

Run these and explain what each tells us:

```bash
# What branch am I on?
git branch --show-current

# What's the state of my working directory?
git status

# How does my branch compare to main?
git log main..HEAD --oneline

# Are there any stashed changes I forgot about?
git stash list

# What's the recent history?
git log --oneline -10
```

## Explain in Plain English

After running the commands, summarize:

1. **Current branch**: What branch I'm on
2. **Working directory state**: 
   - Clean? 
   - Uncommitted changes? (list them)
   - Untracked files?
3. **Commits ahead of main**: How many commits, brief summary
4. **Stashes**: Any forgotten stashed work?
5. **Suggested next action**: What should I probably do next?

## Common Situations and What They Mean

### "Nothing to commit, working tree clean"
You have no uncommitted changes. Ready to start new work or switch branches.

### "Changes not staged for commit"
You've modified files but haven't `git add`ed them yet.

### "Changes to be committed"
Files are staged and ready to commit.

### "Your branch is ahead of 'origin/main' by N commits"
You have local commits that haven't been pushed.

### "Your branch is behind 'origin/main' by N commits"
The remote has commits you don't have locally. Consider pulling.

### "Your branch and 'origin/main' have diverged"
Both you and the remote have new commits. Will need to merge or rebase.

## If Things Look Messy

Help me understand my options:
- Should I commit what I have?
- Should I stash and come back to it?
- Should I create a WIP commit?
- Am I on the wrong branch?
