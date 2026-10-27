#!/bin/bash

set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/base-test.sh"

stub_dir=$(mktemp -d)
trap 'rm -rf "$stub_dir"' EXIT

cat >"$stub_dir/ufw" <<'STUB'
#!/bin/bash
printf 'ufw %s\n' "$*" >>"$TEST_LOG"
if [[ ${1:-} == status ]]; then
  echo 'Status: inactive'
fi
STUB

cat >"$stub_dir/ufw-docker" <<'STUB'
#!/bin/bash
set -euo pipefail
PATH="/bin:/usr/bin:/sbin:/usr/sbin:/snap/bin/"
printf 'ufw-docker %s\n' "$*" >>"$TEST_LOG"
if ! ufw status 2>/dev/null | grep -Fq 'Status: active'; then
  echo 'inactive' >&2
  exit 1
fi
STUB

cat >"$stub_dir/systemctl" <<'STUB'
#!/bin/bash
printf 'systemctl %s\n' "$*" >>"$TEST_LOG"
STUB

chmod +x "$stub_dir"/*

export TEST_LOG="$stub_dir/firewall.log"
printf 'ENABLED=no\n' >"$stub_dir/ufw.conf"
ARCH_PATH="$ROOT" ARCH_UFW_CONFIG="$stub_dir/ufw.conf" PATH="$stub_dir:$PATH" \
  python3 -I "$ROOT/src/python/installer/system_setup/firewall.py"

grep -q '^ufw-docker install$' "$TEST_LOG" || fail "ufw-docker rules are installed"
grep -q '^systemctl enable ufw$' "$TEST_LOG" || fail "ufw is enabled for next boot"

pass "firewall config installs ufw-docker rules without activating live UFW"
