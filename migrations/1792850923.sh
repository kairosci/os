echo "Refresh the Arch UKI metadata and select it as the default boot entry"

arch-hw-x86 || exit 0

bootloader_status=$(sudo bootctl status --no-pager 2>/dev/null) || bootloader_status=""
if ! grep -Eq '^[[:space:]]*Product: systemd-boot([[:space:]]|$)' <<<"$bootloader_status"; then
  echo "systemd-boot is not running yet; keeping the UKI refresh pending." >&2
  exit 75
fi

running_kernel=$(uname -r)
modules_dir="${ARCH_KERNEL_MODULES_DIR:-/usr/lib/modules}"
pkgbase_file="$modules_dir/$running_kernel/pkgbase"
if [[ ! -r $pkgbase_file ]] || [[ $(<"$pkgbase_file") != "linux" ]]; then
  echo "The running kernel is not the Arch linux package; keeping the UKI refresh pending." >&2
  exit 75
fi

os_release_file="${ARCH_OS_RELEASE_FILE:-/etc/os-release}"
if ! grep -Fxq 'NAME="Arch Linux"' "$os_release_file" || ! grep -Fxq 'ID=arch' "$os_release_file"; then
  echo "/etc/os-release does not identify Arch Linux; keeping the UKI refresh pending." >&2
  exit 75
fi

uki="${ARCH_ARCH_UKI:-/boot/EFI/Linux/os_linux.efi}"
os_release=$(mktemp)
trap 'rm -f -- "$os_release"' EXIT

sudo env ARCH_PATH="$ARCH_PATH" python3 -I \
  "$ARCH_PATH/src/python/installer/system_setup/systemd_boot_kernel.py"
sudo mkinitcpio -P

read_uki_os_release() {
  sudo objcopy -O binary --only-section=.osrel "$uki" "$os_release"
}

if ! read_uki_os_release || ! grep -Fxq 'NAME="Arch Linux"' "$os_release" || ! grep -Fxq 'ID=arch' "$os_release"; then
  echo "The Arch UKI does not contain Arch Linux metadata after rebuilding." >&2
  exit 1
fi

sudo bootctl set-default os_linux.efi
boot_entries=$(sudo bootctl list --no-pager 2>/dev/null) || boot_entries=""
if ! grep -B 2 -F 'id: os_linux.efi' <<<"$boot_entries" | grep -Fq '(default)'; then
  echo "systemd-boot did not select the Arch UKI as its default entry." >&2
  exit 1
fi
