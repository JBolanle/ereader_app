# Session Logs

This directory contains end-of-session summaries to maintain continuity between Claude Code sessions.

## Naming Convention

**Single session per day:**
- Use `YYYY-MM-DD.md` - e.g., `2025-12-01.md`

**Multiple sessions in one day:**
- First session: `YYYY-MM-DD.md`
- Subsequent sessions: `YYYY-MM-DD-session-2.md`, `YYYY-MM-DD-session-3.md`, etc.

## When to Create New vs Update Existing

**Create a NEW session file when:**
- Starting a fresh session after a break (1+ hours)
- Switching to a completely different task/topic
- Starting a new context (e.g., after closing and reopening Claude Code)

**Update EXISTING session file when:**
- Continuing work in the same context (< 1 hour break)
- Adding to the current task
- Making quick follow-up changes

**Rule of thumb:** If you need to read the previous session notes to understand context, create a new file.

## Created By

Use the `/wrapup` command at the end of each coding session:

```bash
/wrapup
```

The wrapup command will ask whether to create a new file or update an existing one based on timing and context.

## Purpose

Since Claude Code doesn't retain memory between sessions, these logs help:
- Remember what was accomplished
- Track decisions made
- Know what to pick up next
- Maintain project momentum
- Build a learning history over time

## Format

Each session log should include:
- **Accomplished**: What got done
- **Decisions Made**: Technical choices and reasoning
- **Learned Today**: Key concepts understood
- **Next Session**: What to pick up next
- **CLAUDE.md Updates**: Any changes made to project documentation