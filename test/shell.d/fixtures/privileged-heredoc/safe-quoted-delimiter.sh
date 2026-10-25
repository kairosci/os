cat <<'EOF' | sudo tee /etc/udev/rules.d/99-arch.rules >/dev/null
SUBSYSTEM=="power_supply", RUN+="/usr/bin/arch-powerprofiles-set $HOME"
EOF

cat <<"XML" | sudo tee /etc/arch/agent.xml >/dev/null
<config path="$HOME/.local/share/arch" />
XML
