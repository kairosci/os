# Arch system packages

The `arch` runtime and `arch-settings` system defaults are built from this
checkout. Together they replace the former runtime and settings packages. The
x86_64 runtime uses the verified systemd-boot and Arch UKI path; Limine and its
mkinitcpio/Snapper integrations are not part of this configuration.

Build both packages from the repository root:

```sh
ARCH_SRC="$PWD" makepkg -Csf --nodeps --dir packages/arch-settings
ARCH_SRC="$PWD" makepkg -Csf --nodeps --dir packages/arch-systemd-boot
```

Install them together so pacman can transfer shared files and resolve the new
dependency in one transaction:

```sh
sudo pacman -U packages/arch-settings/arch-settings-4.0.6-8-x86_64.pkg.tar.zst \
  packages/arch-systemd-boot/arch-4.0.6-37-x86_64.pkg.tar.zst
```

Confirm that the machine has a working systemd-boot entry and Arch UKI before
removing any legacy boot packages. Keep the runtime and settings package
versions aligned: reset `pkgrel` to 1 when `pkgver` changes, otherwise
increment `pkgrel`.
