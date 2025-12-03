# Sprint

Orchestrate a development sprint for a feature (for when you want to delegate more).

**Note**: For learning, prefer using individual commands (pm, mentor, developer) 
so you stay involved. Use this when you understand the patterns and want to move faster.

## Input

Feature name or description from CLAUDE.md's target features list.

## Phase 1: Specification

Invoke the `/pm` command in Plan mode to:
- Write a detailed spec for the feature
- Save to docs/specs/[feature-name].md
- Create GitHub issues for each task

**Stop and ask user to confirm before continuing.**

## Phase 2: Architecture (If Needed)

Invoke the `/architect` command to:
- Determine if new components or patterns are needed
- If yes, design them and document in docs/architecture/
- Update CLAUDE.md with any new patterns

**Stop and ask user to confirm before continuing.**

## Phase 3: Implementation

For each issue, invoke the `/developer` command to:
- Work through the issue in logical order
- Create feature branch
- Implement with tests
- Commit and push

**Stop and report progress. Ask if user wants to review before continuing.**

## Phase 4: Review

Invoke the `/code-review` command to:
- Review all changes against main
- Document feedback in docs/reviews/
- List any issues that need fixing

**Stop and report findings.**

## Phase 5: Completion

- If issues found, invoke `/developer` to fix them
- Invoke `/pr` to open PR with full description:
  - Summary of changes
  - Link to spec
  - List of issues closed
  - Screenshots if UI changes
- Update CLAUDE.md's Current Sprint section

## Final Report

Provide links to all artifacts:
- Spec document
- Architecture docs (if created)
- GitHub issues
- Branches created
- Review document
- Pull request

## Important

This command moves fast. If you're learning, consider instead:
1. `/pm` to create the spec
2. `/mentor` to understand what you'll build
3. Implement yourself with `/hint` when stuck
4. `/code-review` to get feedback
5. Fix issues yourself with `/mentor` help

The sprint command is for when you're confident and want to delegate.
