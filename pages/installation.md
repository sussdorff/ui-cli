# Installation

## Requirements

- Python 3.10 or higher
- pip or conda

## Install with pip

```bash
# Clone the repository
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install
pip install -e .
```

## Install with Conda

```bash
# Clone the repository
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli

# Create conda environment
conda env create -f environment.yml
conda activate ui-cli

# Install
pip install -e .
```

## Development Installation

For contributing or development:

```bash
pip install -e ".[dev]"
```

This includes:

- pytest - Testing framework
- pytest-asyncio - Async test support
- ruff - Linting
- mypy - Type checking

## Verify Installation

```bash
# Using the wrapper script
./ui --help

# Or directly after pip install
ui --help
```

Expected output:

```
Usage: ui [OPTIONS] COMMAND [ARGS]...

  UniFi CLI - Manage your UniFi infrastructure from the command line.

Options:
  --help  Show this message and exit.

Commands:
  devices    Manage UniFi devices
  hosts      Manage UniFi hosts
  isp        ISP metrics and information
  local      Local UniFi Controller commands (alias: lo)
  sdwan      SD-WAN configuration management
  sites      Manage UniFi sites
  speedtest  Run a speed test
  status     Check API connection status
  version    Show version information
```

## Updating

```bash
cd ui-cli
git pull origin main
pip install -e .
```

## Uninstalling

```bash
pip uninstall ui-cli

# If using conda
conda deactivate
conda env remove -n ui-cli
```
