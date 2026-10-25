echo "Install hey (hey-cli) via mise wrapper"

if [[ ! -f $HOME/.local/state/arch/preinstalls-removed ]]; then
  arch-mise-install github:basecamp/hey-cli hey
fi
