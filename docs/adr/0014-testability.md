# Testability

## Status
Accepted

## Context
GitNotes needs a well-structured testing approach that covers all major components: editor integration, hashing, locking, Pandoc export, and Git commands.

We considered several approaches:
- **A**: Mock-based unit tests with isolated components
- **B**: Integration tests with temp repos only
- **C**: Hybrid (unit + integration)

## Decision
**Hybrid approach: Both A and B**

### Editor Component
- Mock with `true` command, `cp`, or script file
- Simulate editor behavior by writing expected output to temp files
- Test hash comparison logic separately from actual editor spawning

### Hashing Component
- Deterministic: Same input always produces same SHA256 hash
- Testable with known files and expected outputs
- Can use fixed-size test fixtures for reproducibility

### Locks/flock Component
- Simulated in tests (file-based locks or memory locks)
- Test lock acquisition/release, timeout behavior
- Verify auto-release on process exit

### Pandoc Component
- Mocked output files (write expected HTML to temp location)
- Test pre-flight checks and error handling
- Test retry logic with controlled failures

### Git Commands
- Tested against temp repos created in test directory
- Use `tempfile.mkdtemp()` for isolated test environments
- Verify commit messages, file states after operations

## Implementation Details
1. **Unit tests** (isolated components):
   - Hash computation: Verify SHA256 output matches known values
   - Lock acquisition/release: Test with temp lock files
   - Pandoc pre-flight: Mock `shutil.which()` to simulate presence/absence
2. **Integration tests** (full flow):
   - Create temp Git repo, initialize GitNotes
   - Edit a note file through full session lifecycle
   - Verify commits created, hashes match expectations
3. **Test fixtures**: Pre-written test markdown files with known YAML front matter

### Why Hybrid?
- **Comprehensive coverage**: Unit tests catch edge cases; integration tests verify end-to-end behavior
- **Fast execution**: Unit tests run quickly for CI feedback
- **Realistic scenarios**: Integration tests match actual user workflow
- **Isolated testing**: Can test components independently without Git overhead

## Consequences

### Positive
- Comprehensive coverage: Both unit and integration tests catch issues
- Fast execution: Unit tests provide quick CI feedback
- Realistic scenarios: Integration tests match actual user workflow
- Isolated testing: Components can be tested independently

### Negative
- More test files to maintain (unit + integration)
- Slight complexity in test setup/teardown for both types

### Future Implications
- Can add property-based testing for hashing and lock logic
- Integration tests establish baseline for regression detection