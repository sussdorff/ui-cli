"""Utility functions for local commands."""

import asyncio
import os
from contextlib import contextmanager
from typing import TypeVar

from rich.progress import Progress, SpinnerColumn, TextColumn

from ui_cli.output import console

T = TypeVar("T")

# Store timeout override globally for subcommands to access
_timeout_override: int | None = None

# Quick timeout value in seconds
QUICK_TIMEOUT = 5


def is_spinner_disabled() -> bool:
    """Check if spinners should be disabled.

    Spinners are disabled when:
    - UNIFI_NO_SPINNER=1 or UNIFI_NO_SPINNER=true
    - CI=true (common CI/CD environment variable)
    - NO_COLOR is set (accessibility/CI convention)
    """
    no_spinner = os.environ.get("UNIFI_NO_SPINNER", "").lower()
    if no_spinner in ("1", "true", "yes"):
        return True

    # Common CI/CD environment variables
    if os.environ.get("CI", "").lower() == "true":
        return True

    # NO_COLOR is a convention for disabling color/formatting
    if os.environ.get("NO_COLOR"):
        return True

    return False


def set_timeout_override(timeout: int | None) -> None:
    """Set the timeout override value."""
    global _timeout_override
    _timeout_override = timeout


def get_timeout() -> int | None:
    """Get the timeout override if --quick or --timeout was specified."""
    return _timeout_override


@contextmanager
def spinner(message: str = "Connecting..."):
    """Context manager that shows a spinner while executing.

    Usage:
        with spinner("Fetching clients..."):
            result = asyncio.run(async_operation())
    """
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[cyan]{message}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(message, total=None)
        yield


def run_with_spinner(coro, message: str = "Connecting...") -> T:
    """Run an async coroutine with a spinner.

    Spinner is automatically disabled in CI/CD environments.

    Usage:
        result = run_with_spinner(client.list_clients(), "Fetching clients...")
    """
    if is_spinner_disabled():
        return asyncio.run(coro)

    with spinner(message):
        return asyncio.run(coro)
