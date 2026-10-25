#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

export PATH="$ROOT/src/cli:$PATH"

require_command jq
require_command lua
require_command python3

jq empty "$ROOT/config/arch/shell.json"
pass "default shell.json is valid JSON"

jq -e '.version == 1 and ([.bar.layout[("left", "centerBegin", "center", "centerEnd", "right")] | type == "array"] | all)' "$ROOT/config/arch/shell.json" >/dev/null
pass "default shell.json has versioned bar layout"

# The center box holds only the clock, so it stays dead center while the
# widgets either side of it come and go.
jq -e '
  def ids: map(.id // .);
  (.bar | has("centerAnchor") | not) and (.bar.layout.center | ids) == ["arch.clock"]
' "$ROOT/config/arch/shell.json" >/dev/null
pass "default center box holds just the clock"

jq -e '
  def ids: map(.id // .);
  (.bar.layout.centerBegin | ids | index("arch.indicators")) != null
' "$ROOT/config/arch/shell.json" >/dev/null
pass "default indicators sit before the center box"

# Pinning the whole row made this fail every time an unrelated widget moved,
# so assert the adjacency the name is about and let the rest of the row change.
jq -e '
  def ids: map(.id // .);
  (.bar.layout.centerEnd | ids) as $ids |
  ($ids | index("arch.weather")) as $weather |
  ($ids | index("arch.system-update")) as $update |
  $weather != null and $update == $weather + 1
' "$ROOT/config/arch/shell.json" >/dev/null
pass "default center layout keeps update next to weather"

jq -e '
  def ids: map(.id // .);
  (.bar.layout.centerEnd | ids) as $ids |
  ($ids | index("arch.elsewhen")) as $elsewhen |
  ($ids | index("arch.weather")) as $weather |
  $elsewhen == 0 and $weather > $elsewhen
' "$ROOT/config/arch/shell.json" >/dev/null
pass "default center layout puts elsewhen immediately after the clock and before weather"

# Every CLI write goes through the normalizer, which keeps every bar section a
# list, the ones beside the center box included.
normalized=$(ARCH_PATH="$ROOT" bash -c 'source "$ARCH_PATH/src/cli/arch-shell-config" && jq -c "$NORMALIZE | .bar.layout" <<<"{\"bar\":{\"layout\":{\"centerBegin\":null}}}"')
[[ $normalized == '{"centerBegin":[],"left":[],"center":[],"centerEnd":[],"right":[]}' ]] ||
  fail "shell config normalizer keeps every bar section a list" "$normalized"
pass "shell config normalizer keeps every bar section a list"

# A service widget defaulting to centerEnd goes after the weather.
grep -qF 'def anchor_for(\$section): { left: \"arch.workspaces\", centerEnd: \"arch.weather\", right: \"arch.tray\" }[\$section];' "$ROOT/src/cli/arch-bar" ||
  fail "bar defaults anchors centerEnd widgets after the weather"
pass "bar defaults anchors centerEnd widgets after the weather"

jq -e '
  any(.bar.layout.center[]; (.id // .) == "arch.clock" and (.formatAlt // "") == "d MMMM \u0027W\u0027ww yyyy")
' "$ROOT/config/arch/shell.json" >/dev/null
pass "default clock date format has no leading zero"

# The bar drew the tray first in the right section whatever the layout said
# (migrations/1791968925.sh), so the default lists it there. Agents follow it,
# past only the keyboard layout, which hides itself with a single layout.
jq -e '
  def ids: map(.id // .);
  (.bar.layout.right | ids) as $ids |
  ($ids | index("arch.agents")) as $agents |
  $ids[0] == "arch.tray" and $agents != null and ($ids[1:$agents] - ["arch.keyboard-layout"]) == []
' "$ROOT/config/arch/shell.json" >/dev/null || fail "default right layout starts with the tray, with agents beside it"
pass "default right layout starts with the tray, with agents beside it"

ROOT="$ROOT" python3 <<'PY'
import json
import os
import sys
from pathlib import Path

root = Path(os.environ["ROOT"])
config = json.loads((root / "config/arch/shell.json").read_text())
manifests = {}
for manifest_path in (root / "src/shell/plugins").glob("**/*.manifest.json"):
  data = json.loads(manifest_path.read_text())
  manifests[data.get("id", "")] = (manifest_path, data)
for manifest_path in (root / "src/shell/plugins").glob("**/manifest.json"):
  data = json.loads(manifest_path.read_text())
  manifests[data.get("id", "")] = (manifest_path, data)

entries = []
for section in ("left", "centerBegin", "center", "centerEnd", "right"):
  entries.extend(config["bar"]["layout"][section])

missing = []
bad = []
for entry in entries:
  widget_id = entry["id"] if isinstance(entry, dict) else str(entry)
  if not widget_id.startswith("arch."):
    continue

  row = manifests.get(widget_id)
  if row is None:
    missing.append(widget_id)
    continue
  manifest_path, manifest = row

  if "bar-widget" not in manifest.get("kinds", []):
    bad.append(f"{widget_id}: missing bar-widget kind")
  entry_point = manifest.get("entryPoints", {}).get("barWidget")
  if not entry_point:
    bad.append(f"{widget_id}: missing barWidget entry point")
  elif not (manifest_path.parent / entry_point).exists():
    bad.append(f"{widget_id}: missing {entry_point}")

if missing or bad:
  for item in missing:
    print(f"missing manifest for {item}", file=sys.stderr)
  for item in bad:
    print(item, file=sys.stderr)
  sys.exit(1)
PY
pass "default bar widget ids resolve to manifests and entry points"

# The PKGBUILDs live in the arch-pkgs checkout, wherever this machine keeps it.
if find_arch_pkgs; then
  ROOT="$ROOT" ARCH_PKGS_ROOT="$ARCH_PKGS_ROOT" python3 <<'PY'
import os
import re
import sys
from pathlib import Path

root = Path(os.environ["ROOT"])
pkgs_root = Path(os.environ["ARCH_PKGS_ROOT"])
settings_pkgbuild_path = pkgs_root / "arch-settings/PKGBUILD"
arch_pkgbuild_path = pkgs_root / "arch/PKGBUILD"
if not settings_pkgbuild_path.exists():
  settings_pkgbuild_path = pkgs_root / "arch-settings-dev/PKGBUILD"
if not arch_pkgbuild_path.exists():
  arch_pkgbuild_path = pkgs_root / "arch-dev/PKGBUILD"
pkgbuild = settings_pkgbuild_path.read_text()
arch_pkgbuild = arch_pkgbuild_path.read_text()
errors = []
package_defaults = [
  ("default/uwsm/env.d/10-arch", "/usr/share/uwsm/env.d/10-arch", "uwsm/env"),
  ("default/uwsm/default", None, "uwsm/default"),
  ("default/environment.d/10-arch-fcitx.conf", "/usr/lib/environment.d/10-arch-fcitx.conf", "environment.d/fcitx.conf"),
  ("default/fontconfig/conf.avail/50-arch.conf", "/usr/share/fontconfig/conf.avail/50-arch.conf", "fontconfig/fonts.conf"),
  ("default/xdg-terminal-exec/hyprland-xdg-terminals.list", "/usr/share/xdg-terminal-exec/hyprland-xdg-terminals.list", "xdg-terminals.list"),
  ("default/applications/mimeapps.list", "/usr/share/applications/mimeapps.list", "mimeapps.list"),
  ("etc/fastfetch/config.jsonc", "/etc/fastfetch/config.jsonc", "fastfetch/config.jsonc"),
  ("default/systemd/user/bt-agent.service", "/usr/lib/systemd/user/bt-agent.service", "systemd/user/bt-agent.service"),
  ("default/systemd/user/arch-sleep-lock.service", "/usr/lib/systemd/user/arch-sleep-lock.service", "systemd/user/arch-sleep-lock.service"),
  ("default/systemd/user/arch-recover-internal-monitor.service", "/usr/lib/systemd/user/arch-recover-internal-monitor.service", "systemd/user/arch-recover-internal-monitor.service"),
  ("default/systemd/user/arch-migrate-notify.service", "/usr/lib/systemd/user/arch-migrate-notify.service", "systemd/user/arch-migrate-notify.service"),
  ("default/systemd/user/arch-tailscale-receive.service", "/usr/lib/systemd/user/arch-tailscale-receive.service", "systemd/user/arch-tailscale-receive.service"),
  ("default/systemd/user/arch-fcitx5.service", "/usr/lib/systemd/user/arch-fcitx5.service", "systemd/user/arch-fcitx5.service"),
  ("default/systemd/user/arch-crash-watch.service", "/usr/lib/systemd/user/arch-crash-watch.service", "systemd/user/arch-crash-watch.service"),
  ("default/systemd/zram-generator.conf.d/90-arch.conf", "/usr/lib/systemd/zram-generator.conf.d/90-arch.conf", "systemd/zram-generator.conf.d/90-arch.conf"),
  ("default/systemd/timesyncd.conf.d/10-arch.conf", "/usr/lib/systemd/timesyncd.conf.d/10-arch.conf", "systemd/timesyncd.conf.d/10-arch.conf"),
  ("default/systemd/system/plocate-updatedb.service.d/10-arch.conf", "/usr/lib/systemd/system/plocate-updatedb.service.d/10-arch.conf", "systemd/system/plocate-updatedb.service.d/10-arch.conf"),
  ("default/fonts/arch/arch.ttf", "/usr/share/fonts/arch/arch.ttf", "arch.ttf"),
  ("default/snapper/root", "/etc/snapper/config-templates/arch", "snapper/root"),
]

for source, destination, legacy in package_defaults:
  if not (root / source).exists():
    errors.append(f"missing package default source: {source}")
  if (root / "config" / legacy).exists():
    errors.append(f"legacy path still in config/: {legacy}")
  if destination and (source not in pkgbuild or destination not in pkgbuild):
    errors.append(f"PKGBUILD does not explicitly install {source} -> {destination}")

# A user unit has to be on the machine before anything turns it on: shipped in
# /usr/lib/systemd/user, or copied out of default/ by the command enabling it.
def installs_first(text):
  source = re.search(r'(\w+)="[^"\n]*default/systemd/user/', text)
  held = rf"|\$\{{?{source[1]}\b" if source else ""
  copy = re.search(rf"^[ \t]*(?:sudo[ \t]+)?(?:install|cp)\b[^\n]*(?:default/systemd/user/{held})", text, re.MULTILINE)
  enable = text.find("systemctl --user enable")
  return bool(copy) and (enable < 0 or copy.start() < enable)

named = 'unit="$ARCH_PATH/default/systemd/user/a.service"\n'
if installs_first(named + "systemctl --user enable a.service\n"):
  errors.append("unit check accepts a command that names a unit's source but never installs it")
if installs_first(named + 'systemctl --user enable a.service\ninstall -Dm644 "$unit" "$target"\n'):
  errors.append("unit check accepts a command that installs a unit after enabling it")

scripts = [path.read_text(errors="ignore") for folder in ("bin", "installer", "migrations")
           for path in (root / folder).rglob("*") if path.is_file()]
for unit in sorted(path.name for path in (root / "default/systemd/user").glob("*.service")):
  if f"/usr/lib/systemd/user/{unit}" in pkgbuild:
    continue
  named = [text for text in scripts if unit in text]
  if not any(installs_first(text) for text in named):
    errors.append(f"PKGBUILD does not ship default/systemd/user/{unit} and no command installs it")
  elif any("systemctl --user enable" in text and not installs_first(text) for text in named):
    errors.append(f"{unit} is enabled without being shipped by PKGBUILD or installed first")

# Existing users have an absolute wants symlink to the old unit path, and the
# migration that repoints it only runs for users who run an update -- the
# opposite of who the notifier is for. Dropping this alias strands them.
notify_alias = 'ln -sfn arch-migrate-notify.service "$pkgdir/usr/lib/systemd/user/arch-update-user-notify.service"'
if notify_alias not in pkgbuild:
  errors.append(
    "PKGBUILD does not ship the arch-update-user-notify.service compatibility "
    "alias, so users who have not run migration 1785095882 lose the login notifier"
  )

alpm_hooks = [
  "00-arch-update-guard.hook",
  "10-arch-hyprland-reload-pause.hook",
  "90-arch-hyprland-reload-resume.hook",
]
for hook in alpm_hooks:
  source = f"default/libalpm/hooks/{hook}"
  destination = f"/usr/share/libalpm/hooks/{hook}"
  if not (root / source).exists():
    errors.append(f"missing package default source: {source}")
  if source not in arch_pkgbuild or destination not in arch_pkgbuild:
    errors.append(f"arch PKGBUILD does not install {source} -> {destination}")

if errors:
  print("\n".join(errors), file=sys.stderr)
  sys.exit(1)
PY
  pass "package-owned defaults live outside config"
else
  skip "package-owned defaults live outside config: needs the arch-pkgs checkout; set ARCH_PKGS_PATH to it"
fi

grep -Fq 'pre_upgrade() {' "$ROOT/packages/arch/arch-branding.install" &&
  grep -Fq 'arch-hyprland-reload-guard pause' "$ROOT/packages/arch/arch-branding.install" &&
  grep -Fq 'arch-hyprland-reload-guard resume' "$ROOT/packages/arch/arch-branding.install" ||
  fail "Arch package upgrades pause Hyprland config reload until the payload is replaced"

grep -F 'dofile((os.getenv("ARCH_PATH") or "/usr/share/arch") .. "/default/hypr/bootstrap.lua")' "$ROOT/config/hypr/hyprland.lua" >/dev/null
grep -F 'require("default.hypr.arch")' "$ROOT/config/hypr/hyprland.lua" >/dev/null
grep -F 'package.path = home' "$ROOT/default/hypr/bootstrap.lua" >/dev/null
grep -F '/.local/state/?.lua;' "$ROOT/default/hypr/bootstrap.lua" >/dev/null
pass "Hyprland user entrypoint keeps package and state path bootstrap in defaults"

ARCH_PATH="$ROOT" lua <<'LUA'
package.loaded["default.hypr.arch"] = true
package.loaded["default.hypr.require_optional"] = true
package.loaded["hypr.looknfeel"] = true
package.loaded["arch.current.theme.hyprland"] = true
package.loaded["unrelated.module"] = true

dofile(os.getenv("ARCH_PATH") .. "/default/hypr/bootstrap.lua")

assert(package.loaded["default.hypr.arch"] == nil)
assert(package.loaded["default.hypr.require_optional"] == nil)
assert(package.loaded["hypr.looknfeel"] == nil)
assert(package.loaded["arch.current.theme.hyprland"] == nil)
assert(package.loaded["unrelated.module"] == true)
LUA
pass "Hyprland bootstrap reloads cached os config modules"

TMPDIR=$(mktemp -d)
test_arch_root="$TMPDIR/arch-root"
mkdir -p "$test_arch_root"
for entry in config default etc migrations version; do
  [[ -e $ROOT/$entry ]] && ln -s "$ROOT/$entry" "$test_arch_root/$entry"
done
mkdir -p "$test_arch_root/src"
ln -s "$ROOT/src/cli" "$test_arch_root/src/cli"
ln -s "$ROOT/installer" "$test_arch_root/installer"
ln -s "$ROOT/src/shell" "$test_arch_root/src/shell"
mkdir -p "$test_arch_root/assets"
ln -s "$ROOT/assets/themes" "$test_arch_root/assets/themes"
ln -s "$ROOT/assets/applications" "$test_arch_root/assets/applications"
mkdir -p "$test_arch_root/assets/branding"
for entry in arch-mark.svg arch-symbol.png icon.txt logo.txt logo.svg; do
  ln -s "$ROOT/assets/branding/$entry" "$test_arch_root/assets/branding/$entry"
done
mkdir -p "$TMPDIR/home/.config/arch"
# The bar keeps its blur toggle where Hyprland reads it, under XDG_STATE_HOME,
# so that points into the test home too.
export XDG_STATE_HOME="$TMPDIR/home/.local/state"

ipc_mock_bin="$TMPDIR/ipc-mock"
mkdir -p "$ipc_mock_bin"
cat >"$ipc_mock_bin/arch-shell" <<'SH'
#!/bin/bash
set -euo pipefail

mkdir -p "$HOME/.local/state/arch"
printf '%s\n' "$*" >>"$HOME/.local/state/arch/shell-ipc-calls"
printf 'ok\n'
SH
chmod +x "$ipc_mock_bin/arch-shell"
export PATH="$ipc_mock_bin:$PATH"

cat >"$TMPDIR/home/.config/arch/shell.json" <<'JSON'
{
  "version": 1,
  "bar": {
    "layout": {
      "left": [{ "id": "arch.menu" }, { "id": "arch.workspaces" }, { "id": "arch.active-window" }],
      "center": [{ "id": "arch.clock" }, { "id": "arch.weather" }, { "id": "arch.system-update" }, { "id": "arch.tailscale" }],
      "right": [{ "id": "arch.tray" }, { "id": "arch.microphone" }, { "id": "arch.bluetooth" }]
    }
  },
  "plugins": []
}
JSON

mkdir -p "$TMPDIR/home/.config/arch/plugins/local.demo-bar"
cat >"$TMPDIR/home/.config/arch/plugins/local.demo-bar/manifest.json" <<'JSON'
{
  "schemaVersion": 1,
  "id": "local.demo-bar",
  "name": "Demo bar",
  "version": "1.0.0",
  "author": "Test",
  "description": "Replacement bar for config tests",
  "kinds": ["bar"],
  "entryPoints": { "bar": "Bar.qml" }
}
JSON
touch "$TMPDIR/home/.config/arch/plugins/local.demo-bar/Bar.qml"

if HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar use local.nonexistent-bar 2>/dev/null; then
  fail "bar use accepted an unknown bar option"
fi
pass "bar use rejects an unknown bar option"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar use local.demo-bar
jq -e '.bar.id == "local.demo-bar"' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
pass "shell config selects a bar option"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar reset
jq -e '.bar.id == null' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
pass "shell config resets to built-in bar option"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar move arch.active-window right
grep -Fqx 'shell moveBarWidget arch.active-window {"section":"right"}' \
  "$TMPDIR/home/.local/state/arch/shell-ipc-calls"
pass "bar move accepts a positional target section"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar move arch.active-window left
grep -Fqx 'shell moveBarWidget arch.active-window {"section":"left"}' \
  "$TMPDIR/home/.local/state/arch/shell-ipc-calls"
pass "bar move can restore a widget with positional syntax"

if HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar move arch.active-window left --section right 2>/dev/null; then
  fail "bar move accepted positional and flagged target sections"
fi
pass "bar move rejects conflicting target section syntax"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar position bottom
jq -e '
  .bar.position == "bottom" and
  .plugins == []
' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
pass "shell config sets bar position"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar transparent true
jq -e '
  .bar.background == "none" and
  .bar.position == "bottom" and
  .plugins == []
' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
pass "shell config sets bar transparency"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar transparent toggle
jq -e '.bar.background == "opaque"' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
pass "shell config toggles bar transparency"

# The bar background is opaque, glassy or none. A glassy bar needs Hyprland's
# blur, so the bar-glassy toggle follows it.
printf '#!/bin/bash\nprintf "%%s\\n" "$*" >>"%s/hyprctl.log"\n' "$TMPDIR" >"$ipc_mock_bin/hyprctl"
chmod +x "$ipc_mock_bin/hyprctl"
glass_toggle="$TMPDIR/home/.local/state/arch/toggles/hypr/bar-glassy.lua"
bar_background() { HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar background "$@"; }

bar_background opaque >/dev/null
[[ $(bar_background) == "opaque" ]] || fail "an opaque bar background is reported"
bar_background glassy >/dev/null
jq -e '.bar.background == "glassy"' "$TMPDIR/home/.config/arch/shell.json" >/dev/null ||
  fail "shell config sets a glassy bar"
[[ $(bar_background) == "glassy" ]] || fail "a glassy bar background is reported"
[[ -f $glass_toggle ]] || fail "a glassy bar turns on Hyprland's blur behind it"
grep -qx 'reload' "$TMPDIR/hyprctl.log" || fail "a glassy bar reloads Hyprland"
bar_background none >/dev/null
jq -e '.bar.background == "none"' "$TMPDIR/home/.config/arch/shell.json" >/dev/null ||
  fail "a bar without a background is stored as none"
[[ ! -f $glass_toggle ]] || fail "a bar without a background turns Hyprland's blur off again"
pass "shell config sets the bar background, and Hyprland's blur follows a glassy one"

seen=()
for _ in 1 2 3; do
  bar_background cycle >/dev/null
  seen+=("$(bar_background)")
done
[[ ${seen[*]} == "glassy opaque none" ]] || fail "the bar background cycles from clear to glassy to opaque and around" "${seen[*]}"
if bar_background frosted 2>/dev/null; then
  fail "an unknown bar background is refused"
fi
: >"$TMPDIR/hyprctl.log"
bar_background opaque >/dev/null
[[ ! -s $TMPDIR/hyprctl.log ]] || fail "Hyprland reloads only when the bar's glass changes"
pass "the bar background cycles through its looks and refuses unknown ones"

# transparent stays for scripts written against it: true is none, false opaque.
bar_background glassy >/dev/null
HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar transparent true >/dev/null
[[ $(bar_background) == "none" ]] || fail "transparent true leaves the bar without a background"
HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar transparent toggle >/dev/null
[[ $(bar_background) == "opaque" ]] || fail "toggling transparency off makes the bar opaque"
# A shell.json from before background says transparent, which reads as none
# and is dropped once a background is set.
jq '.bar.transparent = true | del(.bar.background)' "$TMPDIR/home/.config/arch/shell.json" >"$TMPDIR/legacy.json" &&
  mv "$TMPDIR/legacy.json" "$TMPDIR/home/.config/arch/shell.json"
[[ $(bar_background) == "none" ]] || fail "an older transparent bar reads as no background"
bar_background glassy >/dev/null
jq -e '.bar.background == "glassy" and (.bar | has("transparent") | not)' "$TMPDIR/home/.config/arch/shell.json" >/dev/null ||
  fail "setting a background drops the older transparent flag"
pass "the older transparent form still sets and reads as the bar background"

# Restoring the default bar also restores its glassy background and its blur.
bar_background glassy >/dev/null
[[ -f $glass_toggle ]] || fail "a glassy bar has its blur on before defaults"
HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar defaults >/dev/null
[[ $(bar_background) == "glassy" && -f $glass_toggle ]] || fail "archctl bar defaults restores the glassy background"
pass "restoring the default bar restores its glassy background"

# A background set by editing shell.json gets its blur when the shell syncs it.
jq '.bar.background = "glassy"' "$TMPDIR/home/.config/arch/shell.json" >"$TMPDIR/edited.json" &&
  mv "$TMPDIR/edited.json" "$TMPDIR/home/.config/arch/shell.json"
HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar sync-glass
[[ -f $glass_toggle ]] || fail "syncing a hand-edited glassy bar turns its blur on"
jq '.bar.background = "opaque"' "$TMPDIR/home/.config/arch/shell.json" >"$TMPDIR/edited.json" &&
  mv "$TMPDIR/edited.json" "$TMPDIR/home/.config/arch/shell.json"
HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar sync-glass
[[ ! -f $glass_toggle ]] || fail "syncing a hand-edited opaque bar turns its blur off"
pass "a bar background edited into shell.json gets its blur synced"

# A glassy bar whose blur can't be turned on keeps the background it had.
toggles_dir="${glass_toggle%/*}"
chmod a-w "$toggles_dir"
if bar_background glassy >/dev/null 2>&1; then
  chmod u+w "$toggles_dir"
  fail "a bar whose blur can't be turned on reports failure"
fi
chmod u+w "$toggles_dir"
[[ $(bar_background) == "opaque" && ! -f $glass_toggle ]] || fail "a bar whose blur can't be turned on keeps its old background" "$(bar_background)"
pass "a bar whose blur can't change keeps its old background"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar set arch.bluetooth enabled false --json
grep -Fqx 'shell setBarWidget arch.bluetooth enabled false {}' \
  "$TMPDIR/home/.local/state/arch/shell-ipc-calls"
pass "bar set accepts false JSON values"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar set arch.bluetooth optional null --json
grep -Fqx 'shell setBarWidget arch.bluetooth optional null {}' \
  "$TMPDIR/home/.local/state/arch/shell-ipc-calls"
pass "bar set accepts null JSON values"

if HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar set arch.bluetooth broken '{' --json 2>/dev/null; then
  fail "bar set accepted malformed JSON"
fi
pass "bar set rejects malformed JSON"

if HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" arch-bar set arch.bluetooth broken 'false null' --json 2>/dev/null; then
  fail "bar set accepted multiple JSON values"
fi
pass "bar set rejects multiple JSON values"

mock_bin="$TMPDIR/mock-bin"
mkdir -p "$mock_bin"

cat >"$mock_bin/arch-refresh-config" <<'SH'
#!/bin/bash
set -euo pipefail

relative_path="${1:-}"
[[ -n $relative_path ]] || exit 1
mkdir -p "$HOME/.config/$(dirname "$relative_path")"
cp "$ARCH_PATH/config/$relative_path" "$HOME/.config/$relative_path"
SH

cat >"$mock_bin/arch-restart-shell" <<'SH'
#!/bin/bash
set -euo pipefail

mkdir -p "$HOME/.local/state/arch"
touch "$HOME/.local/state/arch/restart-shell-called"
SH

cat >"$mock_bin/arch-shell" <<'SH'
#!/bin/bash
[[ ${ARCH_TEST_SHELL_DOWN:-0} == "1" ]] && exit 1
printf 'ok\n'
SH

cat >"$mock_bin/arch-installed-service-dropbox" <<'SH'
#!/bin/bash
set -euo pipefail

[[ ${ARCH_TEST_DROPBOX:-0} == "1" ]]
SH

cat >"$mock_bin/arch-installed-service-tailscale" <<'SH'
#!/bin/bash
set -euo pipefail

[[ ${ARCH_TEST_TAILSCALE:-0} == "1" ]]
SH

chmod +x "$mock_bin"/*
mock_path="$mock_bin:$ROOT/src/cli:$PATH"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" PATH="$mock_path" ARCH_TEST_DROPBOX=0 ARCH_TEST_TAILSCALE=0 arch-bar defaults
jq -e --slurpfile defaults "$ROOT/config/arch/shell.json" '
  .bar == $defaults[0].bar and
  .plugins == []
' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
pass "bar defaults restores the stock bar"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" PATH="$mock_path" ARCH_TEST_DROPBOX=1 ARCH_TEST_TAILSCALE=1 arch-bar defaults
jq -e '
  def ids: map(.id // .);
  (.bar.layout.right | ids) as $right |
  ($right | index("arch.tray")) as $tray |
  ($right | index("arch.tailscale") == $tray + 1) and
  ($right | index("arch.dropbox") == $tray + 2) and
  ([.bar.layout[]] | map(ids) | add | map(select(. == "arch.tailscale")) | length == 1)
' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
pass "bar defaults places plugins for running optional services"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" PATH="$mock_path" \
  ARCH_TEST_SHELL_DOWN=1 ARCH_TEST_DROPBOX=1 ARCH_TEST_TAILSCALE=1 \
  arch-bar defaults
jq -e '
  def ids: map(.id // .);
  (.bar.layout.right | ids) as $right |
  ($right | index("arch.tray")) as $tray |
  ($right | index("arch.tailscale") == $tray + 1) and
  ($right | index("arch.dropbox") == $tray + 2) and
  ([.bar.layout[]] | map(ids) | add | map(select(. == "arch.tailscale")) | length == 1)
' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
pass "bar defaults places service widgets without a running shell"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" PATH="$mock_path" ARCH_TEST_DROPBOX=0 ARCH_TEST_TAILSCALE=0 arch-refresh-shell
jq -e '
  def ids: map(.id // .);
  ([.bar.layout[]] | map(ids) | add) as $all |
  ($all | index("arch.dropbox") == null) and
  ($all | index("arch.tailscale") == null)
' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
pass "shell refresh keeps optional service widgets absent when services are unavailable"

HOME="$TMPDIR/home" ARCH_PATH="$test_arch_root" PATH="$mock_path" ARCH_TEST_DROPBOX=1 ARCH_TEST_TAILSCALE=1 arch-refresh-shell
jq -e '
  def ids: map(.id // .);
  (.bar.layout.right | ids) as $right |
  ($right | index("arch.tray")) as $tray |
  ($right | index("arch.tailscale") == $tray + 1) and
  ($right | index("arch.dropbox") == $tray + 2) and
  ([.bar.layout[]] | map(ids) | add | map(select(. == "arch.tailscale")) | length == 1)
' "$TMPDIR/home/.config/arch/shell.json" >/dev/null
[[ -f $TMPDIR/home/.local/state/arch/restart-shell-called ]] || fail "shell refresh restarts shell"
pass "shell refresh places optional service widgets when services are available"

if grep -RIl 'upgrade-to-quattro\|os 4\.0 is upgraded' "$ROOT/migrations" >/dev/null; then
  fail "4.0 upgrade is not modeled as a migration"
fi
pass "4.0 upgrade is handled outside the migration runner"
