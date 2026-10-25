configure_systemd_boot_kernel() {
  local systemd_boot_esp="${ARCH_SYSTEMD_BOOT_KERNEL_ESP:-/boot}"
  local mkinitcpio_config_dir="${ARCH_MKINITCPIO_CONFIG_DIR:-/etc/mkinitcpio.d}"
  local kernel_cmdline_file="${ARCH_KERNEL_CMDLINE_FILE:-/etc/kernel/cmdline}"
  local kernel_uki="${ARCH_KERNEL_UKI:-$systemd_boot_esp/EFI/Linux/os_linux.efi}"
  local kernel_preset="$mkinitcpio_config_dir/linux.preset"
  local kernel_preset_template="${ARCH_KERNEL_PRESET_TEMPLATE:-$ARCH_PATH/default/mkinitcpio/linux.preset}"
  local mkinitcpio_default_preset="${ARCH_MKINITCPIO_DEFAULT_PRESET:-/usr/share/mkinitcpio/hook.preset}"
  local hw_x86_helper="${ARCH_HW_X86_HELPER:-$ARCH_PATH/bin/arch-hw-x86}"
  local kernel_cmdline_dir temporary_section temporary_cmdline temporary_default_preset temporary_legacy_preset
  local embedded_cmdline argument key
  local -a cmdline_arguments=() embedded_arguments=()
  local -A existing_cmdline_keys=() existing_cmdline_flags=()

  "$hw_x86_helper" || return 0
  [[ -s $systemd_boot_esp/EFI/systemd/systemd-bootx64.efi ]] || return 0

  if [[ ! -s $kernel_uki ]]; then
    echo "The systemd-boot Arch UKI is missing at $kernel_uki." >&2
    return 1
  fi

  kernel_cmdline_dir=$(dirname "$kernel_cmdline_file")
  mkdir -p "$kernel_cmdline_dir"
  temporary_section=$(mktemp)
  if ! objcopy -O binary --only-section=.cmdline "$kernel_uki" "$temporary_section"; then
    rm -f -- "$temporary_section"
    echo "Could not read the embedded command line from $kernel_uki." >&2
    return 1
  fi
  embedded_cmdline=$(tr -d '\0' <"$temporary_section")
  rm -f -- "$temporary_section"
  read -r -a embedded_arguments <<<"$embedded_cmdline"

  if [[ -s $kernel_cmdline_file ]]; then
    read -r -a cmdline_arguments <"$kernel_cmdline_file"
  fi

  for argument in "${cmdline_arguments[@]}"; do
    if [[ $argument == *=* ]]; then
      key=${argument%%=*}
      existing_cmdline_keys[$key]=true
    else
      existing_cmdline_flags[$argument]=true
    fi
  done

  for argument in "${embedded_arguments[@]}"; do
    if [[ $argument == *=* ]]; then
      key=${argument%%=*}
      [[ ${existing_cmdline_keys[$key]:-} ]] && continue
      existing_cmdline_keys[$key]=true
    else
      [[ ${existing_cmdline_flags[$argument]:-} ]] && continue
      existing_cmdline_flags[$argument]=true
    fi
    cmdline_arguments+=("$argument")
  done

  if ! printf '%s\n' "${cmdline_arguments[*]}" | grep -Eq '(^|[[:space:]])root='; then
    echo "The command line in $kernel_uki and $kernel_cmdline_file has no root= parameter." >&2
    return 1
  fi

  temporary_cmdline=$(mktemp "$kernel_cmdline_dir/.cmdline.XXXXXX")
  printf '%s\n' "${cmdline_arguments[*]}" >"$temporary_cmdline"
  chmod 0644 "$temporary_cmdline"
  mv -f -- "$temporary_cmdline" "$kernel_cmdline_file"

  mkdir -p "$mkinitcpio_config_dir"
  if [[ -e $kernel_preset ]] && ! cmp -s "$kernel_preset" "$kernel_preset_template"; then
    temporary_default_preset=$(mktemp)
    temporary_legacy_preset=$(mktemp)
    cat >"$temporary_legacy_preset" <<'PRESET'
# mkinitcpio preset for Arch Linux on systemd-boot.

ALL_config="/etc/mkinitcpio.conf"
ALL_kver="/boot/vmlinuz-linux"
ALL_cmdline="/etc/kernel/cmdline"

PRESETS=('default' 'fallback')

default_uki="/boot/EFI/Linux/os_linux.efi"
fallback_uki="/boot/EFI/Linux/os_linux-fallback.efi"
fallback_options="-S autodetect"
PRESET
    if [[ -r $mkinitcpio_default_preset ]]; then
      sed 's|%PKGBASE%|linux|g' "$mkinitcpio_default_preset" >"$temporary_default_preset"
    fi

    if { [[ ! -s $temporary_default_preset ]] || ! cmp -s "$kernel_preset" "$temporary_default_preset"; } \
      && ! cmp -s "$kernel_preset" "$temporary_legacy_preset"; then
      rm -f -- "$temporary_default_preset" "$temporary_legacy_preset"
      echo "Preserving custom mkinitcpio preset at $kernel_preset." >&2
      return 1
    fi

    rm -f -- "$temporary_default_preset" "$temporary_legacy_preset"
  fi

  install -Dm 0644 "$kernel_preset_template" "$kernel_preset"
  echo "Configured the Arch kernel UKI for mkinitcpio and systemd-boot."
}

configure_systemd_boot_kernel
kernel_setup_status=$?
unset -f configure_systemd_boot_kernel
return "$kernel_setup_status"
