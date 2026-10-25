servers="1.1.1.1 9.9.9.9"

# arch:heredoc-expands paths=none -- $servers is a validated IP list, not a path
cat <<EOF | sudo tee /etc/arch/dns.conf >/dev/null
servers=$servers
EOF

# arch:heredoc-expands paths=storage -- validated by valid_path and symlink-checked before use
cat <<EOF | sudo tee /var/lib/arch/mounts.conf >/dev/null
source=$storage:/storage
EOF
