"""UniFi Site Manager CLI - Manage your UniFi infrastructure from the command line."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _version_file_path() -> Path:
    """Return the repository version file path when running from a source checkout."""
    return Path(__file__).resolve().parents[2] / "VERSION"


def _read_version_file() -> str:
    """Read the repository version during local source execution."""
    version_file = _version_file_path()
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _detect_version() -> str:
    """Prefer the checkout version file and fall back to installed package metadata."""
    version_file = _version_file_path()
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    try:
        return version("ui-cli")
    except PackageNotFoundError:
        return "0.0.0"


__version__ = _detect_version()
