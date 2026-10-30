#!/usr/bin/env bash
# init.sh — BUILDER-OS bootstrap + verify gate for fcar-local.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(dirname "$ROOT_DIR")}"
cd "$PROJECT_ROOT"
VERIFY_CMD=".venv/bin/python -m pytest -q"
START_CMD=".venv/bin/python fcar_check.py --help"
echo "== verify =="; $VERIFY_CMD
echo "INIT OK"
