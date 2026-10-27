echo "Remove coding agent CLI shims from mise"

if arch-cmd-present mise; then
  mise reshim --system
  mise reshim
fi
