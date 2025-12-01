# Session Logs

This directory contains end-of-session summaries to maintain continuity between Claude Code sessions.

## Naming Convention

`YYYY-MM-DD.md` - e.g., `2024-01-15.md`

## Created By

Use the `/wrapup` command at the end of each coding session:

```bash
claude /wrapup
```

## Purpose

Since Claude Code doesn't retain memory between sessions, these logs help:
- Remember what was accomplished
- Track decisions made
- Know what to pick up next
- Maintain project momentum


## Other Notes
- Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP
tools to resolve library id and get library docs without me having to explicitly ask.