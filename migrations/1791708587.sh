echo "Install Signed, the PDF signing app"

if [[ ! -f $HOME/.local/state/arch/preinstalls-removed ]]; then
  arch-pkg-add signed
fi
