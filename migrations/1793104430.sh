echo "Remove the retired terminal workspace manager"

arch-pkg-drop arch-herdr herdr

if arch-cmd-present mise && mise ls herdr 2>/dev/null | grep -q herdr; then
  mise unuse -g herdr &>/dev/null || true
  mise uninstall -a herdr &>/dev/null || true
fi

rm -f "$HOME/.local/bin/herdr" "$HOME/.local/share/mise/shims/herdr"
rm -rf "$HOME/.local/share/mise/installs/herdr" "$HOME/.config/herdr"
rm -f "$HOME/.local/state/arch/toggles/herdr-theme-sync"
