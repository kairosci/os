echo "Finish Arch Linux branding for the login and splash screens"

sudo env ARCH_PATH="$ARCH_PATH" bash -euo pipefail -c \
  'source "$ARCH_PATH/installer/config/arch-branding.sh"'
