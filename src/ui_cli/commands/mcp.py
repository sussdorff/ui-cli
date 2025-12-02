"""MCP server management commands for Claude Desktop integration."""

import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax

app = typer.Typer(help="Manage MCP server for Claude Desktop")
console = Console()


# ==============================================================================
# Config Path Detection
# ==============================================================================


def get_config_path() -> Path:
    """Get Claude Desktop config path for current OS."""
    system = platform.system()
    if system == "Darwin":  # macOS
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    elif system == "Windows":
        return Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config/Claude/claude_desktop_config.json"


def get_src_path() -> Path:
    """Get src directory (parent of ui_cli)."""
    return Path(__file__).parent.parent.parent


def get_project_root() -> Path:
    """Get project root directory (contains .env file)."""
    return Path(__file__).parent.parent.parent.parent


def get_ui_mcp_path() -> Path:
    """Get ui_mcp package path."""
    return get_src_path() / "ui_mcp"


# ==============================================================================
# Output Helpers
# ==============================================================================


def print_header(title: str) -> None:
    """Print section header."""
    console.print(f"\n[bold]{title}[/bold]")
    console.print("=" * len(title))
    console.print()


def print_success(msg: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/green] {msg}")


def print_warning(msg: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]![/yellow] {msg}")


def print_error(msg: str) -> None:
    """Print error message."""
    console.print(f"[red]✗[/red] {msg}")


def print_info(msg: str) -> None:
    """Print info message."""
    console.print(f"[dim]→[/dim] {msg}")


def print_config_summary(config: dict) -> None:
    """Print MCP server configuration summary."""
    console.print()
    console.print("[dim]Configuration:[/dim]")
    console.print(f"  command: [cyan]{config.get('command', 'N/A')}[/cyan]")
    args = config.get('args', [])
    if args:
        console.print(f"  args:    [cyan]{args}[/cyan]")


# ==============================================================================
# Config Read/Write
# ==============================================================================


def read_config(path: Path) -> dict:
    """Read config file, return empty dict structure if doesn't exist."""
    if not path.exists():
        return {}

    try:
        content = path.read_text()
        if not content.strip():
            return {}
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise typer.Exit(
            console.print(f"[red]✗[/red] Invalid JSON in config file: {e}\n"
                         f"  Please fix manually or delete: {path}")
        )


def write_config(path: Path, config: dict) -> None:
    """Write config file with proper formatting."""
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write with nice formatting
    path.write_text(json.dumps(config, indent=2) + "\n")


def create_backup(path: Path) -> Path | None:
    """Create timestamped backup of config file."""
    if not path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".{timestamp}.bak")
    backup_path.write_text(path.read_text())
    return backup_path


# ==============================================================================
# MCP Config Generation
# ==============================================================================


def get_wrapper_script() -> Path:
    """Get path to MCP server wrapper script."""
    return get_project_root() / "scripts" / "mcp-server.sh"


def generate_mcp_config() -> dict:
    """Generate ui-cli MCP server configuration.

    Uses a wrapper script that:
    - Changes to project root
    - Sources .env file to load credentials
    - Sets PYTHONPATH
    - Runs the MCP server with the specified Python
    """
    wrapper_script = get_wrapper_script()

    return {
        "command": str(wrapper_script),
        "args": [],
        "env": {
            "PYTHON_PATH": sys.executable,
        }
    }


def check_mcp_module(python_path: str | Path) -> tuple[bool, str]:
    """Check if mcp module is installed in the given Python environment.

    Returns (success, message) tuple.
    """
    try:
        result = subprocess.run(
            [str(python_path), "-c", "import mcp.server.fastmcp; print('ok')"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and "ok" in result.stdout:
            return True, "installed"
        else:
            return False, "not installed"
    except subprocess.TimeoutExpired:
        return False, "check timed out"
    except Exception as e:
        return False, str(e)


# ==============================================================================
# Commands
# ==============================================================================


@app.command()
def install(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing configuration"),
) -> None:
    """Install ui-cli MCP server to Claude Desktop."""
    print_header("UI-CLI MCP Server Installation")

    config_path = get_config_path()
    console.print(f"Config file: [cyan]{config_path}[/cyan]\n")

    # Read existing config
    config = read_config(config_path)

    # Check existing MCP servers
    mcp_servers = config.get("mcpServers", {})
    existing_count = len(mcp_servers)

    if config_path.exists():
        print_success(f"Config file found ({existing_count} existing MCP server(s))")
    else:
        print_info("Config file will be created")

    # Check wrapper script exists
    wrapper_script = get_wrapper_script()
    if not wrapper_script.exists():
        print_error(f"Wrapper script not found: {wrapper_script}")
        console.print("  Run from the ui-cli project directory")
        raise typer.Exit(1)
    print_success(f"Wrapper script found: {wrapper_script}")

    # Check if ui-cli already configured
    if "ui-cli" in mcp_servers:
        if not force:
            print_warning("'ui-cli' already configured. Use --force to update.")
            print_config_summary(mcp_servers["ui-cli"])
            raise typer.Exit(1)
        else:
            print_info("Updating existing 'ui-cli' configuration")

    # Create backup
    if config_path.exists():
        backup_path = create_backup(config_path)
        if backup_path:
            print_success(f"Backup created: {backup_path.name}")

    # Add ui-cli config
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    mcp_config = generate_mcp_config()
    config["mcpServers"]["ui-cli"] = mcp_config

    # Write config
    write_config(config_path, config)
    print_success("Added 'ui-cli' to mcpServers")

    # Print summary
    print_config_summary(mcp_config)

    # Check mcp module
    console.print()
    mcp_ok, mcp_msg = check_mcp_module(sys.executable)
    if mcp_ok:
        print_success(f"mcp package installed ({mcp_msg})")
    else:
        print_error(f"mcp package not installed in {sys.executable}")
        console.print()
        console.print("[bold red]Required:[/bold red] Install the mcp package:")
        console.print(f"  [cyan]{sys.executable} -m pip install mcp[/cyan]")
        console.print()
        raise typer.Exit(1)

    console.print()
    console.print("[bold yellow]Restart Claude Desktop to activate the MCP server.[/bold yellow]")


@app.command()
def check() -> None:
    """Check MCP server installation status."""
    print_header("UI-CLI MCP Server Status")

    config_path = get_config_path()
    console.print(f"Config file: [cyan]{config_path}[/cyan]\n")

    # Check config file exists
    if not config_path.exists():
        print_error("Config file not found - Claude Desktop may not be installed")
        raise typer.Exit(1)

    print_success("Config file exists")

    # Read config
    config = read_config(config_path)
    mcp_servers = config.get("mcpServers", {})

    # Check ui-cli configured
    if "ui-cli" not in mcp_servers:
        print_error("'ui-cli' not configured - run 'ui mcp install'")
        raise typer.Exit(1)

    print_success("'ui-cli' is configured")

    ui_cli_config = mcp_servers["ui-cli"]
    has_errors = False

    # Validate wrapper script
    command_path = Path(ui_cli_config.get("command", ""))
    if command_path.exists():
        print_success(f"Wrapper script found: {command_path}")
    else:
        print_error(f"Wrapper script not found: {command_path}")
        has_errors = True

    # Check project root and .env
    project_root = get_project_root()
    if project_root.exists():
        print_success(f"Project root valid: {project_root}")
        env_file = project_root / ".env"
        if env_file.exists():
            print_success(".env file found")
        else:
            print_warning(f".env file not found at {env_file}")
    else:
        print_error(f"Project root not found: {project_root}")
        has_errors = True

    # Check ui_mcp module
    ui_mcp_path = get_ui_mcp_path()
    if ui_mcp_path.exists() and (ui_mcp_path / "__init__.py").exists():
        print_success("ui_mcp module found")
    else:
        print_error(f"ui_mcp module not found at: {ui_mcp_path}")
        has_errors = True

    # Check mcp package installed
    mcp_ok, mcp_msg = check_mcp_module(sys.executable)
    if mcp_ok:
        print_success(f"mcp package installed ({mcp_msg})")
    else:
        print_error("mcp package not installed")
        console.print(f"        Run: [cyan]{sys.executable} -m pip install mcp[/cyan]")
        has_errors = True

    # List other servers
    other_servers = [k for k in mcp_servers.keys() if k != "ui-cli"]
    if other_servers:
        console.print()
        console.print(f"[dim]Other MCP servers: {', '.join(other_servers)}[/dim]")

    console.print()
    if has_errors:
        console.print("[bold red]Status: Not Ready (fix errors above)[/bold red]")
        raise typer.Exit(1)
    else:
        console.print("[bold green]Status: Ready[/bold green]")


@app.command()
def remove() -> None:
    """Remove ui-cli MCP server from Claude Desktop."""
    print_header("UI-CLI MCP Server Removal")

    config_path = get_config_path()
    console.print(f"Config file: [cyan]{config_path}[/cyan]\n")

    # Check config exists
    if not config_path.exists():
        print_error("Config file not found")
        raise typer.Exit(1)

    # Read config
    config = read_config(config_path)
    mcp_servers = config.get("mcpServers", {})

    # Check ui-cli exists
    if "ui-cli" not in mcp_servers:
        print_warning("'ui-cli' is not configured - nothing to remove")
        raise typer.Exit(0)

    # Create backup
    backup_path = create_backup(config_path)
    if backup_path:
        print_success(f"Backup created: {backup_path.name}")

    # Remove ui-cli
    del config["mcpServers"]["ui-cli"]
    print_success("Removed 'ui-cli' from mcpServers")

    # Write config
    write_config(config_path, config)

    # List remaining servers
    remaining = list(config.get("mcpServers", {}).keys())
    if remaining:
        console.print()
        console.print(f"[dim]Remaining MCP servers: {', '.join(remaining)}[/dim]")
    else:
        console.print()
        console.print("[dim]No MCP servers remaining[/dim]")

    console.print()
    console.print("[bold yellow]Restart Claude Desktop to apply changes.[/bold yellow]")


@app.command()
def show() -> None:
    """Show current Claude Desktop MCP configuration."""
    print_header("Claude Desktop MCP Configuration")

    config_path = get_config_path()
    console.print(f"Config file: [cyan]{config_path}[/cyan]\n")

    if not config_path.exists():
        print_error("Config file not found")
        raise typer.Exit(1)

    # Read and display config
    config = read_config(config_path)

    if not config:
        console.print("[dim]Config file is empty[/dim]")
        return

    # Pretty print with syntax highlighting
    json_str = json.dumps(config, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)
