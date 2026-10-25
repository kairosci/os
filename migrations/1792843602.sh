echo "Switch x86 UEFI systems from Limine to systemd-boot"

if ! arch-hw-x86 || [[ ! -d /sys/firmware/efi/efivars ]]; then
  exit 0
fi

if ! sudo bootctl status 2>/dev/null | grep -q 'Product: Limine'; then
  exit 0
fi

if [[ $(findmnt -n -o FSTYPE --target /boot) != "vfat" ]]; then
  echo "The EFI system partition is not mounted at /boot; leaving the boot setup unchanged." >&2
  exit 1
fi

arch-pkg-add linux linux-headers

sudo install -Dm0644 "$ARCH_PATH/etc/limine-entry-tool.d/arch-defaults.conf" \
  /etc/limine-entry-tool.d/arch-defaults.conf
if [[ $(arch-kernel get) != "linux" ]]; then
  sudo arch-kernel set linux
else
  sudo limine-mkinitcpio linux
fi

uki=/boot/EFI/Linux/os_linux.efi
if ! sudo test -s "$uki"; then
  echo "The Arch kernel UKI was not created at $uki; leaving systemd-boot uninstalled." >&2
  exit 1
fi

sudo install -Dm0644 "$ARCH_PATH/etc/loader/loader.conf" /boot/loader/loader.conf
sudo bootctl --esp-path=/boot install
sudo systemctl enable systemd-boot-update.service

sudo env ARCH_PATH="$ARCH_PATH" bash -c \
  'source "$ARCH_PATH/install/config/systemd-boot-snapshots.sh"'

if ! sudo bootctl --esp-path=/boot list | grep -Fq 'id: os_linux.efi'; then
  echo "systemd-boot does not list the Arch kernel UKI; leaving Limine as the active loader." >&2
  exit 1
fi

echo "systemd-boot is first in the firmware boot order. The Limine EFI entry remains available until the first successful systemd-boot start."
