tmp=$(mktemp)

cat >"$tmp" <<EOF
#!/bin/bash
exec "$HOME/.local/share/arch/bin/arch-agent" "$@"
EOF

sudo install -m 0755 "$tmp" /usr/local/bin/arch-agent-shim
