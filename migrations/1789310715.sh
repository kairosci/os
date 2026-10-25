echo "Install cf (Cloudflare CLI) via mise wrapper"

if [[ ! -f $HOME/.local/state/arch/preinstalls-removed ]]; then
  arch-mise-install npm:cf cf
fi
