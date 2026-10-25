# Set default XCompose that is triggered with Shift + CapsLock
tee ~/.XCompose >/dev/null <<EOF
# Run arch-restart-xcompose to apply changes

# Include fast emoji access
include "/usr/share/arch/default/xcompose"

# Identification
<Multi_key> <space> <n> : "$ARCH_USER_NAME"
<Multi_key> <space> <e> : "$ARCH_USER_EMAIL"
EOF
