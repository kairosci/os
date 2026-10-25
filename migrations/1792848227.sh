echo "Remove the retired kernel after booting the Arch kernel with systemd-boot"

arch-hw-x86 || exit 0

modules_dir="${ARCH_KERNEL_MODULES_DIR:-/usr/lib/modules}"

bootloader_status=$(bootctl status --no-pager 2>/dev/null) || bootloader_status=""
if ! grep -Eq '^[[:space:]]*Product: systemd-boot([[:space:]]|$)' <<<"$bootloader_status"; then
  echo "systemd-boot is not running yet; reboot into the Arch UKI, then run arch-migrate again." >&2
  exit 75
fi

running_kernel=$(uname -r)
pkgbase_file="$modules_dir/$running_kernel/pkgbase"
if [[ ! -r $pkgbase_file ]] || [[ $(<"$pkgbase_file") != "linux" ]]; then
  echo "The running kernel is not the Arch linux package; keeping linux installed." >&2
  exit 75
fi

arch-pkg-drop linux linux-headers
