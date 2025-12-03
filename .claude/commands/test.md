# Test

Run comprehensive test suite with coverage analysis and code quality checks.

## Purpose

Provide fast feedback during development by running all quality checks:
- Test suite execution
- Coverage analysis and reporting
- Linting and code style
- Type checking (when enabled)

Run this frequently during development, not just before commits.

## What This Does

1. Run all tests with coverage reporting
2. Analyze coverage against project standards
3. Identify untested code and assess risk
4. Run linting checks
5. Provide actionable recommendations

## Execution

```bash
# 1. Run tests with coverage
echo "Running test suite with coverage..."
uv run pytest --cov=src/ereader --cov-report=term-missing --cov-fail-under=80

# 2. Run linting
echo ""
echo "Running linting checks..."
uv run ruff check src/

# 3. Type checking (when mypy is configured)
# echo ""
# echo "Running type checks..."
# uv run mypy src/
```

## Coverage Analysis

After running tests, analyze the coverage report to understand what's tested and what isn't.

### Coverage Evaluation Criteria

Use these thresholds aligned with professional standards:

- **< 80%**: 🔴 Below minimum threshold - investigate why coverage dropped
- **80-89%**: 🟡 Acceptable - meets minimum standard
- **90-94%**: 🟢 Good coverage - professional standard
- **95-100%**: ✅ Excellent coverage - high-quality code

### What to Analyze

For each module with missing coverage, evaluate:

1. **What lines are missing?** (from --cov-report=term-missing)
2. **What type of code is untested?**
   - Critical user-facing features → 🔴 Must test
   - Error handling edge cases → 🟡 Consider testing
   - Defensive logging/warnings → 🟢 Low priority
3. **What's the risk if bugs exist there?**
   - User data loss/corruption → 🔴 Critical
   - UI glitches or poor UX → 🟡 Medium
   - Logging inconsistencies → 🟢 Low
4. **What's the effort to test?**
   - Simple unit test → Just do it
   - Requires mock setup → Worth it for critical paths
   - Needs complex malformed data → Document and defer

### Professional Decision Framework

Use this framework to decide what to test:

```
For each untested code section:

IF (critical functionality OR user-facing feature):
    Priority: 🔴 MUST TEST NOW

ELSE IF (error handling for common scenarios):
    Priority: 🟡 SHOULD TEST SOON

ELSE IF (edge cases with low probability):
    Priority: 🟢 TEST IF TIME PERMITS

ELSE IF (defensive code for malformed inputs):
    Priority: ⚪ DOCUMENT AND DEFER
```

## Report Format

Provide a clear, actionable report:

### ✅ Test Results
```
Tests: X passed, Y failed
Coverage: Z% (threshold: 80%)
Linting: Pass/Fail with N issues
```

### 📊 Coverage Breakdown

By module:
```
src/ereader/models/epub.py     93%  (11 lines missing - see analysis)
src/ereader/controllers/       0%   (not implemented yet)
src/ereader/views/             0%   (not implemented yet)
```

### 🔴 Critical Gaps (Must Address)

List any:
- User-facing features without tests
- Critical paths with no coverage
- Test failures that need fixing

If none: "✅ No critical gaps - all user-facing features tested"

### 🟡 Coverage Opportunities (Consider)

List areas where coverage could be improved:
- Missing error handling tests
- Edge cases not covered
- Integration test gaps

For each, provide:
- What's untested
- Why it matters (or doesn't)
- Estimated effort to test

### 🟢 Well-Tested Areas

Highlight modules with excellent coverage (90%+):
- Reinforces good practices
- Shows what's safe to refactor

### 📝 Recommendations

Provide specific, prioritized actions:

**Now (before commit):**
- Fix failing tests
- Test critical untested features

**Soon (this sprint):**
- Add tests for common error cases
- Improve coverage in X module

**Later (backlog):**
- Edge case testing for Y
- Integration tests for Z

**Never (document why):**
- Defensive logging in edge cases (lines X-Y)
- Malformed input handling (would require extensive mock data)

## Coverage Trend Tracking

When possible, note coverage changes:
```
Previous: 91%
Current:  93% ↑
Delta:    +2% ✅
```

If coverage dropped:
```
Previous: 93%
Current:  89% ↓
Delta:    -4% 🔴 INVESTIGATE
```

Coverage should never decrease unless there's a good reason (e.g., removing dead code).

## Integration with Other Commands

### During Development
```bash
# Write code
# Write tests
/test              # Fast feedback loop
# Fix issues
/test              # Verify fixes
```

### Before Commit
```bash
/test              # Ensure all tests pass
/code-review       # Comprehensive code quality review
/commit            # Commit with confidence
```

### Professional Workflow
This mirrors industry CI/CD pipelines:
1. Developer runs /test locally (frequent)
2. /code-review before commit (quality gate)
3. CI runs automated tests on push (verification)

## When Tests Fail

If tests fail:

1. **Don't panic** - failures are feedback
2. **Read the error** - understand what broke
3. **Reproduce** - can you trigger it manually?
4. **Fix** - address the root cause
5. **Verify** - run /test again

Common failure types:
- **Logic error**: Fix the implementation
- **Test error**: Fix the test (if test was wrong)
- **Regression**: New code broke old functionality
- **Flaky test**: Test has timing/dependency issues

## When Coverage Drops

If coverage is below threshold:

1. **Identify what's new** - use git diff
2. **Write tests first** - for the new code
3. **Run /test** - verify coverage improves
4. **Consider test quality** - are you testing the right things?

Don't chase 100% coverage - chase meaningful coverage.

## Success Criteria

The /test command succeeds when:
- ✅ All tests pass
- ✅ Coverage meets or exceeds 80%
- ✅ No linting errors
- ✅ No critical untested code
- ✅ Coverage hasn't decreased unexpectedly

## Remember

**Quality over quantity**: 80% meaningful coverage is better than 100% shallow coverage.

**Test what matters**: User-facing features and critical paths first, edge cases second.

**Fast feedback**: Run /test frequently - don't wait until commit time.

**Learn from failures**: Every test failure teaches you something about your code.
