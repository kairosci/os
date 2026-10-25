echo "Install oh-my-pi (omp) via mise wrapper"

if [[ ! -f $HOME/.local/state/arch/preinstalls-removed ]]; then
  arch-mise-install github:can1357/oh-my-pi omp
fi
