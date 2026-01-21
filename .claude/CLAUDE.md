# CLAUDE.md

## Code Quality Standards

### Before Every Commit

1. Always run `./gradlew spotlessCheck build` before creating any commit
2. If spotless fails, run `./gradlew spotlessApply` to auto-fix, then verify with spotlessCheck again
3. Run ruff for Python code linting and formatting checks

### Spotless Workflow

When you finish code changes:
1. Run: `./gradlew spotlessApply`   check for and apply any formatting issues
2. Run: `./gradlew build`  resolve any build issues
3. Run: `./gradlew spotlessCheck` (verify it passes)
4. Run: `git add -A`

### Java Formatting Requirements:
- No trailing whitespace on any line
- 4-space indentation (no tabs)
- One blank line between method definitions
- Opening braces on same line as declaration
- Import statements alphabetically sorted within groups
