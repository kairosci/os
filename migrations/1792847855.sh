echo "Apply Arch Linux identity to the installed system"

if ! grep -Fqx 'PRETTY_NAME="Arch Linux"' /etc/os-release || ! grep -Fqx 'LOGO=archlinux-logo' /etc/os-release; then
  sudo env ARCH_PATH="$ARCH_PATH" python3 -I \
    "$ARCH_PATH/src/python/installer/system_setup/branding.py"
fi

terminal_desktop="$HOME/.local/share/applications/org.arch.terminal.desktop"
if [[ -f $terminal_desktop ]]; then
  sed -i \
    -e 's/^Name=os Terminal$/Name=Terminal/' \
    -e 's/^Comment=Open the default terminal for os$/Comment=Open the default terminal for Arch Linux/' \
    "$terminal_desktop"
fi
