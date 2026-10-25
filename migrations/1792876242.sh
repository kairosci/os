echo "Migrate built-in shell plugin IDs to Arch"

rewrite_json() {
  local target="$1" convert_metadata="$2" temporary

  [[ -f $target ]] || return 0
  temporary=$(mktemp "${target}.XXXXXX")
  if [[ $convert_metadata == true ]]; then
    if ! jq '
      walk(if type == "string" and startswith("arch.")
        then "arch." + ltrimstr("arch.")
        else .
        end)
      | if (.bar.transparent? == true) then .bar.background = "glassy" | del(.bar.transparent) else . end
      | if has("arch") then .arch = (.arch // .arch) | del(.arch) else . end
    ' "$target" >"$temporary"; then
      rm -f -- "$temporary"
      return 1
    fi
  else
    if ! jq '
      walk(if type == "string" and startswith("arch.")
        then "arch." + ltrimstr("arch.")
        else .
        end)
      | if (.bar.transparent? == true) then .bar.background = "glassy" | del(.bar.transparent) else . end
    ' "$target" >"$temporary"; then
      rm -f -- "$temporary"
      return 1
    fi
  fi
  chmod --reference="$target" "$temporary"
  mv -- "$temporary" "$target"
}

rewrite_json "$HOME/.config/arch/shell.json" false

shopt -s nullglob
for manifest in "$HOME"/.config/arch/plugins/*/manifest.json; do
  rewrite_json "$manifest" true
done
