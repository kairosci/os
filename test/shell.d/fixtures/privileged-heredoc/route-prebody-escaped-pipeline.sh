#!/bin/bash

cat <<EOF | \
  sudo tee /etc/arch/review.conf
ExecStart=$HOME/.local/bin/payload
EOF
