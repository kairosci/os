set -euo pipefail
source_root=$ARCH_PATH
backup_dir="/var/backups/arch-branding-$(date +%Y%m%d-%H%M%S)"
replace_file() {
  local source=$1 target=$2
  if [[ -e $target ]] && cmp -s "$source" "$target"; then
    return 0
  fi
  if [[ -e $target ]]; then
    mkdir -p "$backup_dir"
    cp --parents "$target" "$backup_dir"
  fi
  install -Dm644 "$source" "$target"
}
replace_file "$source_root/etc/os-release" /etc/os-release
replace_file "$source_root/etc/fastfetch/config.jsonc" /etc/fastfetch/config.jsonc
replace_file "$source_root/arch-mark.svg" /usr/share/pixmaps/arch-mark.svg
replace_file "$source_root/etc/sddm.conf.d/10-theme.conf" /etc/sddm.conf.d/10-theme.conf
replace_file "$source_root/etc/plymouth/plymouthd.conf" /etc/plymouth/plymouthd.conf
session_dir=${ARCH_WAYLAND_SESSIONS_DIR:-/usr/local/share/wayland-sessions}
replace_file "$source_root/default/wayland-sessions/arch.desktop" "$session_dir/arch.desktop"
install -d /usr/share/sddm/themes/arch /usr/share/plymouth/themes/arch
cp -a "$source_root/default/sddm/arch/." /usr/share/sddm/themes/arch/
cp -a "$source_root/default/plymouth/." /usr/share/plymouth/themes/arch/
replace_file "$source_root/logo.svg" /usr/share/sddm/themes/arch/os.svg
replace_file "$source_root/default/plymouth/logo.png" /usr/share/plymouth/themes/arch/logo.png
install -Dm644 "$source_root/default/bashrc" /etc/skel/.bashrc
if ! grep -Fqx 'Theme=arch' /etc/plymouth/plymouthd.conf; then
  plymouth-set-default-theme arch --rebuild-initrd
fi
for target in /boot/limine.conf /boot/limine/limine.conf /etc/default/limine; do
  if [[ -f $target ]] && grep -q 'Arch' "$target"; then
    mkdir -p "$backup_dir"
    cp --parents "$target" "$backup_dir"
    sed -i 's/Arch/Arch Linux/g' "$target"
  fi
done
printf 'Backup: %s\n' "$backup_dir"
