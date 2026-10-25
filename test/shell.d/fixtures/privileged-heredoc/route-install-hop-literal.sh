#!/bin/bash

cat <<EOF >/tmp/arch-review-unit
[Service]
ExecStart=$HOME/.local/bin/payload
EOF
sudo install -m 644 /tmp/arch-review-unit /etc/systemd/system/review.service
