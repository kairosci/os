echo "Update the Hyprland entry point to the Arch defaults module"

target="$HOME/.config/hypr/hyprland.lua"
[[ -f $target ]] || exit 0
grep -q 'default\.hypr\.arch' "$target" || exit 0

temporary=$(mktemp "${target}.XXXXXX")
if ! sed 's/default\.hypr\.arch/default.hypr.arch/g' "$target" >"$temporary"; then
  rm -f -- "$temporary"
  exit 1
fi
chmod --reference="$target" "$temporary"
mv -- "$temporary" "$target"
