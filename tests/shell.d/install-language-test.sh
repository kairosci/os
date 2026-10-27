#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
export ARCH_PATH="$scratch/arch" ARCH_INSTALL="$ROOT/installer" COMMAND_LOG="$scratch/commands"
mkdir -p "$ARCH_PATH/src/cli" "$ARCH_PATH/default/i18n"
printf '{"en":{},"fr":{},"es":{},"it":{}}\n' >"$ARCH_PATH/default/i18n/locales.json"
mkdir -p "$ARCH_PATH/data/installer"
cp "$ROOT/data/installer/system-setup.yml" "$ARCH_PATH/data/installer/system-setup.yml"
for command in arch-locale-generate arch-language; do
  printf '#!/bin/bash\nprintf "%%s %%s\\n" "${0##*/}" "$*" >>"$COMMAND_LOG"\n' >"$ARCH_PATH/src/cli/$command"
  chmod +x "$ARCH_PATH/src/cli/$command"
done
export ARCH_LANGUAGE_MARKER="$scratch/language"

system_step() { : >"$COMMAND_LOG"; python3 -I "$ROOT/src/python/installer/system_setup/language_setup.py" 2>"$scratch/err"; }

system_step
[[ ! -s $COMMAND_LOG ]] || fail "no preset language generates no locale"
printf 'it\n' >"$ARCH_LANGUAGE_MARKER"
system_step
[[ $(<"$COMMAND_LOG") == "arch-locale-generate it" ]] || fail "a preset language generates its locale" "$(<"$COMMAND_LOG")"
for bad in 'zh-CN' 'zh_CN' '../x' 'it; reboot' '$(touch NEVER)'; do
  printf '%s\n' "$bad" >"$ARCH_LANGUAGE_MARKER"
  system_step
  [[ ! -s $COMMAND_LOG ]] || fail "a malformed preset is never passed on: $bad" "$(<"$COMMAND_LOG")"
done
pass "the system step generates only a well-formed preset language's locale"

grep -qxF 'language_file=/etc/arch/language' "$ROOT/installer/user/language.sh" ||
  fail "the user step reads the preset as data"
grep -q 'marker_default: /etc/arch/language' "$ROOT/data/installer/system-setup.yml" ||
  fail "the system step reads the Arch language marker"
grep -qF 'language_file=/etc/arch/language' "$ROOT/installer/user/language.sh" ||
  fail "the user step can still read a legacy language preset"
! grep -qE '(^|[^a-z])(source|\.) .*/etc/(arch|arch)/language' "$ROOT/installer/user/language.sh" ||
  fail "neither step sources the preset"
grep -qx 'run_logged "$ARCH_PATH/src/python/installer/system_setup/language_setup.py"' "$ROOT/installer/config/all.sh" || fail "system finalization runs the language step"
grep -qx 'run_logged "$ARCH_INSTALL/user/language.sh"' "$ROOT/installer/user/all.sh" || fail "user finalization runs the language step"
pass "both finalization steps run, and read the preset as data"

# The user step's `arch-language seed`: the real command, with the outside
# world stubbed, so it is seen to elevate and notify nothing.
work=$scratch/seed
mkdir -p "$work/stubs"
export XDG_CONFIG_HOME=$work/config ARCH_LANGUAGE_FILE=$work/language SEED_LOG=$work/log
for command in sudo pkexec locale-gen arch-notification-send dbus-update-activation-environment; do
  printf '#!/bin/bash\necho "%s $*" >>"$SEED_LOG"\n' "$command" >"$work/stubs/$command"
done
chmod +x "$work/stubs/"*
seed() { : >"$SEED_LOG"; ARCH_PATH=$ROOT PATH="$work/stubs:$ROOT/src/cli:$PATH" "$ROOT/src/cli/arch-language" seed "$@" </dev/null; }
seed it
[[ $(<"$ARCH_LANGUAGE_FILE") == it ]] || fail "seeding persists the preset language"
grep -qx 'export LANG=it_IT.UTF-8' "$XDG_CONFIG_HOME/uwsm/env.d/50-arch-language" || fail "seeding sets the session LANG for the first login"
! grep -qE '^(sudo|pkexec|locale-gen|arch-notification-send) ' "$SEED_LOG" || fail "seeding elevates, generates and notifies nothing" "$(<"$SEED_LOG")"
if seed xx 2>/dev/null; then fail "seeding rejects unknown codes"; fi
printf 'da\n' >"$ARCH_LANGUAGE_FILE"
seed it
[[ $(<"$ARCH_LANGUAGE_FILE") == da ]] || fail "seeding keeps a language the user already chose"
! grep -q '^dbus-update-activation-environment ' "$SEED_LOG" || fail "seeding needs no session bus" "$(<"$SEED_LOG")"
pass "seeding sets the user's language and session LANG without elevating or notifying"

# A deferred install's region, settled at first boot against the owner's
# timezone; the function is taken from owner setup itself.
eval "$(sed -n '/^configure_region() {$/,/^}$/p' "$ROOT/src/cli/arch-provision-owner")"
region_root=$scratch/region
mkdir -p "$region_root/arch/default/regions/cn" "$region_root/arch/src/cli" "$region_root/etc/arch"
printf 'Asia/Shanghai\nAsia/Urumqi\n' >"$region_root/arch/default/regions/cn/timezones"
printf '#!/bin/bash\necho "apply $*" >>"$REGION_LOG"\n' >"$region_root/arch/src/cli/arch-apply-pacman"
chmod +x "$region_root/arch/src/cli/arch-apply-pacman"
export ARCH_FORM_DEFAULTS=$region_root/etc/arch/form-defaults ARCH_REGION_FILE=$region_root/etc/arch/region \
  ARCH_PACMAN_CONF=$region_root/etc/pacman.conf ARCH_REGION_TARGET=$region_root REGION_LOG=$region_root/log
printf '[arch]\nServer = https://pkgs.arch.cn/stable/$arch\nServer = https://pkgs.github.com/kairosci/os/stable/$arch\n' >"$ARCH_PACMAN_CONF"
settle() {
  timezone=$1
  printf 'cn\n' >"$ARCH_REGION_FILE"
  : >"$REGION_LOG"
  ARCH_PATH=$region_root/arch configure_region
  [[ -e $ARCH_REGION_FILE ]] && cat "$ARCH_REGION_FILE" || echo global
}
printf 'KEYBOARD=Chinese (Simplified, Pinyin)\nTIMEZONE=Asia/Shanghai\nREGION=cn\n' >"$ARCH_FORM_DEFAULTS"
for case in Asia/Shanghai:cn UTC:cn Europe/Copenhagen:cn Asia/Hong_Kong:global Hongkong:global Asia/Macau:global Asia/Macao:global Asia/Taipei:global ROC:global; do
  [[ $(settle "${case%%:*}") == "${case#*:}" ]] || fail "an owner in ${case%%:*} gets the ${case#*:} region"
  if [[ ${case#*:} == global ]]; then
    grep -qx "apply stable $region_root" "$REGION_LOG" || fail "leaving China re-renders pacman for the installed channel" "$(cat "$REGION_LOG")"
  else
    [[ ! -s $REGION_LOG ]] || fail "keeping the region leaves pacman alone"
  fi
done
printf 'KEYBOARD=English (US)\n' >"$ARCH_FORM_DEFAULTS"
[[ $(settle Asia/Taipei) == cn && ! -s $REGION_LOG ]] || fail "a region the media did not choose is left alone"
pass "a deferred install settles the media's region against the owner's timezone, and Hong Kong, Macau and Taiwan are always World"
