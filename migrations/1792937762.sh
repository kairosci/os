echo "Remove saved floating workspace layouts"

# Floating layouts are no longer supported. Preserve each affected workspace
# as a tiled dwindle workspace, including older state roots set through XDG.
for state_home in "$HOME/.local/state" "${XDG_STATE_HOME:-}"; do
  [[ -n $state_home ]] || continue
  for saved in "$state_home"/arch/workspace-layouts/*.lua; do
    [[ -f $saved ]] || continue
    sed -i --follow-symlinks \
      -e 's/mode = "floating"/mode = "dwindle"/g' \
      -e 's/default = "floating"/default = "dwindle"/g' \
      "$saved"
  done
done
