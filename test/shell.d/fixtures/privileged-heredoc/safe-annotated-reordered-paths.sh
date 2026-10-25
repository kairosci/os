storage="$HOME/storage"
shared="$HOME/shared"

# arch:heredoc-expands paths=shared,storage -- both sources are validated before use
cat >/etc/arch/mounts.conf <<EOF
storage=$storage:/storage
shared=$shared:/shared
EOF
