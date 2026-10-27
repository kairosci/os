echo "Finish Arch Linux branding for the login and splash screens"

sudo env ARCH_PATH="$ARCH_PATH" python3 -I \
  "$ARCH_PATH/src/python/installer/system_setup/branding.py"
