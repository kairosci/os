#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
require_command python3
require_command pacman-conf

# Every platform's repositories are a pacman.conf and mirrorlist per channel,
# copied into place whole on a channel change and at install finalization, as
# x86_64's always were.

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
export ARCH_PATH="$ROOT"
source "$ROOT/installer/helpers/pacman.sh"

platforms="x86 aarch64 aarch64-apple"
# Apple Silicon has edge alone: its packages and Asahi ALARM are published for
# edge only so far.
channels_for() {
  if [[ $1 == "aarch64-apple" ]]; then echo "edge"; else echo "stable rc edge"; fi
}

# ── the templates ────────────────────────────────────────────────────────────

[[ $(arch_pacman_templates x86) == "$ROOT/default/pacman" ]] || fail "x86 keeps its templates where they were"
[[ $(arch_pacman_templates aarch64) == "$ROOT/default/pacman/aarch64" ]] || fail "plain aarch64 uses the aarch64 templates"
[[ $(arch_pacman_templates aarch64-apple) == "$ROOT/default/pacman/aarch64-apple" ]] || fail "Apple Silicon uses its own templates"
for platform in aarch64-qualcomm aarch64-n1x aarch64-gb10; do
  [[ $(arch_pacman_templates "$platform") == "$ROOT/default/pacman/aarch64" ]] || fail "$platform shares the aarch64 templates"
  [[ $(arch_pacman_default_channel "$platform") == stable ]] || fail "$platform defaults to stable"
done
! arch_pacman_templates riscv 2>/dev/null || fail "an unknown platform has no templates"
pass "each platform's templates sit in a directory of their own, x86_64's where they always were"

for platform in x86 aarch64; do
  [[ $(arch_pacman_default_channel "$platform") == stable ]] || fail "$platform defaults to stable"
done
[[ $(arch_pacman_default_channel aarch64-apple) == edge ]] || fail "aarch64-apple defaults to edge"
! arch_pacman_default_channel riscv 2>/dev/null || fail "an unknown platform has no default channel"
pass "every platform defaults to stable but Apple Silicon, which defaults to edge"

# pacman reads each repository list from the template, with its mirrorlist
# standing in for /etc/pacman.d/mirrorlist.
repos() {
  local templates=$1 channel=$2
  sed "s|/etc/pacman.d/mirrorlist|$templates/mirrorlist-$channel|" "$templates/pacman-$channel.conf" >"$work/pacman.conf"
  pacman-conf --config "$work/pacman.conf" --repo-list | tr '\n' ' '
}
for platform in $platforms; do
  templates=$(arch_pacman_templates "$platform")
  for channel in stable rc; do
    [[ $platform == "aarch64-apple" ]] || continue
    [[ ! -e $templates/pacman-$channel.conf && ! -e $templates/mirrorlist-$channel ]] ||
      fail "$platform has no $channel template or mirrorlist"
  done
  for channel in $(channels_for "$platform"); do
    [[ -f $templates/pacman-$channel.conf && -f $templates/mirrorlist-$channel ]] ||
      fail "$platform has a $channel template and mirrorlist"
    list=$(repos "$templates" "$channel") || fail "$platform $channel: pacman reads the template"
    case $platform in
      x86) expected="arch core extra multilib " ;;
      aarch64) expected="arch core extra alarm " ;;
      aarch64-apple) expected="arch asahi-alarm core extra alarm " ;;
    esac
    [[ $list == "$expected" ]] || fail "$platform $channel: repositories in order" "$list"
    # $arch stays literal: pacman fills it in on the machine.
    server=$(sed -n '/^\[arch\]/,/^\[/s/^Server = //p' "$templates/pacman-$channel.conf")
    [[ $server == "https://pkgs.github.com/kairosci/os/$channel/\$arch" ]] ||
      fail "$platform $channel: os's $channel repository" "$server"
    # Each platform uses its official generic mirror for every channel; the
    # selected package repository identifies the channel.
    case $platform in
      x86) mirror="https://geo.mirror.pkgbuild.com/\$repo/os/\$arch" ;;
      *) mirror="http://mirror.archlinuxarm.org/\$arch/\$repo" ;;
    esac
    expected_mirror=$mirror
    mirror=$(sed -n 's/^Server = //p' "$templates/mirrorlist-$channel")
    [[ $mirror == "$expected_mirror" ]] || fail "$platform $channel: the official Arch mirror" "$mirror"
  done
done
pass "x86 and aarch64 have templates for stable, rc and edge and Apple Silicon for edge alone, each with its repositories in order and its channel's mirrors"

# arch-version-channel names each template pair's channel: the menu's
# checkmarks and a refresh with no channel go by it.
for platform in $platforms; do
  templates=$(arch_pacman_templates "$platform")
  for channel in $(channels_for "$platform"); do
    cp "$templates/pacman-$channel.conf" "$work/pacman.conf"
    cp "$templates/mirrorlist-$channel" "$work/mirrorlist"
    said=$(ARCH_PACMAN_CONF="$work/pacman.conf" ARCH_PACMAN_MIRRORLIST="$work/mirrorlist" \
      "$ROOT/src/arch/commands/arch-version-channel")
    [[ $said == "$channel" ]] || fail "$platform $channel: arch-version-channel names it" "$said"
  done
done
pass "arch-version-channel names the channel of every platform's templates"

# ── install finalization ─────────────────────────────────────────────────────

finalize_bin=$work/finalize-bin
mkdir -p "$finalize_bin"
printf '#!/bin/bash\necho "$PLATFORM"\n' >"$finalize_bin/arch-hw-platform"
for command in arch-pkg-add pacman-key; do
  printf '#!/bin/bash\nexit 0\n' >"$finalize_bin/$command"
done
printf '#!/bin/bash\nexit 0\n' >"$finalize_bin/lspci"
chmod +x "$finalize_bin"/*
# Finalization restores the templates through arch-apply-pacman, whose copy
# here writes into the test's etc rather than the host's.
finalize_root=$work/finalize-root
mkdir -p "$finalize_root/installer" "$finalize_root/src/arch/commands" "$finalize_root/src/arch/python/installer/hardware" "$finalize_root/src/arch/python/installer/post_install" "$finalize_root/data/installer/hardware" "$finalize_root/data/installer" "$finalize_root/default"
cp -r "$ROOT/installer/helpers" "$finalize_root/installer/"
cp "$ROOT/src/arch/python/installer/hardware/pacman_repositories.py" "$finalize_root/src/arch/python/installer/hardware/"
cp "$ROOT/data/installer/hardware/pacman-repositories.yml" "$finalize_root/data/installer/hardware/"
cp "$ROOT/src/arch/python/installer/post_install/pacman.py" "$finalize_root/src/arch/python/installer/post_install/"
cp "$ROOT/data/installer/post-install.yml" "$finalize_root/data/installer/"
cp -r "$ROOT/default/pacman" "$ROOT/default/regions" "$finalize_root/default/"
cp "$ROOT/src/arch/commands/arch-apply-pacman" "$finalize_root/src/arch/commands/arch-apply-pacman"
mkdir -p "$work/installer/hardware"

# Finalization asks the image helper whether this is an image build, which root
# answers from the real /var/lib/arch; everyone else from the test's root.
if (( EUID == 0 )); then
  skip "install finalization copies the platform's channel template and mirrorlist (refuses to run as root)"
else
for platform in $platforms; do
  templates=$(arch_pacman_templates "$platform")
  # An install built for a channel the platform has no templates for, or for
  # none, gets the platform's default channel.
  for channel in stable rc edge ""; do
    expected=$channel
    [[ -n $expected && -f $templates/pacman-$expected.conf ]] || expected=$(arch_pacman_default_channel "$platform")
    rm -rf "$work/etc"
    mkdir -p "$work/etc/pacman.d"
    printf 'offline\n' | tee "$work/etc/pacman.conf" >"$work/etc/pacman.d/mirrorlist"
    ARCH_PATH=$finalize_root ARCH_IMAGE_ROOT=$work ARCH_MIRROR=$channel PLATFORM=$platform PATH="$finalize_bin:$PATH" \
      python3 -I "$finalize_root/src/arch/python/installer/post_install/pacman.py" >/dev/null || fail "$platform finalization on '$channel'"
    cmp -s "$work/etc/pacman.conf" "$templates/pacman-$expected.conf" || fail "$platform '$channel': finalization copies the $expected template"
    cmp -s "$work/etc/pacman.d/mirrorlist" "$templates/mirrorlist-$expected" || fail "$platform '$channel': finalization copies the $expected mirrorlist"
  done
done
pass "install finalization copies the platform's channel template and mirrorlist, or its default channel's when it has none for that channel"
fi

# The Python finalization runner reads the ordered steps from packaged data,
# sources shell leaves in isolated Bash and stops with the leaf's exit status.
ARCH_PATH="$ROOT" ARCH_INSTALL="$ROOT/installer" python3 -I \
  "$ROOT/src/arch/python/installer/step_runner.py" --validate data/installer/post-install.yml ||
  fail "the post-install setup data resolves every configured leaf"
pass "post-install setup data resolves every configured leaf"

post_install_root="$work/post-install-root"
mkdir -p "$post_install_root/data/installer" \
  "$post_install_root/installer/post-install" \
  "$post_install_root/src/arch/python/installer/post_install"
cat >"$post_install_root/data/installer/post-install.yml" <<'YAML'
steps:
  - root: arch_install
    path: post-install/first.sh
  - src/arch/python/installer/post_install/second.py
  - installer/post-install/third.sh
messages:
  en:
    starting: "Starting: {step}"
    completed: "Completed: {step}"
    failed: "Failed: {step} (exit code: {status})"
  it:
    starting: "Avvio: {step}"
    completed: "Completato: {step}"
    failed: "Non riuscito: {step} (codice di uscita: {status})"
YAML
cat >"$post_install_root/installer/post-install/first.sh" <<'SH'
printf 'first\n' >>"$POST_INSTALL_ORDER"
SH
cat >"$post_install_root/src/arch/python/installer/post_install/second.py" <<'PY'
import os
from pathlib import Path

with Path(os.environ["POST_INSTALL_ORDER"]).open("a", encoding="utf-8") as stream:
  stream.write("second\n")
if os.environ.get("POST_INSTALL_FAIL"):
  raise SystemExit(23)
PY
cat >"$post_install_root/installer/post-install/third.sh" <<'SH'
printf 'third\n' >>"$POST_INSTALL_ORDER"
SH

post_install_order="$work/post-install-order"
post_install_output="$work/post-install-output"
ARCH_PATH="$post_install_root" ARCH_INSTALL="$post_install_root/installer" \
  POST_INSTALL_ORDER="$post_install_order" LANG=it_IT.UTF-8 \
  python3 -I "$ROOT/src/arch/python/installer/step_runner.py" data/installer/post-install.yml >"$post_install_output" 2>&1 ||
  fail "post-install runner completes every configured step"
[[ $(<"$post_install_order") == $'first\nsecond\nthird' ]] ||
  fail "post-install runner preserves YAML order across Python and shell leaves"
grep -Fq "Avvio: $post_install_root/installer/post-install/first.sh" "$post_install_output" ||
  fail "post-install runner localizes its progress log"
pass "post-install runner executes ordered YAML steps and localizes progress"

: >"$post_install_order"
ARCH_PATH="$post_install_root" ARCH_INSTALL="$post_install_root/installer" \
  POST_INSTALL_ORDER="$post_install_order" LANG=en_US.UTF-8 \
  ARCH_INSTALL_DEBUG=1 python3 -I "$ROOT/src/arch/python/installer/step_runner.py" data/installer/post-install.yml \
  >"$post_install_output" 2>&1 || fail "post-install runner supports installer debug mode"
grep -Fq '+ first.sh:' "$post_install_output" || fail "post-install runner traces sourced leaves in debug mode"
pass "post-install runner preserves shell tracing in debug mode"

: >"$post_install_order"
if ARCH_PATH="$post_install_root" ARCH_INSTALL="$post_install_root/installer" \
  POST_INSTALL_ORDER="$post_install_order" POST_INSTALL_FAIL=1 LANG=it_IT.UTF-8 \
  python3 -I "$ROOT/src/arch/python/installer/step_runner.py" data/installer/post-install.yml >"$post_install_output" 2>&1; then
  fail "post-install runner stops when a step fails"
else
  [[ $? == 23 ]] || fail "post-install runner preserves the failing step's status" "$(<"$post_install_output")"
fi
[[ $(<"$post_install_order") == $'first\nsecond' ]] ||
  fail "post-install runner does not continue after a failure"
grep -Fq 'Non riuscito:' "$post_install_output" || fail "post-install runner localizes failure logs"
pass "post-install runner stops at and reports the failing step"

printf 'steps:\n  - ../outside.sh\nmessages:\n  en: {starting: "Starting {step}", completed: "Done {step}", failed: "Failed {step} {status}"}\n' \
  >"$post_install_root/data/installer/unsafe.yml"
cat >"$post_install_root/outside.sh" <<'SH'
touch "$POST_INSTALL_ESCAPE_MARKER"
SH
if ARCH_PATH="$post_install_root" ARCH_INSTALL="$post_install_root/installer" \
  POST_INSTALL_ESCAPE_MARKER="$work/escaped" python3 -I \
  "$ROOT/src/arch/python/installer/step_runner.py" data/installer/unsafe.yml \
  >"$post_install_output" 2>&1; then
  fail "post-install runner rejects a step outside its root"
fi
[[ ! -e $work/escaped ]] || fail "post-install runner never executes a path outside its root"
pass "post-install runner rejects path traversal in step data"

# ── refresh through the command, with every privileged step a stand-in ───────

rm -rf "$work"
source "$SHELL_TEST_DIR/fixtures/sudo-boundary-test.sh"
copy_boundary_file bin/arch-refresh-pacman
copy_boundary_file bin/arch-apply-pacman
cat >"$SUDO_TEST_ROOT/src/arch/commands/arch-channel-current" <<'STUB'
#!/bin/bash
[[ ${SUDO_TEST_CHANNEL_FAIL:-0} != "1" ]] || exit 1
echo "${SUDO_TEST_CHANNEL:-unknown}"
STUB
chmod +x "$SUDO_TEST_ROOT/src/arch/commands/arch-channel-current"

refresh() {
  "$SUDO_TEST_ROOT/src/arch/commands/arch-refresh-pacman" "$@" >"$boundary_tmp/output" 2>&1
}
events() {
  grep -vE '^sudo (-h|-k)$' "$SUDO_TEST_LOG" || true
}

for platform in $platforms; do
  case $platform in
    x86) templates=$SUDO_TEST_ROOT/default/pacman ;;
    aarch64) templates=$SUDO_TEST_ROOT/default/pacman/aarch64 ;;
    aarch64-apple) templates=$SUDO_TEST_ROOT/default/pacman/aarch64-apple ;;
  esac
  # No channel named refreshes to the platform's default one.
  for channel in $(channels_for "$platform") ""; do
    reset_boundary
    SUDO_TEST_PLATFORM=$platform refresh $channel || fail "$platform refreshes to '$channel'" "$(cat "$boundary_tmp/output")"
    [[ -n $channel ]] || channel=$(arch_pacman_default_channel "$platform")
    python3 - "$SUDO_TEST_LOG" "$templates" "$channel" <<'PY'
import sys
events = [e for e in open(sys.argv[1]).read().splitlines() if e not in ('sudo -h', 'sudo -k')]
templates, channel = sys.argv[2:]
# The caller renders from the platform's templates; root backs up and copies
# the result.
copies = [e for e in events if e.startswith('step:cp ')]
assert len(copies) == 6, events
rendered = copies[0].split()[-1].rsplit('/', 1)[0]
expected = [
  f'step:cp {templates}/pacman-{channel}.conf {rendered}/pacman.conf',
  f'step:cp {templates}/mirrorlist-{channel} {rendered}/mirrorlist',
  'step:cp -f /etc/pacman.conf /etc/pacman.conf.bak',
  'step:cp -f /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak',
  f'step:cp -f {rendered}/pacman.conf /etc/pacman.conf',
  f'step:cp -f {rendered}/mirrorlist /etc/pacman.d/mirrorlist',
]
assert copies == expected, events
hook = events.index('step:arch-hook pre-refresh-pacman')
upgrade = 'step:pacman -Syyuu --noconfirm'
if channel in ('stable', 'rc'):
  # The -dev pair is edge's: an old build of it in a stable or rc repository is
  # left to the channel switch's swap.
  upgrade += ' --ignore arch-dev,arch-settings-dev'
transaction = events.index(upgrade)
assert events.index(expected[-1]) < hook < transaction, events
PY
    assert_boundary_cold "$platform $channel"
  done
done
pass "a refresh renders and copies the named channel, or the platform default when the current channel is unknown, then runs the cold hook and the upgrade"

for channel in stable rc edge dev; do
  reset_boundary
  SUDO_TEST_CHANNEL=$channel refresh || fail "refresh preserves $channel" "$(cat "$boundary_tmp/output")"
  expected=$channel
  [[ $channel != "dev" ]] || expected=edge
  grep -F "step:cp $SUDO_TEST_ROOT/default/pacman/pacman-$expected.conf " "$SUDO_TEST_LOG" >/dev/null ||
    fail "$channel refresh uses $expected repositories" "$(events)"
  grep -F "step:cp $SUDO_TEST_ROOT/default/pacman/mirrorlist-$expected " "$SUDO_TEST_LOG" >/dev/null ||
    fail "$channel refresh uses $expected mirrors" "$(events)"
  assert_boundary_cold "$channel refresh"
done
pass "a refresh with no channel preserves stable, rc and edge, and uses edge for a linked dev checkout"

reset_boundary
SUDO_TEST_CHANNEL=edge SUDO_TEST_CHANNEL_FAIL=1 refresh rc || fail "explicit rc overrides current edge without detecting it"
grep -F "step:cp $SUDO_TEST_ROOT/default/pacman/pacman-rc.conf " "$SUDO_TEST_LOG" >/dev/null ||
  fail "explicit rc overrides current edge" "$(events)"
assert_boundary_cold "explicit override"
pass "an explicit channel overrides the current channel without querying it"

for channel in stable rc; do
  reset_boundary
  if SUDO_TEST_PLATFORM=aarch64-apple SUDO_TEST_CHANNEL=$channel refresh; then fail "aarch64-apple refuses current $channel without templates"; fi
  [[ -z $(events) ]] || fail "unsupported current channel changes nothing" "$(events)"
  assert_boundary_cold "unsupported current channel"
done
for channel in invalid failed; do
  reset_boundary
  if [[ $channel == "failed" ]]; then
    if SUDO_TEST_CHANNEL_FAIL=1 refresh; then fail "failed channel detection is refused"; fi
  else
    if SUDO_TEST_CHANNEL=$channel refresh; then fail "unexpected channel is refused"; fi
  fi
  [[ -z $(events) ]] || fail "failed channel detection changes nothing" "$(events)"
  assert_boundary_cold "failed channel detection"
done
pass "unsupported, unexpected or failed current channel detection changes nothing"

reset_boundary
if refresh invalid; then fail "invalid explicit channel is refused"; fi
[[ -z $(events) ]] || fail "invalid explicit channel changes nothing" "$(events)"
assert_boundary_cold "invalid explicit channel"
pass "an invalid explicit channel changes nothing"

# A channel the platform has no template for (stable or rc on Apple Silicon),
# or a machine whose platform can't be told, stops before anything changes.
for platform in aarch64-apple; do
  for channel in stable rc; do
    reset_boundary
    if SUDO_TEST_PLATFORM=$platform refresh "$channel"; then fail "$platform: $channel is refused"; fi
    [[ -z $(events) ]] || fail "$platform: $channel stops before anything" "$(events)"
    grep -q "os has no $channel channel for $platform" "$boundary_tmp/output" || fail "the refusal says why" "$(cat "$boundary_tmp/output")"
    assert_boundary_cold "$platform $channel"
  done
done
cat >"$SUDO_TEST_ROOT/src/arch/commands/arch-hw-platform" <<'STUB'
#!/bin/bash
exit 1
STUB
reset_boundary
if refresh stable; then fail "an unknown platform is refused"; fi
[[ -z $(events) ]] || fail "an unknown platform stops before anything" "$(events)"
assert_boundary_cold "unknown platform"
pass "a channel without a template, or a machine whose platform can't be told, changes nothing"
