# A language the install media preset (/etc/arch/language) becomes this
# user's desktop language; the system step generated its locale.
code=
language_file=/etc/arch/language
[[ -r $language_file ]] || language_file=/etc/arch/language
[[ -r $language_file ]] && read -r code <"$language_file"
if [[ -n $code ]]; then
  "$ARCH_PATH/src/cli/arch-language" seed "$code" || echo "Could not set the preset language $code" >&2
fi
