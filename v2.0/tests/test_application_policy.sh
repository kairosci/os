#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/test_lib.sh"

test_section "Single Application Policy and OnlyOffice"
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT
export HOME="$SANDBOX/home"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_STATE_HOME="$HOME/.local/state"
export OMARCHY_PATH="$SANDBOX/omarchy"
export OS_LANG=en
mkdir -p "$OMARCHY_PATH/themes" "$XDG_CONFIG_HOME/onlyoffice" "$XDG_CONFIG_HOME/micro" "$XDG_CONFIG_HOME/gdu" "$XDG_CONFIG_HOME/omarchy/hooks/theme-set.d"
printf '[General]\neditorWindowMode=true\nappdata=personal-account\n[Personal]\nkeep=1\n' > "$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf"
printf 'personal\n' > "$XDG_CONFIG_HOME/micro/settings.json"
printf 'personal\n' > "$XDG_CONFIG_HOME/gdu/gdu.yaml"
cat > "$HOME/.bashrc" <<'RC'
export PERSONAL=1
# >>> os micro >>>
function mh() { printf old; }
# <<< os micro <<<
# >>> os disk >>>
function dh() { printf old; }
# <<< os disk <<<
RC
for hook in micro-theme disk-theme btop-theme gtk-theme; do
    printf 'personal\n' > "$XDG_CONFIG_HOME/omarchy/hooks/theme-set.d/$hook"
done

assert_true "OnlyOffice configuration installs" "lua -E '$PROJECT_DIR/src/main.lua' '$PROJECT_DIR' apply-settings onlyoffice"
assert_file_contains_literal "OnlyOffice keeps personal account data" "$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf" 'appdata=personal-account'
assert_file_contains_literal "OnlyOffice keeps unrelated preferences" "$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf" 'keep=1'
assert_file_contains_literal "OnlyOffice uses tabbed editing" "$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf" 'editorWindowMode=false'
assert_file_contains_literal "OnlyOffice uses the native custom title bar" "$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf" 'titlebar=custom'
assert_file_exists "OnlyOffice backs up previous preferences" "$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf.bak"
assert_true "OnlyOffice preferences remain private" "[[ \$(stat -c %a '$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf') == 600 ]]"
assert_true "OnlyOffice backups remain private" "[[ \$(stat -c %a '$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf.bak') == 600 ]]"
before=$(sha256sum "$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf")
chmod 644 "$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf.bak"
assert_true "OnlyOffice configuration is idempotent" "lua -E '$PROJECT_DIR/src/main.lua' '$PROJECT_DIR' apply-settings onlyoffice; [[ \"\$(sha256sum '$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf')\" == '$before' ]]"
assert_true "idempotent installation reconciles backup privacy" "[[ \$(stat -c %a '$XDG_CONFIG_HOME/onlyoffice/DesktopEditors.conf.bak') == 600 ]]"

assert_true "desktop migration installs" "lua -E '$PROJECT_DIR/src/main.lua' '$PROJECT_DIR' apply-settings desktop"
assert_file_contains_literal "desktop migration hides the required mpv backend" "$XDG_DATA_HOME/applications/mpv.desktop" 'Hidden=true'
assert_file_contains_literal "desktop migration preserves personal shell settings" "$HOME/.bashrc" 'export PERSONAL=1'
assert_file_not_contains "desktop migration removes retired shell helpers" "$HOME/.bashrc" 'function (mh|dh)'
assert_file_contains_literal "desktop migration preserves Micro preferences" "$XDG_CONFIG_HOME/micro/settings.json" 'personal'
assert_file_contains_literal "desktop migration preserves gdu preferences" "$XDG_CONFIG_HOME/gdu/gdu.yaml" 'personal'
assert_file_exists "desktop migration preserves the GTK theme hook" "$XDG_CONFIG_HOME/omarchy/hooks/theme-set.d/gtk-theme"
for hook in micro-theme disk-theme btop-theme; do
    assert_false "desktop migration removes $hook" "[[ -e '$XDG_CONFIG_HOME/omarchy/hooks/theme-set.d/$hook' ]]"
done
before=$(sha256sum "$HOME/.bashrc" "$XDG_DATA_HOME/applications/mpv.desktop")
assert_true "desktop migration is idempotent" "lua -E '$PROJECT_DIR/src/main.lua' '$PROJECT_DIR' apply-settings desktop; [[ \"\$(sha256sum '$HOME/.bashrc' '$XDG_DATA_HOME/applications/mpv.desktop')\" == '$before' ]]"

source "$PROJECT_DIR/scripts/lib/userconf.sh"
printf '# >>> os micro >>>\n' > "$SANDBOX/broken-rc"
assert_false "unbalanced shell migration fails" "remove_shell_block '$SANDBOX/broken-rc' '# >>> os micro >>>' '# <<< os micro <<<'"
assert_file_contains_literal "failed shell migration preserves the original" "$SANDBOX/broken-rc" '# >>> os micro >>>'
printf 'old\n' > "$SANDBOX/blocked-config"
mkdir "$SANDBOX/blocked-config.bak"
assert_false "failed backups stop configuration replacement" "printf 'new\n' | install_user_content '$SANDBOX/blocked-config'"
assert_file_contains_literal "failed backups preserve existing settings" "$SANDBOX/blocked-config" 'old'

test_summary
