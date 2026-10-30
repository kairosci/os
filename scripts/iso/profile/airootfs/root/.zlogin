# fix for screen readers
if grep -Fqa 'accessibility=' /proc/cmdline &> /dev/null; then
    setopt SINGLE_LINE_ZLE
fi

if [[ -r /usr/share/arch/default/bash/env-bootstrap ]]; then
    source /usr/share/arch/default/bash/env-bootstrap || return 1
fi

~/.automated_script.sh
