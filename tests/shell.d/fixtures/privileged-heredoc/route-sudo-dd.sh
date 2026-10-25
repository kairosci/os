sudo dd status=none of=/etc/arch/boot.conf <<EOF
cmdline=$boot_params
EOF
