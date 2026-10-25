cat <<EOF | sudo tee /etc/udev/rules.d/99-arch.rules >/dev/null
SUBSYSTEM=="power_supply", ATTR{type}=="Mains", RUN+="/usr/bin/arch-powerprofiles-set"
EOF
