echo "Let Chromium use the cameras of Snapdragon laptops through PipeWire"

if arch-hw-aarch64-qualcomm; then
  python3 -I "$ARCH_PATH/src/python/installer/hardware/qualcomm_camera.py"
  arch-install-camera

  echo "Log out and back in to load the PipeWire camera backend."
fi
