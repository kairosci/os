echo "Set the Arch UKI as the persistent systemd-boot default"

systemd_boot_esp="${ARCH_SYSTEMD_BOOT_ESP:-/boot}"
loader_conf="${ARCH_SYSTEMD_BOOT_LOADER_CONF:-$systemd_boot_esp/loader/loader.conf}"
[[ -s $systemd_boot_esp/EFI/systemd/systemd-bootx64.efi ]] || exit 0

if ! sudo bootctl --esp-path="$systemd_boot_esp" list | grep -Fq 'id: os_linux.efi'; then
  echo "The Arch Linux UKI is missing from the systemd-boot menu; leaving the default entry unchanged." >&2
  exit 1
fi

sudo install -d -m 0755 "$(dirname "$loader_conf")"
sudo touch "$loader_conf"
sudo sed -i -E '/^[[:space:]]*default[[:space:]]+/d' "$loader_conf"
printf '%s\n' 'default os_linux.efi' | sudo tee -a "$loader_conf" >/dev/null
sudo bootctl --esp-path="$systemd_boot_esp" set-default os_linux.efi
