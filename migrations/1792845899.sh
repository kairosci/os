echo "Prepare Arch kernel updates for systemd-boot"

if ! arch-hw-x86 || [[ ! -d /sys/firmware/efi/efivars ]]; then
  exit 0
fi

if ! sudo test -s /boot/EFI/systemd/systemd-bootx64.efi; then
  exit 0
fi

sudo env ARCH_PATH="$ARCH_PATH" python3 -I \
  "$ARCH_PATH/src/python/installer/system_setup/systemd_boot_kernel.py"
