#!/bin/bash

set -euo pipefail

# Replace the old desktop id so launchers, windows and application matching all
# identify this as the Arch terminal. The user's xdg-terminals.list still
# selects kitty.desktop, preserving Kitty as the default emulator.
bash "$ARCH_PATH/installer/user/terminal.sh"
