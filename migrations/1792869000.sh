#!/bin/bash

set -euo pipefail

echo "Use the Arch-supported mkinitcpio hooks for the stock kernel"

config_dir=${ARCH_MKINITCPIO_CONFIG_DIR:-/etc/mkinitcpio.conf.d}

sudo install -Dm644 "$ARCH_PATH/etc/mkinitcpio.conf.d/00-arch-hooks.conf" \
  "$config_dir/00-arch-hooks.conf"
sudo install -Dm644 "$ARCH_PATH/etc/mkinitcpio.conf.d/arch_hooks.conf" \
  "$config_dir/arch_hooks.conf"
sudo mkinitcpio -P
