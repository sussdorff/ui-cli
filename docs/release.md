# Release Process

`ui-cli` uses Semantic Versioning and publishes to PyPI from a git tag, following
the same overall pattern as `fmcli` and `nanobanana`.

## One-time PyPI setup

Create the `ui-cli` project on PyPI and add a Trusted Publisher with these values:

- PyPI project name: `ui-cli`
- Owner: `sussdorff`
- Repository: `ui-cli`
- Workflow filename: `.github/workflows/release.yml`
- Environment name: leave empty

This allows the GitHub Actions release workflow to publish without a stored PyPI token.

## Release flow

```bash
# 1. Bump the single version source
hatch version 1.3.0

# 2. Review unreleased changelog content
git cliff --unreleased

# 3. Run quality gates
uv run pytest tests/unit
uv build

# 4. Commit and push
git add VERSION CHANGELOG.md
git commit -m "chore(release): prepare v1.3.0"
git push

# 5. Tag and push the release
git tag v1.3.0
git push origin v1.3.0
```

When the tag is pushed, `.github/workflows/release.yml` will:

1. Run unit tests
2. Verify that the tag matches `VERSION`
3. Build the package with `uv build`
4. Publish to PyPI with `uv publish --trusted-publishing always`
5. Create a GitHub release

## Notes

- `ui-cli` keeps a single version source in the root `VERSION` file.
- `git-cliff` is used for changelog generation only.
- The release tag must always be `v<contents of VERSION>`.
