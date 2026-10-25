# Snapdragon cameras run through libcamera, which apps reach through
# PipeWire's libcamera backend.

if arch-hw-aarch64-qualcomm; then
  arch-pkg-add pipewire-libcamera
fi
