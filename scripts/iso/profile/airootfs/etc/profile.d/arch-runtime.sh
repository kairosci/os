if [[ -r /usr/share/arch/src/python/runtime/environment_bootstrap.py ]]; then
  arch_runtime_exports=$(/usr/bin/python3 -I /usr/share/arch/src/python/runtime/environment_bootstrap.py --shell) || return 1
  eval "$arch_runtime_exports"
  unset arch_runtime_exports
fi
