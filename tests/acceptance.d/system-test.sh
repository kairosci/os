#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

status=0

verify_core_packages() {
  local package
  local manifest="$ARCH_PATH/installer/arch-base.packages"
  local -a missing=()

  # Without this, a missing manifest reads as an empty package list and the
  # audit passes having checked nothing.
  [[ -f $manifest ]] || fail "all Arch core packages are installed" "package manifest not found: $manifest"

  while IFS= read -r package; do
    [[ -z $package || $package == \#* ]] && continue
    pacman -Q "$package" >/dev/null 2>&1 || missing+=("$package")
  done <"$manifest"

  (( ${#missing[@]} == 0 )) || fail "all Arch core packages are installed" "missing packages: ${missing[*]}"
  pass "all Arch core packages are installed (${#missing[@]} missing)"
}

verify_bootloader() {
  local status
  status=$(bootctl status --no-pager 2>&1 || true)
  grep -Eq '^[[:space:]]*Product: systemd-boot([[:space:]]|$)' <<<"$status" ||
    fail "systemd-boot is the active bootloader"
  grep -Eq '^[[:space:]]*Current Entry: os_linux\.efi$' <<<"$status" ||
    fail "the system booted the Arch Linux UKI" "$(grep 'Current Entry:' <<<"$status" || echo 'current entry unavailable')"
  pass "systemd-boot started the Arch Linux UKI"
}

verify_kernel_headers() {
  local kernel=linux headers=linux-headers release pkgbase
  release=$(uname -r)
  if arch-pkg-present linux-t2; then
    kernel=linux-t2
    headers=linux-t2-headers
  fi

  [[ -r /usr/lib/modules/$release/pkgbase ]] ||
    fail "the running Arch kernel has module metadata" "$release has no pkgbase file"
  pkgbase=$(</usr/lib/modules/$release/pkgbase)
  [[ $pkgbase == "$kernel" ]] ||
    fail "the installed system boots the Arch Linux kernel" "$release uses $pkgbase, expected $kernel"
  arch-pkg-present "$headers" || fail "kernel headers are installed" "$headers is missing"
  [[ $(cat "/usr/lib/modules/$release/build/include/config/kernel.release") == "$release" ]] ||
    fail "headers match the running kernel" "$release has missing or mismatched headers"
  pass "the running Arch $kernel kernel has matching headers ($release)"
}

verify_defaults() {
  [[ $(arch-default-terminal) == "kitty" ]] || fail "Kitty is the default terminal"
  pass "Kitty is the default terminal"

  [[ $(arch-default-editor) == "nvim" ]] || fail "Neovim is the default editor"
  pass "Neovim is the default editor"

  [[ $(arch-theme-current) == "Cosmic" ]] || fail "Cosmic is the active theme"
  pass "Cosmic is the active theme"

  [[ $(gsettings get org.gnome.desktop.interface icon-theme | tr -d "'") == "Cosmic" ]] ||
    fail "the Cosmic icon theme is active"
  pass "the Cosmic icon theme is active"

  [[ $(arch-theme-bg-current) != "Unknown" ]] || fail "a current background is configured"
  pass "a current background is configured"

  [[ -n $(arch-font-current) ]] || fail "a monospace font is configured"
  pass "a monospace font is configured"

  [[ $(xdg-mime query default inode/directory) == "org.gnome.Nautilus.desktop" ]] || fail "directory MIME handling uses Nautilus"
  pass "directory MIME handling uses Nautilus"
}

verify_services() {
  local unit

  for unit in \
    avahi-daemon.service docker.socket \
    NetworkManager.service power-profiles-daemon.service sddm.service \
    systemd-resolved.service ufw.service; do
    systemctl is-enabled --quiet "$unit" || fail "core system services are enabled" "$unit is not enabled"
  done
  pass "core system services are enabled"

  for unit in NetworkManager.service systemd-resolved.service ufw.service; do
    systemctl is-active --quiet "$unit" || fail "critical system services are running" "$unit is not active"
  done
  pass "critical system services are running"

  systemctl --user is-active --quiet pipewire.service pipewire-pulse.service wireplumber.service ||
    fail "user audio services are running"
  pass "user audio services are running"
}

verify_runtime_tools() {
  # Docker access is intentionally NOT granted to the desktop user: the docker
  # group is root-equivalent, so a rogue process running as the user could
  # otherwise `docker run -v /:/host` its way to passwordless root. The daemon is
  # still enabled (docker.socket, checked in verify_services) and reached through
  # a polkit/sudo prompt; opting into sudoless Docker is a separate, warned step.
  command -v docker >/dev/null 2>&1 || fail "Docker CLI is installed"
  ! id -nG | grep -qw docker || fail "desktop user must not be in the docker group"
  # The group name being absent is not sufficient — a world-writable socket or an
  # ACL would still hand the user the root daemon. Prove it is actually
  # unreachable without elevation.
  if timeout 10 docker info >/dev/null 2>&1; then
    fail "desktop user must not reach the Docker daemon without elevation"
  fi
  pass "Docker is installed but unreachable by the desktop user without elevation"

  nvim --headless '+qa' >/dev/null 2>&1 || fail "Neovim starts headlessly"
  pass "Neovim starts headlessly"

  timeout 10 fastfetch --pipe false >/dev/null 2>&1 || fail "Fastfetch can read system information"
  pass "Fastfetch can read system information"

  git --version >/dev/null || fail "Git is installed and runnable"
  tmux -V >/dev/null || fail "Tmux is installed and runnable"
  mise --version >/dev/null || fail "Mise is installed and runnable"
  pass "core terminal tools are runnable"
}

verify_user_setup() {
  local directory

  for directory in DESKTOP DOCUMENTS DOWNLOAD PICTURES; do
    [[ -d $(xdg-user-dir "$directory") ]] || fail "XDG user directories exist" "$directory is missing"
  done
  pass "XDG user directories exist"

  [[ -e $HOME/.local/state/arch/current/theme ]] || fail "current theme state exists"
  [[ -e $HOME/.local/state/arch/current/background ]] || fail "current background state exists"
  [[ -s $HOME/.config/arch/shell.json ]] || fail "shell configuration exists"
  jq empty "$HOME/.config/arch/shell.json" || fail "shell configuration is valid JSON"
  pass "os user state and shell configuration exist"
}

for check in verify_core_packages verify_bootloader verify_kernel_headers verify_defaults verify_services verify_runtime_tools verify_user_setup; do
  if ! ("$check"); then
    status=1
  fi
done

exit $status
