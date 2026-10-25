echo "Replace the Gemini coding agent with Antigravity"

ARCH_PATH="${ARCH_PATH:-/usr/share/arch}"

agent_file="$HOME/.config/arch/defaults/agent"
legacy_agent_file="$HOME/.config/arch/defaults/agent"
skills_source="$ARCH_PATH/default/agents/skills"

# Read the default the way arch-default-agent reads it, so this migration and
# the launcher always agree on which agent is selected.
selected_agent=""
if [[ -f $agent_file ]]; then
  read -r selected_agent <"$agent_file" || true
elif [[ -f $legacy_agent_file ]]; then
  read -r selected_agent <"$legacy_agent_file" || true
fi

preinstalls_removed=0
if [[ -f $HOME/.local/state/arch/preinstalls-removed || -f $HOME/.local/state/arch/preinstalls-removed ]]; then
  preinstalls_removed=1
fi

# Choosing Gemini was opting into an agent, so its replacement follows even for
# someone who removed the preinstalls. Otherwise the default rewritten below
# would name a command that is not there.
if arch-cmd-missing agy &&
  { [[ $selected_agent == "gemini" ]] || (( ! preinstalls_removed )); }; then
  arch-mise-install antigravity-cli agy
fi

if [[ $selected_agent == "gemini" ]]; then
  mkdir -p "$(dirname "$agent_file")"
  printf '%s\n' agy >"$agent_file"
fi

# Remove Preinstalls no longer lists gemini, so Arch's own wrapper would
# linger with nothing left to clean it up. Anchored to the line the installer
# writes, so a hand-written wrapper that merely mentions it is left alone.
if [[ -f $HOME/.local/bin/gemini ]] && grep -Eq '^mise use -g .*"gemini"' "$HOME/.local/bin/gemini"; then
  rm -f "$HOME/.local/bin/gemini"
fi

if [[ -d $skills_source ]]; then
  mkdir -p "$HOME/.gemini/config/skills"
  for skill in "$skills_source"/*/; do
    [[ -d $skill ]] || continue
    name=${skill%/}
    ln -sfn "$name" "$HOME/.gemini/config/skills/${name##*/}"
  done
fi
