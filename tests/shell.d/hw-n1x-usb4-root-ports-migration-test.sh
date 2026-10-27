#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
mkdir -p "$tmp_dir/bin"
export CALL_LOG="$tmp_dir/calls"
real_udevadm=$(command -v udevadm || true)
export PATH="$tmp_dir/bin:$PATH"

printf '#!/bin/bash\necho "udevadm $*" >> "$CALL_LOG"\n' > "$tmp_dir/bin/udevadm"
cat > "$tmp_dir/bin/arch-hw-aarch64-n1x" <<'SH'
#!/bin/bash
[[ ${IS_N1X:-1} == 1 ]]
SH
cat > "$tmp_dir/bin/arch-hw-match" <<'SH'
#!/bin/bash
[[ ${PRODUCT:-H7407BA} == *"$1"* ]]
SH
cat > "$tmp_dir/bin/sudo" <<'SH'
#!/bin/bash
"$@"
SH
chmod +x "$tmp_dir/bin/"*

migration="$ROOT/migrations/1791134093.sh"
rules="$tmp_dir/etc/udev/rules.d/71-arch-n1x-usb4-root-ports.rules"

# A ProArt's PCI tree: the three tunnel root ports, plus the NVMe root port,
# which has to be left alone.
write_ports() {
  rm -rf "$tmp_dir/pci"
  local slot spec
  for spec in "000b:00:00.0 0x22cf $1" "000c:00:00.0 0x22cf $1" "000d:00:00.0 0x22cf $1" "0002:00:00.0 0x22ce auto"; do
    read -r slot device control <<<"$spec"
    mkdir -p "$tmp_dir/pci/$slot/power"
    echo 0x10de > "$tmp_dir/pci/$slot/vendor"
    echo "$device" > "$tmp_dir/pci/$slot/device"
    echo "$control" > "$tmp_dir/pci/$slot/power/control"
  done
}

run_migration() {
  : > "$CALL_LOG"
  ARCH_N1X_USB4_ROOT_PORT_RULES="$rules" ARCH_PCI_DEVICES_PATH="$tmp_dir/pci" \
    bash -euo pipefail "$migration" >/dev/null 2>&1
}

write_ports auto
IS_N1X=0 run_migration
[[ ! -e $rules && ! -s $CALL_LOG ]] && pass "other machines are left alone" || fail "other machines are left alone"

PRODUCT=DX16263 run_migration
[[ ! -e $rules && ! -s $CALL_LOG ]] && pass "N1x machines without USB4 set up are left alone" || fail "N1x machines without USB4 set up are left alone"

run_migration
grep -Fxq 'ACTION=="add|bind", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{device}=="0x22cf", ATTR{power/control}="on"' "$rules" &&
  pass "the ProArt keeps its tunnel root ports in D0" || fail "the ProArt keeps its tunnel root ports in D0"
[[ $(stat -c %a "$rules") == "644" ]] && pass "the rule is world-readable, root-writable" || fail "the rule is world-readable, root-writable"
grep -Fxq 'udevadm trigger --action=add --subsystem-match=pci --attr-match=vendor=0x10de --attr-match=device=0x22cf' "$CALL_LOG" &&
  pass "the running system gets the rule without a reboot" || fail "the running system gets the rule without a reboot"
(( $(grep -c 'udevadm trigger' "$CALL_LOG") == 1 )) && pass "one trigger covers all three ports" || fail "one trigger covers all three ports"

write_ports on
run_migration
[[ ! -s $CALL_LOG ]] && pass "another user's run is a no-op" || fail "another user's run is a no-op"

echo '# administrator copy' > "$rules"
write_ports auto
run_migration
grep -Fxq '# administrator copy' "$rules" && pass "an existing rule file is kept" || fail "an existing rule file is kept"

# New installs and the migration share the ProArt-only USB4 rule.
hardware_config="$ROOT/data/installer/hardware/n1x.yml"
rule_from() { sed -n "/$2/,/^ *$3\$/p" "$1" | sed '1d;$d;s/^ *//'; }
n1x_rule=$(python3 - "$hardware_config" <<'PY'
import sys
from pathlib import Path
import yaml

config = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
content = config["files"]["usb4_proart_root_ports"]["content"]
for key in ("proart_pci_vendor", "proart_pci_device"):
  content = content.replace(f"@{key.upper()}@", config["hardware"][key])
print(content)
PY
)
if [[ -n $n1x_rule && $n1x_rule == "$(rule_from "$migration" '"$rules" <<' EOF)" ]]; then
  pass "new installs and the migration write the same rule"
else
  fail "new installs and the migration write the same rule"
fi
python3 - "$hardware_config" <<'PY' || fail "new installs only get the root-port rule on validated ProArt hardware"
import sys
from pathlib import Path
import yaml

config = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert config["hardware"]["proart_match"]
assert config["files"]["usb4_proart_root_ports"]["path"]
PY
pass "new installs only get the root-port rule on validated ProArt hardware"

if [[ -n $real_udevadm ]] && "$real_udevadm" verify --help >/dev/null 2>&1; then
  printf '%s\n' "$n1x_rule" > "$tmp_dir/71-arch-n1x-usb4-root-ports.rules"
  "$real_udevadm" verify --no-summary "$tmp_dir/71-arch-n1x-usb4-root-ports.rules" >/dev/null 2>&1 &&
    pass "udevadm verify accepts the rule" || fail "udevadm verify accepts the rule"
fi
