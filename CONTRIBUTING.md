# Contributing to UniFi CLI

Thank you for your interest in contributing to UniFi CLI!

## Getting Started

### Development Setup

```bash
# Clone the repository
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli

# Create conda environment
conda env create -f environment.yml
conda activate ui-cli

# Install in development mode
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
# Edit .env with your test credentials
```

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests (requires real API credentials)
pytest tests/integration/

# Run with coverage
pytest --cov=ui_cli
```

## Releases

`ui-cli` now uses a single version source in [`VERSION`](VERSION), while
[`cliff.toml`](cliff.toml) is only used for changelog generation. Public package
publishing is handled with the tag-based GitHub Actions workflow in
[`release.yml`](.github/workflows/release.yml), analogous to `fmcli` and `nanobanana`.

### One-time repository setup

1. Create the project on PyPI using the final distribution name.
2. Configure a PyPI Trusted Publisher for this GitHub repository.
3. Point the publisher at workflow `.github/workflows/release.yml`.
4. Leave the environment empty unless you intentionally add one later.

Recommended publisher settings:

- PyPI project name: `ui-cli`
- Owner: `sussdorff`
- Repository: `ui-cli`
- Workflow name: `release.yml`
- Environment name: empty

### Release workflow

```bash
# 0. Install local release tools
python -m pip install hatch build
# Install git-cliff separately if needed: https://git-cliff.org/docs/installation/

# 1. Bump the single source version
hatch version 1.3.0

# 2. Preview unreleased changelog content
git cliff --unreleased

# 3. Run local quality gates
pytest
uv build
```

1. Commit the release preparation changes.
2. Push the version tag that matches `VERSION`, for example `v1.3.0`.
3. The `Release` workflow will test, build, publish to PyPI, and create a GitHub release.

### Notes

- Keep SemVer. `git-cliff` is configured for changelog generation, not version bumping.
- The PyPI tag must match the version exactly: `v<contents of VERSION>`.
- Trusted Publishing removes the need for a long-lived PyPI API token.
- `hatch` and `git-cliff` are release tools and are not required for normal CLI use.

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `housekeeping/description` - Maintenance tasks

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add voucher creation command
fix: handle SSL certificate errors
docs: update user guide with new commands
test: add unit tests for local client
```

### Pull Requests

1. Create a feature branch from `main`
2. Make your changes
3. Run tests locally
4. Create a pull request with:
   - Clear description of changes
   - Test plan
   - Screenshots (for UI changes)

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use `ruff` for linting

### CLI Commands

- Use Typer for command definitions
- Use Rich for terminal output
- Support `-o/--output` for table/json/csv formats
- Include `--help` documentation

### Example Command Structure

```python
@app.command()
def list(
    output: OutputFormat = typer.Option(
        OutputFormat.TABLE, "-o", "--output", help="Output format"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Show additional details"
    ),
) -> None:
    """List items with optional filtering."""
    # Implementation
```

## Project Structure

```
ui-cli/
├── src/ui_cli/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── client.py            # Site Manager API client
│   ├── local_client.py      # Local Controller API client
│   ├── settings.py          # Configuration
│   ├── output.py            # Output formatting
│   └── commands/
│       ├── hosts.py         # Cloud: hosts commands
│       ├── sites.py         # Cloud: sites commands
│       ├── devices.py       # Cloud: devices commands
│       └── local/           # Local controller commands
│           ├── clients.py
│           ├── devices.py
│           ├── firewall.py
│           └── ...
├── tests/
│   ├── conftest.py          # Shared fixtures
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── .env.example
├── pyproject.toml
└── README.md
```

## Adding New Commands

### Cloud API Command

1. Add method to `src/ui_cli/client.py`
2. Create command file in `src/ui_cli/commands/`
3. Register in `src/ui_cli/main.py`
4. Add tests
5. Update documentation

### Local API Command

1. Add method to `src/ui_cli/local_client.py`
2. Create command file in `src/ui_cli/commands/local/`
3. Register in `src/ui_cli/commands/local/__init__.py`
4. Add tests
5. Update documentation

## Testing

### Unit Tests

- Test client methods with mocked responses
- Test command output formatting
- Test error handling

### Integration Tests

- Require real API credentials
- Marked with `@pytest.mark.integration`
- Skipped if credentials not configured

### Test Fixtures

Common fixtures are in `tests/conftest.py`:

- `mock_hosts_response`
- `mock_sites_response`
- `mock_devices_response`
- `mock_local_clients_response`
- etc.

## Questions?

Open an issue on GitHub for questions or discussions.
