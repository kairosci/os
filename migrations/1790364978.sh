echo "Disable system sleep on GB10 machines, as DGX OS does"

# Suspend has not been shown to work on GB10 machines. Existing installs predate
# the install-time setting, so apply it here too.
arch-hw-aarch64-gb10 || exit 0
arch-sleep-disabled && exit 0

sudo bash "$ARCH_PATH/install/hardware/gb10/sleep.sh"
