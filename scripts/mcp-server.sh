#!/bin/bash
# UI-CLI MCP Server Wrapper
# Loads .env and starts the MCP server
#
# PYTHON_PATH is set by ./ui mcp install

# Get script directory (scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Get project root (parent of scripts/)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root (so .env is found)
cd "$PROJECT_ROOT"

# Load .env file if it exists
if [ -f ".env" ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Set PYTHONPATH to src/
export PYTHONPATH="$PROJECT_ROOT/src"

# Use PYTHON_PATH if set, otherwise try to find Python
PYTHON="${PYTHON_PATH:-}"
if [ -z "$PYTHON" ] || [ ! -x "$PYTHON" ]; then
    # Fallback: try common locations
    if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
        PYTHON="$PROJECT_ROOT/.venv/bin/python"
    else
        PYTHON="$(which python3 2>/dev/null || which python 2>/dev/null)"
    fi
fi

if [ -z "$PYTHON" ]; then
    echo "Error: Python not found" >&2
    exit 1
fi

# Run the MCP server
exec "$PYTHON" -m ui_mcp "$@"
