# otter-ml

AI-powered ML framework. Python core + npm wrapper in `npm/`.

## Commits

This repo uses **semantic-release** to auto-publish the npm package. Every commit to `main` that touches `npm/` is analyzed to determine the version bump.

**All commits MUST follow the Conventional Commits spec:**

- `fix: description` — patch release (0.0.X)
- `feat: description` — minor release (0.X.0)
- `feat!: description` or footer `BREAKING CHANGE: ...` — major release (X.0.0)
- `chore:`, `docs:`, `ci:`, `refactor:`, `test:`, `style:` — no release

**Rules:**
- Never modify `version` in `npm/package.json` manually — semantic-release manages it
- Never tag releases manually — semantic-release creates tags and GitHub Releases
- Commit messages must be lowercase after the type prefix
- One logical change per commit — don't bundle unrelated changes
