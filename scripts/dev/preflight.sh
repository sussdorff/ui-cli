#!/usr/bin/env bash
# Repository preflight, run by the pre-push hook (core.hooksPath) before a push.
# Checks toolchain declarations against the library-core toolchains standard.
set -euo pipefail

# A hook inherits GIT_DIR (absolute in a linked worktree) and, via `git hook run`,
# GIT_WORK_TREE=. ; both would redirect repository discovery and the checker's
# `git ls-files`. Drop them so git discovers the repository from this script's path.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR GIT_PREFIX

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && git rev-parse --show-toplevel)"
cd "$repo_root"

status=0
python3 .agents/standards/toolchains/scripts/check_toolchain_versions.py || status=$?
exit "$status"
