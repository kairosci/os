mkdir -p ~/.config/arch

cat >~/.config/arch/agent.conf <<EOF
helper=$HOME/.local/share/arch/bin/arch-agent
EOF

cat >"$HOME/.local/bin/arch-shim" <<EOF
exec "$ARCH_PATH/src/commands/arch-agent" "$@"
EOF
