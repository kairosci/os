#!/bin/bash
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin" "$work/home/.config/systemd/user/graphical-session.target.wants" \
  "$work/home/.config/arch/hooks/theme-set.d"
printf '#!/bin/bash\n# owe theme-set hook\nSOCK=\"/owe/owed.sock\"\n' >"$work/home/.config/arch/hooks/theme-set.d/10-owe-sync"
ln -s /usr/lib/systemd/user/owed.service "$work/home/.config/systemd/user/graphical-session.target.wants/owed.service"

cat >"$work/bin/systemctl" <<'STUB'
#!/bin/bash
printf 'systemctl %s\n' "$*" >>"$TEST_CALLS"
STUB
cat >"$work/bin/arch-pkg-drop" <<'STUB'
#!/bin/bash
printf 'arch-pkg-drop %s\n' "$*" >>"$TEST_CALLS"
STUB
chmod +x "$work/bin/systemctl" "$work/bin/arch-pkg-drop"
export TEST_CALLS="$work/calls"
HOME="$work/home" PATH="$work/bin:$PATH" bash -euo pipefail "$ROOT/migrations/1789764927.sh"
grep -Fx 'arch-pkg-drop owe owe-lockfeed' "$TEST_CALLS" >/dev/null
[[ ! -e $work/home/.config/systemd/user/graphical-session.target.wants/owed.service ]]
[[ ! -e $work/home/.config/arch/hooks/theme-set.d/10-owe-sync ]]
pass "migration removes the retired renderer, service link, and theme hook"

: >"$TEST_CALLS"
HOME="$work/home" PATH="$work/bin:$PATH" bash -euo pipefail "$ROOT/migrations/1789764927.sh"
grep -Fx 'arch-pkg-drop owe owe-lockfeed' "$TEST_CALLS" >/dev/null
pass "renderer removal is safe to repeat"
