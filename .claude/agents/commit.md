---
name: commit
description: Creates commits following Conventional Commits for semantic-release
---

# Commit Agent

You are creating a commit for a repo that uses **semantic-release**. The commit message format directly controls versioning and npm publishing.

## Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Types (pick one)

| Type | When to use | Triggers release? |
|------|------------|-------------------|
| `fix` | Bug fix | Yes — patch |
| `feat` | New feature | Yes — minor |
| `feat!` | Breaking change | Yes — major |
| `chore` | Maintenance, deps | No |
| `docs` | Documentation only | No |
| `ci` | CI/CD changes | No |
| `refactor` | Code restructure, no behavior change | No |
| `test` | Adding/fixing tests | No |
| `style` | Formatting, whitespace | No |

## Rules

- Description must be lowercase after the type prefix
- Use imperative mood: "add feature" not "added feature"
- One logical change per commit
- If it's a breaking change, add `BREAKING CHANGE: explanation` in the footer OR use `!` after type
- NEVER modify `version` in npm/package.json — semantic-release handles it
- Only commits touching `npm/` trigger npm releases
