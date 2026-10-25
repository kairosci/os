#!/bin/bash

# arch:heredoc-expands paths=none -- review regression fixture
sudo tee /etc/arch/review.conf >/dev/null <<EOF
ExecStart=${target:-$HOME/.local/bin/payload}
EOF
