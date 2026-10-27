echo "Normalize Snapper snapshot services"

ARCH_PATH="${ARCH_PATH:-/usr/share/arch}"
snapper_setup_script=/usr/share/arch/src/python/installer/system_setup/snapper_setup.py
if [[ ! -f $snapper_setup_script ]]; then
  snapper_setup_script="$ARCH_PATH/src/python/installer/system_setup/snapper_setup.py"
fi

as_root() {
  if (( EUID == 0 )); then
    "$@"
  else
    sudo "$@"
  fi
}

unit_enabled() {
  systemctl is-enabled --quiet "$1" >/dev/null 2>&1
}

unit_active() {
  systemctl is-active --quiet "$1" >/dev/null 2>&1
}

needs_repair=0

[[ -f /etc/snapper/configs/root ]] || needs_repair=1

if ! unit_enabled snapper-cleanup.timer || ! unit_active snapper-cleanup.timer; then
  needs_repair=1
fi

if ! unit_enabled limine-snapper-sync.service || ! unit_active limine-snapper-sync.service; then
  needs_repair=1
fi

(( needs_repair )) || exit 0

as_root env ARCH_PATH="$ARCH_PATH" python3 -I "$snapper_setup_script"
