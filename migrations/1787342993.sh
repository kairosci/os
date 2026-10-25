echo "Install ori (OpenRouter's agent harness) via mise wrapper"

if [[ ! -f $HOME/.local/state/arch/preinstalls-removed ]]; then
  arch-mise-install github:OpenRouterLabs/ori-releases ori
fi
