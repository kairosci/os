echo "Give the ASUS ProArt P14 (NVIDIA N1x) speakers ASUS's amplifier tuning and voicing"

# See installer/hardware/asus/fix-asus-proart-p14-speakers.sh and the
# asus-proart-p14-n1x speaker tuning. The amplifiers load the new tuning at the
# next boot, under a linux-n1x that passes them the laptop's subsystem ID.
if ! arch-hw-match "H7407BA"; then
  exit 0
fi

arch-pkg-add asus-proart-p14-speaker-firmware

if arch-audio-tuning match >/dev/null 2>&1; then
  arch-pkg-add lsp-plugins-lv2
  arch-audio-tuning on
fi
