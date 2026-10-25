# Install media can preset the desktop language for its users. The marker is a
# registry code, read as data; the system locale stays English, because the
# console cannot draw every script, and the language applies per user.
marker=${ARCH_LANGUAGE_MARKER:-/etc/arch/language}
if [[ ! -r $marker && -r /etc/arch/language ]]; then
  marker=/etc/arch/language
fi
code=
[[ -r $marker ]] && read -r code <"$marker"
if [[ -n $code ]]; then
  locales=${ARCH_LOCALES_JSON:-$ARCH_PATH/default/i18n/locales.json}
  if [[ $code =~ ^[a-z]{2,3}(-[A-Z]{2})?$ ]] && jq -e --arg code "$code" 'has($code)' "$locales" >/dev/null 2>&1; then
    "$ARCH_PATH/bin/arch-locale-generate" "$code"
  else
    echo "Ignoring an invalid language in $marker: $code" >&2
  fi
fi
