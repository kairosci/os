echo "Install Kimi coding agent mise wrapper"

if [[ ! -f $HOME/.local/state/arch/preinstalls-removed ]] && arch-cmd-missing kimi; then
  arch-mise-install npm:@moonshot-ai/kimi-code kimi
fi
