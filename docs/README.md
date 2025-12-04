# UI-CLI Documentation

This directory contains project documentation for developers and contributors.

## Contents

| Document | Description |
|----------|-------------|
| [Client Groups](groups.md) | Groups feature design and implementation |
| [MCP Server](mcp.md) | MCP server architecture and tools |

## User Documentation

For user-facing documentation (installation, commands, examples), see the [GitHub Pages site](https://vedanta.github.io/ui-cli).

The source for GitHub Pages is in the `/pages` directory.

## Design Documents

Design documents for new features are in the `/design` directory:

- [client-groups.md](/design/client-groups.md) - Client groups feature design
- [client-groups-implementation.md](/design/client-groups-implementation.md) - Implementation plan

## Directory Structure

```
ui-cmd/
├── docs/           # Project documentation (this directory)
├── pages/          # GitHub Pages source (mkdocs)
├── design/         # Feature design documents
├── src/            # Source code
│   ├── ui_cli/     # CLI application
│   └── ui_mcp/     # MCP server
└── scripts/        # Utility scripts
```
