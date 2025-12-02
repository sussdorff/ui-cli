"""Entry point for running the MCP server.

Usage:
    cd src && python -m ui_mcp
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ui_mcp.server import main

if __name__ == "__main__":
    main()
