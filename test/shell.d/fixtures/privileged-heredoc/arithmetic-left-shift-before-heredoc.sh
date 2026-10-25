mask=$((1 << bits))

cat >/etc/arch/agent.conf <<EOF
helper=$HOME/.local/share/arch/bin/arch-agent
EOF
