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

---

## Code I'm Proud Of

<!-- Reference good code you wrote and why it's good -->

---

## Mistakes and Lessons

<!-- Track mistakes so you don't repeat them -->

<!-- Template:
### [Date] — [What Happened]
- **Mistake**: What I did wrong
- **Why it was wrong**: The underlying issue
- **Lesson**: What I'll do differently
-->
