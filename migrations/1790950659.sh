echo "Light the N1x panel for Plymouth's LUKS prompt"

# See src/python/installer/hardware/n1x.py: the panel stays at its dim power-on backlight
# until the NVIDIA backlight is first written, which only happened after unlock.
# Only N1x installs where the GPU drives the panel have that backlight.
gpu_conf="${ARCH_N1X_GPU_CONF:-/etc/limine-entry-tool.d/00-arch-n1x-gpu.conf}"
initcpio_dir="${ARCH_INITCPIO_DIR:-/etc/initcpio}"
hooks_conf="${ARCH_N1X_BRIGHTNESS_HOOKS_CONF:-/etc/mkinitcpio.conf.d/zz-arch-n1x-boot-brightness.conf}"
rebuild_marker="${ARCH_LIMINE_REBUILD_MARKER:-/var/lib/arch/migrations/1790950659}"

[[ -f $gpu_conf ]] || exit 0

sudo install -Dm644 /dev/stdin "$initcpio_dir/install/arch-n1x-boot-brightness" <<'EOF'
#!/bin/bash

build() {
    add_runscript
}

help() {
    cat <<HELPEOF
Light the NVIDIA N1x panel for Plymouth's LUKS prompt.
HELPEOF
}
EOF

sudo install -Dm644 /dev/stdin "$initcpio_dir/hooks/arch-n1x-boot-brightness" <<'EOF'
#!/usr/bin/ash

# The panel stays at its dim power-on backlight until the NVIDIA backlight is
# first written, which systemd-backlight only does once the root filesystem is
# unlocked. Write it here so Plymouth's LUKS prompt is readable;
# systemd-backlight restores the saved level after unlock.
run_hook() {
    if [ -w /sys/class/backlight/nvidia_0/brightness ]; then
        echo 60 > /sys/class/backlight/nvidia_0/brightness
    fi
}
EOF

sudo install -Dm644 /dev/stdin "$hooks_conf" <<'EOF'
# N1x: light the panel for Plymouth's LUKS prompt; see src/python/installer/hardware/n1x.py.
# Sorts after arch_hooks.conf so HOOKS is already set.
_arch_n1x_hooks=()
for _arch_n1x_hook in "${HOOKS[@]}"; do
  _arch_n1x_hooks+=("$_arch_n1x_hook")
  [[ $_arch_n1x_hook == plymouth ]] && _arch_n1x_hooks+=(arch-n1x-boot-brightness)
done
HOOKS=("${_arch_n1x_hooks[@]}")
unset _arch_n1x_hooks _arch_n1x_hook
EOF

# The hook only takes effect once it is in the initramfs. A marker records the
# machine-wide rebuild so another user's run skips it, while a missing marker
# still retries an interrupted one.
[[ ! -e $rebuild_marker ]] || exit 0

sudo limine-mkinitcpio
sudo install -Dm644 /dev/null "$rebuild_marker"
