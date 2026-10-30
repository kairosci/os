if [[ -r /usr/share/arch/default/bash/env-bootstrap ]]; then
  . /usr/share/arch/default/bash/env-bootstrap || return 1
fi
