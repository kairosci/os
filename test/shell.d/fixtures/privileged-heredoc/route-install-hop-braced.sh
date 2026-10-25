tmp=/tmp/arch-generated
cat >"$tmp" <<EOF
command=$HOME/.local/share/arch/bin/example
EOF
sudo install -m644 "${tmp}" /etc/arch/example.conf
