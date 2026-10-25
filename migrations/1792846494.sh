echo "Install the systemd-boot Snapper hook"

systemd_boot_esp="${ARCH_SYSTEMD_BOOT_ESP:-/boot}"
[[ -s $systemd_boot_esp/EFI/systemd/systemd-bootx64.efi ]] || exit 0

if ! sudo bootctl --esp-path="$systemd_boot_esp" list | grep -Fq 'id: os_linux.efi'; then
  echo "The Arch Linux UKI is missing from the systemd-boot menu; leaving the default entry unchanged." >&2
  exit 1
fi

sudo bootctl --esp-path="$systemd_boot_esp" set-default os_linux.efi

sudo env ARCH_PATH="$ARCH_PATH" bash -euo pipefail -c \
  'source "$ARCH_PATH/installer/config/systemd-boot-snapshots.sh"'
