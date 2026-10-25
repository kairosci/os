echo "Let Chromium use the cameras of Snapdragon laptops through PipeWire"

if arch-hw-aarch64-qualcomm; then
  source "$ARCH_PATH/install/hardware/qualcomm/camera.sh"
  arch-install-camera

  echo "Log out and back in to load the PipeWire camera backend."
fi
