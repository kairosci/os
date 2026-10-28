DROP_IN=/etc/systemd/system/arch-agent.service.d/override.conf

cat <<EOF | sudo tee "$DROP_IN" >/dev/null
[Service]
ExecStart=$AP/src/arch/commands/arch-agent
EOF
