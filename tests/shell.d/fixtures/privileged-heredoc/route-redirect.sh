# A plain redirect into /etc, no sudo: the command re-execs itself as root.
cat >/etc/arch/agent.conf <<EOF
helper=$HOME/.local/share/arch/bin/arch-agent
EOF
