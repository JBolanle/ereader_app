# Learning Log

Track concepts learned, questions to explore, and patterns implemented.

---

## Concepts Learned

### 2025-12-01 — XML Namespaces
- **What**: XML namespaces prevent tag name collisions by prefixing tags with URIs (e.g., `{urn:oasis:names:tc:opendocument:xmlns:container}rootfiles`)
- **Why**: When mixing XML from different sources, tags might have the same name but different meanings. Namespaces keep them separate.
- **Example**: In EPUB's container.xml, all tags have the namespace `{urn:oasis:names:tc:opendocument:xmlns:container}`. Use XPath wildcard `.//{*}tagname` to find tags regardless of namespace.
- **Gotchas**: `root.find('rootfiles')` won't work if the element has a namespace. Must either include full namespace or use `{*}` wildcard.
- **Resources**: Python ElementTree docs on namespaces

### 2025-12-01 — XPath Syntax in ElementTree
- **What**: XPath is a query language for navigating XML. ElementTree supports a subset: `.` (current), `//` (recursive search), `{*}` (namespace wildcard)
- **Why**: More robust than direct child searches, especially with varying XML structures in the wild
- **Example**: `root.find('.//{*}rootfile')` finds `rootfile` at any depth with any namespace
- **Gotchas**: `//` searches recursively (slower but more forgiving), while `/` only searches direct children
- **Resources**: ElementTree XPath support docs

### 2025-12-01 — EPUB File Structure
- **What**: EPUB files are ZIP archives containing HTML/XHTML content, CSS, images, and metadata in standardized structure
- **Why**: Understanding the format is essential for building a parser/reader
- **Example**:
  - `META-INF/container.xml` → points to OPF file
  - `content.opf` → contains metadata, manifest, spine
  - HTML/XHTML files → actual book content
- **Gotchas**: File extensions are just labels—EPUB is literally a ZIP file renamed
- **Resources**: EPUB 3 specification

### 2025-12-01 — Context Managers (with statement)
- **What**: `with` statements ensure resources are properly cleaned up, even if errors occur
- **Why**: Prevents resource leaks (unclosed files, connections, etc.)
- **Example**: Nested context managers for reading files from ZIP:
  ```python
  with ZipFile(filename, 'r') as epub:
      with epub.open('path/to/file') as f:
          content = f.read()
  ```
- **Gotchas**: Files are automatically closed when exiting the `with` block
- **Resources**: Python context manager docs

### 2025-12-01 — Conventional Commits
- **What**: A standardized commit message format: `type(scope): description` (e.g., `feat(epub): add metadata parsing`)
- **Why**: Makes commit history readable, enables automated changelogs, and clearly communicates intent
- **Example**: `docs: add EPUB parsing feature specification` vs "updated files"
- **Gotchas**: Keep the first line under 50 chars; use imperative mood ("add" not "added")
- **Resources**: https://www.conventionalcommits.org/

### 2025-12-01 — Logical Commit Splitting
- **What**: Breaking changes into multiple focused commits rather than one large commit
- **Why**: Easier code review, cleaner history, ability to revert specific changes without affecting others
- **Example**: Today split command changes into (1) reorganization/renames and (2) enhancements - each commit tells a clear story
- **Gotchas**: Don't split too granularly - each commit should be a complete, logical unit of work
- **Resources**: Git best practices

### 2025-12-01 — Feature Specification Structure
- **What**: Structured documentation format: overview, user stories, acceptance criteria, edge cases, out-of-scope, tasks
- **Why**: Ensures everyone understands what "done" means, prevents scope creep, identifies edge cases early
- **Example**: Created docs/specs/epub-parsing.md with 187 lines covering all aspects of EPUB parsing
- **Gotchas**: "Out of scope" section is as important as "in scope" - prevents feature creep
- **Resources**: User story best practices

### 2025-12-01 — GitHub CLI Workflow
- **What**: Using `gh` command-line tool for GitHub operations instead of web UI
- **Why**: Faster workflow, scriptable, stays in terminal context
- **Example**: `gh issue create --title "..." --body "..."` to create issues programmatically
- **Gotchas**: Need to authenticate first with `gh auth login`; labels must exist in repo before using them
- **Resources**: https://cli.github.com/manual/

<!-- Template:
### [Date] — [Concept Name]
- **What**: Brief explanation of the concept
- **Why**: When and why you'd use it
- **Example**: Code snippet or reference to our codebase
- **Gotchas**: Things that tripped you up
- **Resources**: Links to docs or tutorials
-->

---

## Questions to Explore

<!-- Things you want to understand better -->

- How does LRU cache actually work under the hood?
- When should I use ThreadPoolExecutor vs asyncio?
- What's the difference between Protocol and ABC?
- How does the EPUB spine relate to actual page breaks in a UI?
- What's the best way to cache parsed XML for performance?
- Should I validate EPUB structure strictly or be forgiving?

---

## Patterns Implemented

Track patterns as you use them in the project:

- [ ] MVC pattern
- [ ] Protocol-based abstraction
- [ ] Factory pattern
- [ ] Observer pattern (for UI updates)
- [ ] Repository pattern (for data access)
- [x] Context managers for resource handling (2025-12-01: nested with for ZIP file reading)
- [ ] Async/await for I/O
- [x] Conventional commit messages (2025-12-01: all 7 commits followed the pattern)
- [x] Feature specification documentation (2025-12-01: comprehensive EPUB parsing spec)

---

## Code I'm Proud Of

### 2025-12-01 — EPUB Parsing Feature Spec
- **What**: Created comprehensive 187-line feature specification (docs/specs/epub-parsing.md)
- **Why it's good**:
  - Clear acceptance criteria that define "done"
  - Edge cases identified before implementation
  - Explicit "out of scope" prevents feature creep
  - Tasks broken down with size estimates
  - Success metrics defined
- **Reference**: docs/specs/epub-parsing.md

### 2025-12-01 — Git Command Organization
- **What**: Created 9 comprehensive git workflow commands and 4 GitHub integration commands
- **Why it's good**:
  - Teaching-oriented (explain when/why, not just how)
  - Safety warnings on destructive operations
  - Real examples from the project
  - Structured consistently for easy navigation
- **Reference**: .claude/commands/

---

## Mistakes and Lessons

<!-- Track mistakes so you don't repeat them -->

<!-- Template:
### [Date] — [What Happened]
- **Mistake**: What I did wrong
- **Why it was wrong**: The underlying issue
- **Lesson**: What I'll do differently
-->
