# arch:heredoc-expands paths=none -- the positional argument is a scalar
sudo tee /etc/arch/example.conf <<EOF
argument=$1
command=$HOME/.local/share/arch/bin/example
EOF
