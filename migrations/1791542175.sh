echo "Install Gliff, the Hyprland remote desktop over SSH"

# Gliff has no aarch64 build (installer/arch-x86_64-only.packages).
if arch-hw-x86; then
  arch-pkg-add gliff
fi
