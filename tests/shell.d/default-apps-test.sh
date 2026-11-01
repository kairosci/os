#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

mock_bin="$test_tmp/bin"
test_home="$test_tmp/home"
installed_dir="$test_tmp/installed"
install_log="$test_tmp/install-log"
terminal_log="$test_tmp/terminal-log"
notification_log="$test_tmp/notification-log"
setup_log="$test_tmp/setup-log"
browser_file="$test_tmp/browser"
browser_env_log="$test_tmp/browser-env-log"
mkdir -p "$mock_bin" "$test_home/.config" "$installed_dir"

terminal_home="$test_tmp/terminal-home"
arch_runtime="$test_tmp/arch-runtime"
mkdir -p "$terminal_home/.local/share/applications" "$arch_runtime/assets"
cp -a assets/applications "$arch_runtime/assets/"
cp -a config data default installer "$arch_runtime/"
mkdir -p "$arch_runtime/src/arch"
cp -a src/arch/python "$arch_runtime/src/"
printf 'legacy desktop entry\n' >"$terminal_home/.local/share/applications/org.legacy.terminal.desktop"
grep -Fxq 'kitty.desktop' "$ROOT/default/xdg-terminal-exec/hyprland-xdg-terminals.list" ||
  fail "Kitty remains the default terminal emulator"
pass "Kitty remains the default terminal emulator"

printf 'obsolete launcher\n' >"$terminal_home/.local/share/applications/org.old.terminal.desktop"
HOME="$terminal_home" AP="$ROOT" python3 -I "$ROOT/src/arch/python/installer_user/setup/terminal.py"
cmp -s "$ROOT/assets/applications/org.arch.terminal.desktop" \
  "$terminal_home/.local/share/applications/org.arch.terminal.desktop" ||
  fail "user setup installs the shipped Arch terminal launcher"
[[ ! -e $terminal_home/.local/share/applications/org.old.terminal.desktop ]] ||
  fail "user setup removes obsolete terminal launchers"
pass "user setup installs the Arch terminal launcher and removes obsolete entries"

cat >"$mock_bin/arch-cmd-missing" <<'SH'
#!/bin/bash
[[ ! -e $ARCH_TEST_INSTALLED_DIR/$1 ]]
SH

cat >"$mock_bin/arch-launch-terminal-with-presentation" <<'SH'
#!/bin/bash
printf '%s\0' "$@" >"$ARCH_TEST_TERMINAL_LOG"
SH

cat >"$mock_bin/arch-notification-send" <<'SH'
#!/bin/bash
printf '%s\0' "$@" >>"$ARCH_TEST_NOTIFICATION_LOG"
SH

cat >"$mock_bin/arch-test-setup-call" <<'SH'
#!/bin/bash
printf '%s:%s\n' "${0##*/}" "$*" >>"$ARCH_TEST_SETUP_LOG"
[[ ${ARCH_TEST_SETUP_FAIL:-} != "${0##*/}" ]]
SH

cat >"$mock_bin/sudo" <<'SH'
#!/bin/bash
printf 'sudo:%s\n' "$*" >>"$ARCH_TEST_SETUP_LOG"
[[ ${ARCH_TEST_SETUP_FAIL:-} != "sudo" ]]
SH

cat >"$mock_bin/xdg-settings" <<'SH'
#!/bin/bash
case $1 in
get) [[ -f $ARCH_TEST_BROWSER_FILE ]] && cat "$ARCH_TEST_BROWSER_FILE" ;;
set)
  printf '%s|%s\n' "${BROWSER-}" "${XDG_CURRENT_DESKTOP-}" >>"$ARCH_TEST_BROWSER_ENV_LOG"
  printf '%s\n' "$3" >"$ARCH_TEST_BROWSER_FILE"
  ;;
esac
SH

cat >"$mock_bin/arch-test-installer" <<'SH'
#!/bin/bash
installer=${0##*/}

if [[ $installer == "arch-install-browser" && ${ARCH_TEST_REAL_BROWSER_INSTALL:-false} == "true" ]]; then
  exec "$ROOT/src/arch/commands/arch-install-browser" "$@"
fi

case $installer in
arch-pkg-add|arch-pkg-aur-add)
  package=$1
  printf 'pkg:%s\n' "$package" >>"$ARCH_TEST_INSTALL_LOG"
  case $package in
  chromium) command=chromium ;;
  firefox) command=firefox ;;
  zen-browser-bin) command=zen-browser ;;
  cursor-bin) command=cursor ;;
  zed) command=zeditor ;;
  helix) command=helix ;;
  visual-studio-code-bin) command=code ;;
  arch-emacs) command=emacs ;;
  sublime-text-4) command=subl ;;
  vim) command=vim ;;
  neovim) command=nvim ;;
  esac
  ;;
arch-install-browser)
  selection=$1
  printf 'browser:%s\n' "$selection" >>"$ARCH_TEST_INSTALL_LOG"
  case $selection in
  chromium) command=chromium ;;
  chrome) command=google-chrome-stable ;;
  brave) command=brave ;;
  brave-origin) command=brave-origin ;;
  edge) command=microsoft-edge-stable ;;
  firefox) command=firefox ;;
  zen) command=zen-browser ;;
  esac
  ;;
arch-install-terminal)
  command=$1
  printf 'terminal:%s\n' "$command" >>"$ARCH_TEST_INSTALL_LOG"
  ;;
arch-install-editor-*)
  editor=${installer#arch-install-editor-}
  printf 'editor:%s\n' "$editor" >>"$ARCH_TEST_INSTALL_LOG"
  case $editor in
  vscode) command=code ;;
  zed) command=zeditor ;;
  helix) command=helix ;;
  emacs) command=emacs ;;
  esac
  ;;
esac

[[ ${ARCH_TEST_INSTALL_FAIL:-false} != "true" ]] || exit 1
touch "$ARCH_TEST_INSTALLED_DIR/$command"
SH

cat >"$mock_bin/setsid" <<'SH'
#!/bin/bash
printf 'launch:%s\n' "$*" >>"$ARCH_TEST_INSTALL_LOG"
SH

cat >"$mock_bin/arch-theme-refresh" <<'SH'
#!/bin/bash
printf 'theme:refresh\n' >>"$ARCH_TEST_INSTALL_LOG"
mkdir -p "$HOME/.local/state/arch/current/theme"
printf 'theme = "arch"\n' >"$HOME/.local/state/arch/current/theme/helix.toml"
SH

for installer in \
  arch-pkg-add \
  arch-pkg-aur-add \
  arch-install-browser \
  arch-install-terminal; do
  ln -s arch-test-installer "$mock_bin/$installer"
done
for setup_command in \
  arch-install-emacs \
  arch-theme-set-vscode \
  arch-theme-set-browser; do
  ln -s arch-test-setup-call "$mock_bin/$setup_command"
done

# The real browser installer below calls the platform's post-install hook; on a
# Mac with the platform package installed that would run, so answer it here.
printf '#!/bin/bash\nexit 0\n' >"$mock_bin/arch-lifecycle-dispatch"
chmod +x "$mock_bin"/*

export HOME="$test_home"
export PATH="$mock_bin:$ARCH_TEST_CLI_ROUTER:$ROOT/src/arch/commands:$PATH"
export AP="$ROOT"
export ARCH_TEST_INSTALLED_DIR="$installed_dir"
export ARCH_TEST_INSTALL_LOG="$install_log"
export ARCH_TEST_TERMINAL_LOG="$terminal_log"
export ARCH_TEST_NOTIFICATION_LOG="$notification_log"
export ARCH_TEST_SETUP_LOG="$setup_log"
export ARCH_TEST_BROWSER_FILE="$browser_file"
export ARCH_TEST_BROWSER_ENV_LOG="$browser_env_log"

assert_missing_opens_installer() {
  local type=$1 expected_route
  local selection=$2
  local -a command=(archctl default "$type")

  expected_route="archctl default $type --install $selection"

  : >"$terminal_log"
  "${command[@]}" "$selection"
  mapfile -d '' -t terminal_args <"$terminal_log"
  [[ ${terminal_args[*]} == "$expected_route" ]] ||
    fail "missing $selection opens its default installer in a terminal"
}

browser_cases=(
  'chromium chromium browser:chromium'
  'chrome google-chrome-stable browser:chrome'
  'brave brave browser:brave'
  'brave-origin brave-origin browser:brave-origin'
  'edge microsoft-edge-stable browser:edge'
  'firefox firefox browser:firefox'
  'zen zen-browser browser:zen'
)

terminal_cases=(
  'alacritty Alacritty.desktop'
  'foot foot.desktop'
  'ghostty com.mitchellh.ghostty.desktop'
  'kitty kitty.desktop'
)

editor_cases=(
  'code code pkg:visual-studio-code-bin'
  'cursor cursor pkg:cursor-bin'
  'zed zeditor pkg:zed'
  'sublime_text subl pkg:sublime-text-4'
  'helix helix pkg:helix'
  'vim vim pkg:vim'
  'emacs emacs pkg:arch-emacs'
  'nvim nvim pkg:neovim'
)

mkdir -p "$test_home/.vscode" "$test_home/dotfiles"
printf 'existing user file\n' >"$test_home/dotfiles/vscode-argv.json"
ln -s "$test_home/dotfiles/vscode-argv.json" "$test_home/.vscode/argv.json"

for entry in "${browser_cases[@]}"; do
  read -r selection command installer <<<"$entry"
  assert_missing_opens_installer browser "$selection"
done
for entry in "${terminal_cases[@]}"; do
  read -r selection desktop_id <<<"$entry"
  assert_missing_opens_installer terminal "$selection"
done
for entry in "${editor_cases[@]}"; do
  read -r selection command installer <<<"$entry"
  assert_missing_opens_installer editor "$selection"
done
pass "missing defaults open visible installers for every supported app"

for entry in "${browser_cases[@]}"; do
  read -r selection command installer <<<"$entry"
  rm -f "$installed_dir/$command"
  : >"$install_log"
  archctl default browser --install "$selection"
  [[ $(<"$install_log") == "$installer" ]] || fail "$selection uses its browser installer"
  [[ $(archctl default browser) == "$selection" ]] || fail "$selection becomes the default browser after installation"
done
pass "browser defaults install every missing browser before selection"

: >"$browser_env_log"
BROWSER=arch-launch-browser XDG_CURRENT_DESKTOP=Hyprland archctl default browser firefox
[[ $(<"$browser_env_log") == "|" ]] || fail "default browser selection clears session browser overrides before setting XDG state"
pass "setting the default browser ignores inherited session overrides"

: >"$install_log"
: >"$setup_log"
rm -f "$installed_dir/chromium"
ARCH_TEST_REAL_BROWSER_INSTALL=true archctl default browser --install chromium >/dev/null
[[ $(<"$install_log") == "pkg:chromium" ]] || fail "Chromium browser installer installs the package"
[[ $(archctl default browser) == "chromium" ]] || fail "Chromium becomes the default after its full installer succeeds"
cmp -s "$ROOT/config/chromium-flags.conf" "$test_home/.config/chromium-flags.conf" ||
  fail "Chromium browser installer copies the default flags"
grep -Fxq 'sudo:install -d -m 0755 -o root -g root /etc/chromium' "$setup_log" ||
  fail "Chromium browser installer creates a root-owned Chromium policy parent"
grep -Fxq 'sudo:install -d -m 0755 -o root -g root /etc/chromium/policies' "$setup_log" ||
  fail "Chromium browser installer creates a root-owned Chromium policies parent"
grep -Fxq 'sudo:install -d -m 0755 -o root -g root /etc/chromium/policies/managed' "$setup_log" ||
  fail "Chromium browser installer creates a root-owned managed policy directory"
grep -Fxq 'sudo:find /etc/chromium/policies/managed -mindepth 1 -maxdepth 1 ! -user root -exec rm -rf -- {} +' "$setup_log" ||
  fail "Chromium browser installer drops non-root files from its policy directory"
if grep -E 'groupadd|usermod|arch-browser-policy' "$setup_log" >/dev/null; then
  fail "Chromium browser installer does not create a browser-policy group" "$(cat "$setup_log")"
fi
[[ -f $test_home/.config/chromium/NativeMessagingHosts/com.arch.copy_url.json ]] ||
  fail "Chromium browser installer registers the Copy URL host"
[[ -f $test_home/.config/chromium/NativeMessagingHosts/com.arch.ytdlp.json ]] ||
  fail "Chromium browser installer registers the yt-dlp host"
grep -Fxq 'arch-theme-set-browser:' "$setup_log" ||
  fail "Chromium browser installer applies the current theme"
pass "Chromium browser installer restores the complete os setup"

: >"$install_log"
: >"$setup_log"
rm -f "$installed_dir/firefox"
ARCH_TEST_REAL_BROWSER_INSTALL=true archctl default browser --install firefox >/dev/null
[[ $(<"$install_log") == "pkg:firefox" ]] || fail "Firefox browser installer installs the package"
[[ $(archctl default browser) == "firefox" ]] || fail "Firefox becomes the default after its full installer succeeds"
grep -Fxq 'sudo:install -d -m 0755 -o root -g root /usr/lib/firefox/distribution' "$setup_log" ||
  fail "Firefox browser installer creates its distribution directory"
grep -Fxq 'sudo:find /usr/lib/firefox/distribution -mindepth 1 -maxdepth 1 ! -user root -exec rm -rf -- {} +' "$setup_log" ||
  fail "Firefox browser installer drops non-root files from its distribution directory"
grep -Fxq "sudo:install -m 644 -o root -g root -T $ROOT/default/firefox/policies.json /usr/lib/firefox/distribution/policies.json" "$setup_log" ||
  fail "Firefox browser installer copies policies.json without following a destination symlink"
[[ -e $installed_dir/firefox ]] || fail "Firefox browser installer marks firefox installed"
pass "Firefox browser installer restores the complete os setup"

: >"$install_log"
: >"$setup_log"
rm -f "$installed_dir/zen-browser"
ARCH_TEST_REAL_BROWSER_INSTALL=true archctl default browser --install zen >/dev/null
[[ $(<"$install_log") == "pkg:zen-browser-bin" ]] || fail "Zen browser installer installs the package"
[[ $(archctl default browser) == "zen" ]] || fail "Zen becomes the default after its full installer succeeds"
grep -Fxq 'sudo:install -d -m 0755 -o root -g root /opt/zen-browser/distribution' "$setup_log" ||
  fail "Zen browser installer creates its distribution directory"
grep -Fxq 'sudo:find /opt/zen-browser/distribution -mindepth 1 -maxdepth 1 ! -user root -exec rm -rf -- {} +' "$setup_log" ||
  fail "Zen browser installer drops non-root files from its distribution directory"
grep -Fxq "sudo:install -m 644 -o root -g root -T $ROOT/default/firefox/policies.json /opt/zen-browser/distribution/policies.json" "$setup_log" ||
  fail "Zen browser installer copies policies.json without following a destination symlink"
[[ -e $installed_dir/zen-browser ]] || fail "Zen browser installer marks zen-browser installed"
pass "Zen browser installer restores the complete os setup"

archctl default browser zen
rm -f "$installed_dir/chromium"
if ARCH_TEST_REAL_BROWSER_INSTALL=true ARCH_TEST_INSTALL_FAIL=true \
  archctl default browser --install chromium >"$test_tmp/browser-package-failure" 2>&1; then
  fail "failed Chromium package installation returns an error"
fi
[[ $(archctl default browser) == "zen" ]] || fail "failed Chromium package installation preserves the default browser"
[[ ! -e $installed_dir/chromium ]] || fail "failed Chromium package installation does not mark it installed"
pass "failed Chromium package installation preserves the current default"

if ARCH_TEST_REAL_BROWSER_INSTALL=true ARCH_TEST_SETUP_FAIL=sudo \
  archctl default browser --install chromium >"$test_tmp/browser-install-failure" 2>&1; then
  fail "failed Chromium setup returns an error"
fi
[[ $(archctl default browser) == "zen" ]] || fail "failed Chromium setup preserves the default browser"
grep -Fq 'Installing Chromium' "$test_tmp/browser-install-failure" ||
  fail "failed Chromium setup keeps progress visible in the terminal"
pass "failed Chromium setup preserves the current default"

for entry in "${terminal_cases[@]}"; do
  read -r selection desktop_id <<<"$entry"
  rm -f "$installed_dir/$selection"
  : >"$install_log"
  archctl default terminal --install "$selection"
  [[ $(<"$install_log") == "terminal:$selection" ]] || fail "$selection uses the terminal installer"
  [[ $(tail -n 1 "$test_home/.config/xdg-terminals.list") == "$desktop_id" ]] ||
    fail "$selection becomes the default terminal after installation"
done
pass "terminal defaults install every missing terminal before selection"

for entry in "${editor_cases[@]}"; do
  read -r selection command installer <<<"$entry"
  rm -f "$installed_dir/$command"
  : >"$install_log"
  archctl default editor --install "$selection"
  if [[ $selection == "zed" ]]; then
    for ((attempt = 0; attempt < 100; attempt++)); do
      grep -Fxq 'launch:uwsm-app -- gtk-launch dev.zed.Zed' "$install_log" && break
      sleep 0.01
    done
    [[ $(<"$install_log") == $'pkg:zed\nlaunch:uwsm-app -- gtk-launch dev.zed.Zed' ]] ||
      fail "Zed uses the unified installer route and launches after package installation" "$(<"$install_log")"
  elif [[ $selection == "helix" ]]; then
    [[ $(<"$install_log") == $'pkg:helix\ntheme:refresh' ]] ||
      fail "Helix installs its package and refreshes the theme before setup" "$(<"$install_log")"
    [[ -L $test_home/.config/helix/themes/arch.toml ]] || fail "Helix links the current Arch theme"
    [[ $(<"$test_home/.config/helix/config.toml") == 'theme = "arch"' ]] || fail "Helix seeds its config only when missing"
    grep -Fxq 'alias hx="helix"' "$test_home/.bashrc" || fail "Helix adds the hx alias"
  elif [[ $selection == "emacs" ]]; then
    for ((attempt = 0; attempt < 100; attempt++)); do
      grep -Fxq 'launch:uwsm-app -- gtk-launch emacsclient' "$install_log" && break
      sleep 0.01
    done
    [[ $(<"$install_log") == $'pkg:arch-emacs\nlaunch:uwsm-app -- gtk-launch emacsclient' ]] ||
      fail "Emacs installs before launching its client" "$(<"$install_log")"
    grep -Fxq 'arch-install-emacs:' "$setup_log" || fail "Emacs setup runs before its client launches"
  elif [[ $selection == "code" ]]; then
    for ((attempt = 0; attempt < 100; attempt++)); do
      grep -Fxq 'launch:uwsm-app -- gtk-launch code' "$install_log" && break
      sleep 0.01
    done
    [[ $(<"$install_log") == $'pkg:visual-studio-code-bin\nlaunch:uwsm-app -- gtk-launch code' ]] ||
      fail "VS Code installs before launch" "$(<"$install_log")"
    grep -Fq '"password-store":"gnome-libsecret"' "$test_home/.vscode/argv.json" ||
      fail "VS Code uses the system secret store"
    grep -Fq '"update.mode": "none"' "$test_home/.config/Code/User/settings.json" ||
      fail "VS Code automatic updates are disabled"
    grep -Fxq 'arch-theme-set-vscode:' "$setup_log" || fail "VS Code receives the current Arch theme"
  else
    [[ $(<"$install_log") == "$installer" ]] || fail "$selection uses its editor installer"
  fi
  [[ $(archctl default editor) == "$command" ]] || fail "$selection becomes the default editor after installation"
done
pass "editor defaults install every missing editor before selection"
[[ -L $test_home/.vscode/argv.json ]] || fail "VS Code setup preserves the user config symlink"
grep -Fq '"password-store":"gnome-libsecret"' "$test_home/dotfiles/vscode-argv.json" ||
  fail "VS Code setup writes through an in-home user config symlink"
pass "VS Code setup preserves in-home config symlinks"

vscode_escape_home="$test_tmp/vscode-escape-home"
vscode_escape_target="$test_tmp/external-vscode-argv.json"
mkdir -p "$vscode_escape_home/.vscode"
printf 'protected external file\n' >"$vscode_escape_target"
ln -s "$vscode_escape_target" "$vscode_escape_home/.vscode/argv.json"
: >"$install_log"
if HOME="$vscode_escape_home" archctl install editor vscode >/dev/null 2>&1; then
  fail "VS Code rejects a config symlink that escapes the home directory"
fi
[[ $(<"$vscode_escape_target") == "protected external file" ]] ||
  fail "VS Code does not overwrite files through an external config symlink"
[[ $(<"$install_log") == "pkg:visual-studio-code-bin" ]] ||
  fail "VS Code does not configure or launch after rejecting an external path"
pass "VS Code installer confines config writes to the home directory"

printf 'theme = "user"\n' >"$test_home/.config/helix/config.toml"
: >"$install_log"
archctl install editor helix >/dev/null
[[ $(<"$install_log") == "pkg:helix" ]] || fail "Helix skips refreshing an already available theme"
[[ $(<"$test_home/.config/helix/config.toml") == 'theme = "user"' ]] || fail "Helix preserves an existing user config"
[[ $(grep -Fc 'alias hx="helix"' "$test_home/.bashrc") == 1 ]] || fail "Helix setup does not duplicate its shell alias"
pass "Helix setup preserves existing config and remains idempotent"

helix_failure_home="$test_tmp/helix-failure-home"
mkdir -p "$helix_failure_home"
if HOME="$helix_failure_home" ARCH_TEST_INSTALL_FAIL=true archctl install editor helix >/dev/null 2>&1; then
  fail "Helix package installation failure returns an error"
fi
[[ ! -e $helix_failure_home/.config/helix && ! -e $helix_failure_home/.bashrc ]] ||
  fail "failed Helix package installation makes no user configuration changes"
pass "failed Helix installation leaves user configuration untouched"

editor_state="$HOME/.local/state/arch/defaults/editor"
mkdir -p "$(dirname "$editor_state")"
printf '%s\n' sublime_text >"$editor_state"
[[ $(archctl default editor) == "subl" ]] || fail "legacy Sublime Text state resolves to its current command"
rm -f "$installed_dir/zeditor"
: >"$install_log"
archctl default editor --install zeditor
for ((attempt = 0; attempt < 100; attempt++)); do
  grep -Fxq 'launch:uwsm-app -- gtk-launch dev.zed.Zed' "$install_log" && break
  sleep 0.01
done
[[ $(<"$install_log") == $'pkg:zed\nlaunch:uwsm-app -- gtk-launch dev.zed.Zed' && $(archctl default editor) == "zeditor" ]] ||
  fail "the legacy Zed alias installs and selects the canonical backend"
pass "editor aliases and legacy state values are preserved"

: >"$install_log"
: >"$terminal_log"
archctl default browser zen
archctl default terminal kitty
archctl default editor nvim
[[ ! -s $install_log && ! -s $terminal_log ]] || fail "installed defaults skip installation"
pass "installed defaults are selected immediately"

previous_editor=$(archctl default editor)
rm -f "$installed_dir/vim"
if ARCH_TEST_INSTALL_FAIL=true archctl default editor --install vim >"$test_tmp/install-failure" 2>&1; then
  fail "failed default installation returns an error"
fi
[[ $(archctl default editor) == "$previous_editor" ]] || fail "failed installation preserves the default"
pass "failed installation preserves the current default"
