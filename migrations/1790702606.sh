echo "Link the arch-app agent skill for building apps"

# arch-provision-user links every skill, but only once per user, so
# existing installs get the new one here, in the same places. A skill of the
# user's own by that name is left where it is.
skill="$ARCH_PATH/default/agents/skills/arch-app"

link_skill() {
  mkdir -p "$1"
  if [[ -e $1/arch-app && ! -L $1/arch-app ]]; then
    echo "Leaving your own $1/arch-app in place"
  else
    ln -sfn "$skill" "$1/arch-app"
  fi
}

if [[ -d $skill ]]; then
  for skills_dir in ~/.agents/skills ~/.claude/skills ~/.codex/skills ~/.pi/agent/skills ~/.gemini/config/skills ~/.hermes/skills; do
    link_skill "$skills_dir"
  done

  if [[ -d ~/.hermes/profiles ]]; then
    for profile in ~/.hermes/profiles/*/; do
      [[ -d $profile ]] || continue
      link_skill "$profile/skills"
    done
  fi
fi
