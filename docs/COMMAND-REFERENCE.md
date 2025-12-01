# Command Reference Card

Quick reference for all custom Claude Code commands in this project.

---

## Development Workflow Commands

### `/pm` — Product Manager
**When to use**: Starting a new feature, need specs or issues created
```
/pm "Create spec for bookmark system"
/pm "Break down the PDF support feature into tasks"
```

### `/architect` — System Architect
**When to use**: Making technical decisions, designing components, evaluating libraries
```
/architect "Should we use PyQt6 or textual for the UI?"
/architect "Design the plugin architecture"
```

### `/mentor` — Teaching Companion
**When to use**: Learning concepts, need explanations, want guidance (not solutions)
```
/mentor "Explain how async/await works in Python"
/mentor "Help me understand the code I need to write for issue #5"
/mentor "Review my implementation and explain what I could improve"
```

### `/hint` — Minimal Nudge
**When to use**: Stuck on something, want the smallest possible help
```
/hint "My function returns None when it shouldn't"
/hint "The test is failing but I don't see why"
```

### `/developer` — Code Implementer
**When to use**: Delegating implementation (use sparingly when learning)
```
/developer "Implement issue #12"
/developer "Generate test scaffolding for the bookmark module"
```

### `/code-review` — Code Reviewer
**When to use**: Finished implementing, want feedback before merging
```
/code-review
/code-review "Focus on error handling"
```

### `/debug` — Debugging Guide
**When to use**: Something's broken, want to learn to find the problem (not just fix it)
```
/debug "The page rendering is slow and I don't know why"
/debug "Getting a KeyError but the key should exist"
```

### `/study` — Deep Dive Learning
**When to use**: Want to thoroughly understand a concept
```
/study "Python Protocols and structural typing"
/study "asyncio event loops"
/study "PyQt signals and slots"
```

### `/quiz` — Test Understanding
**When to use**: Check if you actually learned something
```
/quiz "EPUB file structure"
/quiz "The MVC pattern"
/quiz "async/await"
```

### `/wrapup` — Session Summary
**When to use**: End of coding session, preserve context for next time
```
/wrapup
```

### `/sprint` — Full Feature Orchestration
**When to use**: Want to delegate an entire feature (use when confident, not learning)
```
/sprint "Implement the bookmark system"
```

---

## Git & GitHub Commands

### `/branch` — Start New Work
**When to use**: Beginning work on a feature, bug fix, or task
```
/branch "working on epub parsing"
/branch "fixing the page navigation bug"
```

### `/gh-status` — Current State
**When to use**: Need to understand where you are in git/GitHub
```
/gh-status
```

### `/commit` — Save Work
**When to use**: Ready to commit changes, want a good commit message
```
/commit
```

### `/diff` — View Changes
**When to use**: See what you've changed before committing
```
/diff
/diff "compare against main"
```

### `/log` — Explore History
**When to use**: Find past changes, understand what happened
```
/log "what changed in the models folder"
/log "find commits about caching"
```

### `/pr` — Open Pull Request
**When to use**: Feature complete, ready for merge
```
/pr
```

### `/sync` — Sync with Remote
**When to use**: Update from GitHub, push changes, handle merges
```
/sync
/sync "update main and rebase my branch"
```

### `/stash` — Temporary Storage
**When to use**: Need to switch branches but have uncommitted work
```
/stash "save my work in progress"
/stash "restore my stashed changes"
```

### `/undo` — Fix Git Mistakes
**When to use**: Made a git mistake, need to recover
```
/undo "I committed to the wrong branch"
/undo "I want to undo my last commit"
```

### `/issues` — Manage GitHub Issues
**When to use**: Create, view, edit, or close GitHub issues
```
/issues "create a bug report"
/issues "list my assigned issues"
/issues "close issue #15"
```

### `/repo` — Repository Management
**When to use**: Setup repo, manage settings, releases, actions
```
/repo "create a new GitHub repo"
/repo "check CI status"
/repo "create a release"
```

---

## Common Workflows

### Starting a New Feature (Learning Mode)
```
/pm "Create spec for [feature]"          # Get spec and issues
/mentor "Explain what I need to know"    # Learn the concepts
/branch "feature/[name]"                 # Create branch
# ... implement yourself ...
/hint "stuck on X"                       # Get nudges when stuck
/code-review                             # Get feedback
# ... fix issues ...
/commit                                  # Save work
/pr                                      # Open PR
/wrapup                                  # Document session
```

### Starting a New Feature (Faster Mode)
```
/pm "Create spec for [feature]"          # Get spec and issues
/architect "Design the component"        # Get architecture
/developer "Implement issue #N"          # Delegate implementation
/code-review                             # Review the code
/pr                                      # Open PR
```

### Debugging a Problem
```
/debug "describe the problem"            # Get guided help
# ... investigate based on hints ...
/mentor "explain why X happens"          # Understand root cause
/commit                                  # Save the fix
```

### Daily Standup with Yourself
```
/gh-status                               # Where am I?
/issues "list my assigned issues"        # What's on my plate?
/log "what did I do yesterday"           # Refresh memory
```

### End of Day
```
/commit                                  # Save any pending work
/wrapup                                  # Document the session
```

---

## Decision Guide: Which Command?

| I want to... | Use |
|--------------|-----|
| Understand a concept | `/mentor` or `/study` |
| Get unstuck (small help) | `/hint` |
| Get unstuck (more help) | `/mentor` |
| Get unstuck (debug) | `/debug` |
| Have code written for me | `/developer` |
| Review my code | `/code-review` |
| Test my knowledge | `/quiz` |
| Plan a feature | `/pm` |
| Design architecture | `/architect` |
| Start new work | `/branch` |
| See my git state | `/gh-status` |
| Save my work | `/commit` |
| See what changed | `/diff` |
| Open a PR | `/pr` |
| Fix a git mistake | `/undo` |
| Manage issues | `/issues` |
| End my session | `/wrapup` |

---

## Tips

1. **Start with `/mentor`** — When in doubt, ask the mentor first
2. **Use `/hint` before `/mentor`** — Try the smallest help first
3. **Run `/code-review` before `/pr`** — Catch issues early
4. **Always `/wrapup`** — Future you will thank present you
5. **`/commit` often** — Small, frequent commits are better
6. **Check `/gh-status` when confused** — Know where you are