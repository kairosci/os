echo "Enable desktop camera access on Snapdragon ThinkPad T14s Gen 6"

if arch-hw-aarch64-qualcomm && arch-hw-match '^21N[12]'; then
  source "$ARCH_PATH/install/hardware/lenovo/thinkpad-t14s-camera.sh"

  sudo udevadm control --reload
  sudo udevadm trigger --action=add --subsystem-match=dma_heap --sysname-match=system
  sudo udevadm settle

  echo "Log out and back in to load the PipeWire camera backend."
fi
