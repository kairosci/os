echo "Prepare Arch kernel updates for systemd-boot"

if ! arch-hw-x86 || [[ ! -d /sys/firmware/efi/efivars ]]; then
  exit 0
fi

if ! sudo test -s /boot/EFI/systemd/systemd-bootx64.efi; then
  exit 0
fi

sudo env ARCH_PATH="$ARCH_PATH" bash -euo pipefail -c \
  'source "$ARCH_PATH/install/config/systemd-boot-kernel.sh"'
