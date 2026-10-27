echo "Remove the retired agent usage widget from user shell configuration"

config_file="${XDG_CONFIG_HOME:-$HOME/.config}/arch/shell.json"
[[ -s $config_file ]] || exit 0
config_file=$(realpath -e -- "$config_file")
tmp=$(mktemp "${config_file}.XXXXXX")
if jq '
  def retired_agent_widget:
    if type == "string" then . == "arch.agents"
    elif type == "object" then .id? == "arch.agents"
    else false
    end;

  (if (.bar.layout? | type) == "object" then
    .bar.layout |= map_values(if type == "array" then map(select((retired_agent_widget | not))) else . end)
  else . end)
  | (if (.disabledPlugins? | type) == "array" then
    .disabledPlugins |= map(select(. != "arch.agents"))
  else . end)
' "$config_file" >"$tmp"; then
  chmod --reference="$config_file" "$tmp"
  mv "$tmp" "$config_file"
else
  rm -f "$tmp"
  exit 1
fi
