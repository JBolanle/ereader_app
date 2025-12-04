# Command Reference Card

Quick reference for all custom Claude Code commands in this project.

**Tip:** Type `/` in Claude Code to see all available commands with tab-completion.

---

## Code Standards Quick Reference

Before using commands, remember these non-negotiable rules:

- ✓ **Type hints** on all functions (parameters and return types)
- ✓ **Tests** for every new function (in `tests/` mirroring `src/`)
- ✓ **Custom exceptions** from `src/ereader/exceptions.py` (no bare `except:`)
- ✓ **Logging** instead of `print()` statements
- ✓ **Conventional commits** for all git commits
- ✓ **Run tests before committing**: `uv run pytest`
- ✓ **Run linting before committing**: `uv run ruff check src/`

See [CLAUDE.md](../CLAUDE.md) for complete code standards and architecture principles.

---

## Development Workflow Commands

### `/pm` — Product Manager
**When to use**: Starting a new feature, need specs or issues created
```
/pm "Create spec for bookmark system"
/pm "Break down the PDF support feature into tasks"
```

### `/ux` — User Experience Designer
**When to use**: Designing user-facing features, planning interactions, researching conventions

**UX is not just UI**: This command handles visual interfaces, user workflows, interaction patterns, error handling, information architecture, and feature decisions.

**Modes**:
- **Design**: Plan user interactions and layouts
- **Evaluate**: Critique existing UI/UX for usability
- **Patterns**: Research and apply established UX patterns
- **Flows**: Map user journeys and task flows
- **Research**: Investigate user needs and conventions to inform decisions

```
/ux design "the book library view"
/ux evaluate "check usability of current navigation"
/ux research "what keyboard shortcuts should we support?"
/ux flows "map the user journey for opening a book"
/ux patterns "pagination in e-readers"
```

### `/architect` — System Architect
**When to use**: Making technical decisions, designing components, evaluating libraries

**Note**: For user-facing features, use `/ux` first to design the interaction, then `/architect` to design the technical structure to support that UX.

**Enhanced thinking**: For important architectural decisions, the architect uses extended thinking:
- Standard decisions: Natural thinking about tradeoffs
- Important decisions (multi-component impact): "think hard" for thorough evaluation
- Critical decisions (foundational, hard to change): "think harder" or "ultrathink"

```
/architect "Should we use PyQt6 or textual for the UI?"
/architect "Design the plugin architecture"
/architect "think hard about whether to use Protocols or ABCs for book parsers"
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

**Workflow selection**: The developer adapts to task complexity:
- **Simple tasks** (< 1 hour): Direct implementation
- **Complex features**: Explore → Plan → Code → Commit pattern
- **Clear specifications**: Test-Driven Development (TDD) approach

```
/developer "Implement issue #12"
/developer "Generate test scaffolding for the bookmark module"
/developer "Use TDD approach for the metadata extraction function"
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

## Development Workflow Patterns

This project follows specific patterns for different types of work. Understanding these helps you choose the right commands.

### Pattern 1: Explore → Plan → Code → Commit
**Use for:** Non-trivial features, new components, complex refactoring

**Flow:**
1. **Explore** — Understand existing code and patterns
   - Use subagents: "Use a subagent to investigate how we handle X"
   - Read relevant files and specs in `docs/specs/`
   - Ask clarifying questions
   - **DO NOT write code yet**

2. **Plan** — Design the approach
   - Create written plan outlining approach
   - Consider: What files change? What tests needed? What patterns to follow?
   - Document architectural decisions in `docs/architecture/`
   - Review plan before implementation

3. **Code** — Implement the solution
   - Follow plan and code standards
   - Run tests frequently during development
   - Commit related changes together

4. **Review & Commit** — Ensure quality
   - Run full test suite and linting
   - Use `/code-review` for self-assessment
   - Write clear conventional commit message

### Pattern 2: Test-Driven Development (TDD)
**Use for:** Clear input/output specifications, bug fixes, core algorithms

**Flow:**
1. **Write failing tests first**
   - Cover happy path, edge cases, error conditions
   - Run tests to confirm they fail appropriately
   - Commit: `test: add tests for [feature]`

2. **Implement to pass tests**
   - Write simplest code that makes tests pass
   - Run tests after each small change
   - DO NOT modify tests unless they have bugs

3. **Refactor with safety**
   - Improve code quality while keeping tests green
   - Commit: `feat: implement [feature]`

### Pattern 3: UX-First Development
**Use for:** UI components, user workflows, interaction patterns, any feature users interact with

**Flow:**
1. **Design UX first** (use `/ux`)
   - For UI/visual: `/ux design` to plan layout and interactions
   - For workflows: `/ux flows` to map user journeys
   - For decisions: `/ux research` to investigate conventions
   - Get user approval on UX approach

2. **Plan architecture** (use `/architect` if needed)
   - Design technical structure to support the UX
   - Data models, state management, caching strategies

3. **Implement** following both designs
   - UX design guides user experience
   - Architecture guides technical structure
   - Run tests frequently

4. **Evaluate usability** (use `/ux evaluate`)
   - Check implementation matches UX design
   - Identify usability issues

5. **Review and iterate**
   - `/code-review` for code quality
   - Fix issues from both UX and code review

### Using Subagents Effectively

Subagents preserve main context while investigating specific questions:

```
"Use a subagent to investigate how EPUB spine ordering works in our current code"
"Use a subagent to check if we already have a caching pattern for page rendering"
```

**When to use subagents:**
- Early in tasks to verify assumptions
- To investigate specific details without cluttering main context
- For focused searches across multiple files
- When exploring unfamiliar parts of the codebase

---

## Common Workflows

### Starting a New UI Feature (Learning Mode)
```
/pm "Create spec for [feature]"                              # Get spec and issues
/ux design "[feature name]"                                  # Design user experience
# Review and approve UX design
/architect "Design the component"                            # Get architecture (if needed)
/mentor "Explain what I need to know"                        # Learn the concepts
/branch "feature/[name]"                                     # Create branch
# Use a subagent to investigate existing patterns
# ... implement yourself using UX-First or TDD pattern ...
/hint "stuck on X"                                           # Get nudges when stuck
/ux evaluate                                                 # Check usability
/code-review                                                 # Get code feedback
# ... fix issues ...
/commit                                                      # Save work
/pr                                                          # Open PR
/wrapup                                                      # Document session
```

### Starting a Backend Feature (Learning Mode)
```
/pm "Create spec for [feature]"                              # Get spec and issues
/architect "Design the component"                            # Get architecture
/mentor "Explain what I need to know"                        # Learn the concepts
/branch "feature/[name]"                                     # Create branch
# Use a subagent to investigate existing patterns
# ... implement yourself using TDD or Explore→Plan→Code pattern ...
/hint "stuck on X"                                           # Get nudges when stuck
/code-review                                                 # Get feedback
# ... fix issues ...
/commit                                                      # Save work
/pr                                                          # Open PR
/wrapup                                                      # Document session
```

### Starting a New Feature (Faster Mode)
```
/pm "Create spec for [feature]"                              # Get spec and issues
/ux "[mode] [feature]"                                       # UX design if user-facing
/architect "Design the component"                            # Get architecture
"Use a subagent to check existing patterns for X"            # Quick investigation
/developer "Implement issue #N using Explore→Plan→Code"      # Delegate with pattern
/ux evaluate                                                 # Check usability (if UI feature)
/code-review                                                 # Review the code
/pr                                                          # Open PR
```

### Complex Feature (TDD Approach)
```
/pm "Create spec for [feature]"                              # Get spec and issues
/architect "Design component interface"                      # Define API surface
/branch "feature/[name]"                                     # Create branch
/developer "Write tests first for issue #N"                  # Create failing tests
# Verify tests fail
/developer "Implement to pass tests"                         # Write implementation
# Run tests, iterate
/code-review                                                 # Review
/commit                                                      # Save work
/pr                                                          # Open PR
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
| Check usability of UI | `/ux evaluate` |
| Test my knowledge | `/quiz` |
| Plan a feature | `/pm` |
| Design user experience | `/ux` |
| Design architecture | `/architect` |
| Research UX conventions | `/ux research` |
| Map user workflows | `/ux flows` |
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