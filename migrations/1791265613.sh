echo "Install the Dell XPS 13 Panther Lake speaker firmware"

if arch-hw-dell-xps13-dx13260-ptl; then
  source "$ARCH_PATH/installer/hardware/dell-xps13-ptl-speaker-firmware.sh"
  arch-state set reboot-required
fi
