# fix for screen readers
if grep -Fqa 'accessibility=' /proc/cmdline &> /dev/null; then
    setopt SINGLE_LINE_ZLE
fi

arch_runtime_exports=$(/usr/bin/python3 -I /usr/share/arch/src/python/runtime/environment_bootstrap.py --shell) || return 1
eval "$arch_runtime_exports"
unset arch_runtime_exports

~/.automated_script.sh

if [[ $(tty) == "/dev/tty1" ]]; then
    printf '\n%s\n\n' 'To install Arch with the guided installer, run: os install system'
fi
