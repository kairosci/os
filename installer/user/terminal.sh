install -Dm644 "$ARCH_PATH/applications/org.arch.terminal.desktop" \
  "$HOME/.local/share/applications/org.arch.terminal.desktop"
for entry in "$HOME"/.local/share/applications/*.terminal.desktop; do
  [[ -e $entry ]] || continue
  [[ $entry == "$HOME/.local/share/applications/org.arch.terminal.desktop" ]] && continue
  rm -f "$entry"
done
