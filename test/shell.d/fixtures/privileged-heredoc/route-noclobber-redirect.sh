# `>|` is a plain redirect with noclobber overridden, not a redirect into a pipe.
cat >|/etc/arch/agent.conf <<EOF
helper=$HOME/.local/share/arch/bin/arch-agent
EOF
