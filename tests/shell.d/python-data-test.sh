#!/bin/bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/base-test.sh"
ARCH_PATH="$ROOT" python3 "$ROOT/tests/shell.d/python-data-checks.py"
