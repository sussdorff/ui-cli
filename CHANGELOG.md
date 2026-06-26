# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed


- **firewall:** Migrate to zone-based policy API

## [2.1.0] - 2026-06-26

### Added


- Green - add firewall rule creation


### Tests


- Red - cover firewall rule creation

## [2.0.0] - 2026-04-16

### chore


- Remove legacy MCP server

## [1.2.1] - 2026-04-16

### chore


- **gitignore:** Ignore local backup artifacts

## [1.2.0] - 2026-04-15

### chore


- Update changelog for API key auth (1.2.0)

- Bump version to 1.2.0


### merge


- Worktree-bead-ui-cli-a4b

## [1.1.1] - 2026-04-15

### Added


- **ui-cli-a4b:** Green — UniFi API key authentication (AK1-AK6)


### Documentation


- Update feature documentation for ui-cli-a4b — API key auth


### Fixed


- **ui-cli-a4b:** Address review findings iteration 1 — API prefix in key mode, test assertions

- **ui-cli-a4b:** Address review findings iteration 2 — v2 AK3 test, extract error constant, rename _ensure_cookies_loaded

- **ui-cli-a4b:** Clear error when API key used against non-UDM controller (404/405)

- **ui-cli-a4b:** Legacy-controller fallback, status API-key support, remove v2 404-remapping


### Tests


- **ui-cli-a4b:** Red — API key authentication test class AK1-AK6


### chore


- **beads:** Update dolt backup state after remote sync

- Bump version to 1.1.1

## [1.1.0] - 2026-04-15

### Added


- **cli:** Improve wrapper script config loading and venv support

- **cli:** Add AP groups management, refactor WLAN commands

- **clients:** Add set-ip command for DHCP reservations

- **clients:** Add rename command for setting client display names

- **networks:** Add update command for DHCP range configuration

- **wan:** Add WAN DNS management and extend LAN networks DNS options


### Documentation


- Add CLAUDE.md project instructions and UniFi API reference submodule

- Add X-Sense security range (40-44) to IoT IP schema

- Add X-Sense Base Station AirBnB (.41)


### bd


- Backup 2026-03-02 16:52


### chore


- Ignore uv.lock

- Bump version to 1.1.0

## [1.0.0] - 2025-12-04

### Added


- Add client groups for bulk actions


### Documentation


- Rewrite README for clarity and structure

- Comprehensive README rewrite


### Fixed


- Update docs workflow to use pages/ directory

- Correct Client Groups doc link in README


### release


- V1.0.0 "Glazed"

## [0.3.0] - 2025-12-03

### Added


- Add Docker container support

- Add MCP server for Claude Desktop integration

- Add ./ui mcp command for Claude Desktop integration

- Implement MCP server v2 with tools layer

- Add quick timeout and spinners for local commands


### Changed


- Prepare for MCP server v2


### Documentation


- Add GitHub Pages documentation site

- Compact landing page to avoid scroll

- Redesign landing page with 2-column layout

- Reduce element sizes and fix install command

- Add MCP server documentation

- Add MCP server documentation to main docs


### Fixed


- Add mcp package check to install/check commands

- Set cwd to project root so .env file is found

- Use wrapper script to load .env for MCP server

- Use sys.executable instead of ./ui wrapper in CLI runner

- Network_list command and add MCP tools test script


### chore


- Bump version to 0.3.0


### wip


- MCP server v1 - disabled list_clients due to output issues

## [0.2.0] - 2025-12-01

### Added


- Complete Milestone 2 Local Controller API implementation


### Documentation


- Rewrite user guide for clarity and completeness

- Update README with new mascot art

- Finalize repository documentation

- Add detailed features list to README

- Add Mermaid command tree diagram to README

- Replace Mermaid diagram with collapsible ASCII trees


### chore


- Bump version to 0.2.0 and add release notes


### style


- Fix import order in test file

