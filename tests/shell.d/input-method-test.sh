#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

ARCH_PATH="$ROOT" python "$ROOT/tests/shell.d/input-method-checks.py"
