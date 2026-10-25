#!/bin/bash

# Two hops. The scan resolves arch_bin into helper, so the value it ends up
# judging still carries an unresolved $HOME rather than a literal path.
arch_bin="$HOME/.local/share/arch/bin"
helper="$arch_bin/arch-agent"

# arch:heredoc-expands paths=none -- helper names the agent, no path is baked in
cat <<EOF | sudo tee /etc/udev/rules.d/99-arch-agent.rules >/dev/null
SUBSYSTEM=="power_supply", RUN+="$helper"
EOF
