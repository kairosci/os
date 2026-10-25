echo "Install Hype, the Markdown presentation app"

if [[ ! -f $HOME/.local/state/arch/preinstalls-removed ]]; then
  arch-pkg-add hype
fi
