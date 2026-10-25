if arch-hw-x86 && [[ -f /boot/EFI/systemd/systemd-bootx64.efi ]]; then
  install -Dm755 "$ARCH_PATH/installer/boot/systemd-boot-snapper-plugin.sh" \
    /usr/lib/snapper/plugins/10-arch-systemd-boot
  systemctl disable --now limine-snapper-sync.service arch-snapshot-entries.path \
    arch-snapshot-entries.service >/dev/null 2>&1 || true
  chmod a-x /usr/lib/snapper/plugins/10-limine-snapper-sync 2>/dev/null || true
  rm -f -- /etc/systemd/system/arch-snapshot-entries.path \
    /etc/systemd/system/arch-snapshot-entries.service \
    /usr/local/libexec/arch-sync-systemd-boot-snapshots
  systemctl daemon-reload
fi
