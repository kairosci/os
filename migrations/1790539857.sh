echo "Install Monologue, the webcam recorder"

if [[ ! -f $HOME/.local/state/arch/preinstalls-removed ]]; then
  arch-pkg-add monologue
fi
