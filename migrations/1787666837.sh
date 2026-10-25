echo "Enable Dell XPS 13 sidecar speaker amplifiers"

if arch-hw-dell-xps13-sidecar-amps; then
  source "$ARCH_PATH/installer/hardware/dell-xps13-sidecar-amps.sh"
  arch-state set reboot-required
fi
