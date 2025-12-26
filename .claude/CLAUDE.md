# CLAUDE.md

## Code Quality Standards

### Before Every Commit

1. Always run `./gradlew spotlessCheck` before creating any commit
2. If spotless fails, run `./gradlew spotlessApply` to auto-fix, then verify with spotlessCheck again

### Spotless Workflow

When you finish code changes:
1. Run: `./gradlew spotlessApply`
2. Run: `./gradlew spotlessCheck` (verify it passes)
3. Run: `git add -A`
