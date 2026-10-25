echo "Preserve Voxtype as the default for existing dictation users"

backend_config="${XDG_CONFIG_HOME:-$HOME/.config}/arch/defaults/dictation"
if [[ ! -e $backend_config ]] && arch-pkg-present voxtype-bin; then
  mkdir -p "${backend_config%/*}"
  temporary=$(mktemp "$backend_config.XXXXXX")
  printf '%s\n' voxtype > "$temporary"
  mv -f "$temporary" "$backend_config"
fi
