# The Marvell Wi-Fi firmware is for x86 Surfaces only; Snapdragon Surfaces use Qualcomm Wi-Fi.
if arch-hw-surface && arch-hw-x86; then
  arch-pkg-add linux-firmware-marvell
fi
