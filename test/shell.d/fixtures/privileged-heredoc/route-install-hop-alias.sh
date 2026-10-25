tmp=/tmp/arch-generated
copy=$tmp
cat >"$tmp" <<EOF
command=$HOME/.local/share/arch/bin/example
EOF
sudo install -m644 "$copy" /etc/arch/example.conf
