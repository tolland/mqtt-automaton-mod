# CLAUDE.md

## Structure of project

- src/main/java - Java source code of mod
- src/gametest/java - Fabric gametest testing framework code
- src/test/java - Java unit tests based on junit jupiter
- src-py - Python source code for mqttbot package
- tests - pytest based unit tests for mqttbot package
- docs - documentation and planning files
- config - configuration files for launching mqttbot python cli

## Code Quality Standards

### git process

- pull the latest changes to the current branch

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

### Python pytest
- Ensure signifant Python code is covered by pytest unit tests
- Run `pytest` to verify all tests pass before committing

### General Python

- use uv for package management
- File, package, and library comments should be placed below the main imports section at the top of the file.
- We should favour structured objects rather the dict[str, Any] pattern for passing data around.
- Dataclasses should have a sensible to_dict method for serialization.
- if the class is a core data structure, there should be __rich__ methods for better REPL representation.
- If the dataclass is sourced from config, it should include a from_dict classmethod for deserialization.
- Use type hints for all function signatures
