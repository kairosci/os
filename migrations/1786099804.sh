echo "Rename the model usage widget to agents and prime its data files"

# The widget formerly known as arch.model-usage is now arch.agents, and
# it no longer scans providers itself: it displays the records that
# arch-agent-usage-update writes under ~/.local/state/arch/agents/usage/.
# Rename the widget wherever a user's config mentions it — bar layout entries
# keep their settings, a disabled widget stays disabled — then generate the
# records once so the bar doesn't sit empty until the widget's first refresh
# timer, and drop the old scanner's cache directory, which nothing reads
# anymore.

config_file="$HOME/.config/arch/shell.json"

if [[ -s $config_file ]]; then
  tmp=$(mktemp)
  jq '
    def rename:
      if . == "arch.model-usage" then
        "arch.agents"
      elif type == "object" and .id == "arch.model-usage" then
        .id = "arch.agents"
      else
        .
      end;

    (if (.bar.layout? | type) == "object" then
      .bar.layout |= map_values(if type == "array" then map(rename) else . end)
    else . end)
    | (if (.disabledPlugins? | type) == "array" then
      .disabledPlugins |= map(rename)
    else . end)
  ' "$config_file" >"$tmp" && mv "$tmp" "$config_file" || rm -f "$tmp"
fi

rm -rf "$HOME/.cache/arch/model-usage"

arch-agent-usage-update || true
