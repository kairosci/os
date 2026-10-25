if true; then
  cat <<-EOF | sudo tee /etc/arch/indented.conf >/dev/null
	helper=$HOME/.local/share/arch/bin/arch-agent
	EOF
fi
