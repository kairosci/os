echo "Relink agent skill symlinks to default/agents/skills/arch"

mkdir -p ~/.agents/skills ~/.claude/skills ~/.codex/skills ~/.pi/agent/skills
ln -sfn "$ARCH_PATH/default/agents/skills/arch" ~/.agents/skills/arch
ln -sfn "$ARCH_PATH/default/agents/skills/arch" ~/.claude/skills/arch
ln -sfn "$ARCH_PATH/default/agents/skills/arch" ~/.codex/skills/arch
ln -sfn "$ARCH_PATH/default/agents/skills/arch" ~/.pi/agent/skills/arch
