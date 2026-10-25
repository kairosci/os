---
name: arch
description: >
  REQUIRED for end-user customization of Linux desktop, window manager, or system config.
  Use when editing ANY file in ~/.config/, ~/.config/hypr/, ~/.config/arch/,
  ~/.config/alacritty/, ~/.config/foot/, ~/.config/kitty/, or ~/.config/ghostty/.
  Triggers: Hyprland, window rules, window behavior, animations, keybindings, monitors, gaps, borders,
  blur, opacity, arch-shell, bar, widgets, terminal config, themes, fonts, background,
  night light, idle, lock screen, screenshots, screen recording, reminders, layer rules, workspace
  settings, display config, appearance changes, and user-facing archctl commands. Excludes os
  source development through `arch dev link` workflows.
---

# os Skill

Manage [os](https://github.com/kairosci/arch/) Linux systems - a beautiful, fun, agentic Arch Linux distribution with Hyprland.

This skill is for end-user customization on installed systems.
It is not for contributing to os source code.

## Topic Guides

Deeper instructions for common areas live next to this file. Read the
matching guide before starting:

- [`hyprland.md`](hyprland.md) - keybindings, monitors, window rules, and other Hyprland config
- [`plugins.md`](plugins.md) - the os shell: bar layout, widgets, plugins, idle behavior
- [`theming.md`](theming.md) - themes, backgrounds, and fonts
- [`hooks.md`](hooks.md) - automation hooks that run on system events
- [`capture.md`](capture.md) - screenshots, screen recordings, OCR text capture, and file sharing
- [`contributing.md`](contributing.md) - reporting os bugs and submitting fixes upstream

## Critical Safety Rules

For privileged commands, follow the Privilege Escalation rules below: `sudo` when a terminal is available for the password prompt, `pkexec` when it is not. Do not wrap commands that already manage privilege elevation themselves.

**For end-user customization tasks, NEVER modify anything in `/usr/share/arch/`** - but READING is safe and encouraged.

This directory is owned by the archctl package. Any local changes will be
overwritten on the next `archctl update`.

```
/usr/share/arch/     # READ-ONLY - NEVER EDIT (reading is OK)
├── bin/                    # Command source (packaged binaries are on PATH)
├── config/                 # Default config templates
├── themes/                 # Stock themes
├── default/                # System defaults
├── shell/                  # os shell source and defaults
├── migrations/             # Update migrations
└── install/                # Installation scripts
```

**Reading `/usr/share/arch/` is SAFE and useful** - do it freely to:
- Understand how archctl commands work: `archctl theme set --help` or `cat $(which arch-theme-set)`
- See default configs before customizing: `cat "$ARCH_PATH/config/arch/shell.json"`
- Check stock theme files to copy for customization
- Reference default hyprland settings: `cat /usr/share/arch/default/hypr/*`

**Always use these safe locations instead:**
- `~/.config/` - User configuration (safe to edit)
- `~/.config/arch/themes/<custom-name>/` - Custom themes
- `~/.config/arch/hooks/` - Custom automation hooks

If the request is to develop os itself, this skill is out of scope. Follow repository development instructions instead of this skill.

## Privilege Escalation

For an interactive script or command run in a visible terminal, use `sudo` for
privileged work. os may grant passwordless `sudo` access to particular
commands, and the terminal is the appropriate place to request a password
when one is needed.

Use `pkexec` only when the caller cannot interact with a terminal or cannot
enter a password there, such as a command launched by an agent or a graphical
background process. Do not replace `sudo` with `pkexec` merely because a
command changes system state.

## System Architecture

os is built on:

| Component | Purpose | Config Location |
|-----------|---------|-----------------|
| **Arch Linux** | Base OS | `/etc/`, `~/.config/` |
| **Hyprland** | Wayland compositor/WM | `~/.config/hypr/` |
| **os shell** | Status bar + notifications (Quickshell) | `~/.config/arch/shell.json` |
| **Launcher/menus** | Quickshell menu | `~/.config/arch/extensions/arch-menu.jsonc` |
| **Alacritty/Foot/Kitty/Ghostty** | Terminals | `~/.config/<terminal>/` |
| **os OSD** | On-screen display | Quickshell plugin |

## Command Discovery

os ships a single `arch` CLI that dispatches to all `arch-*` binaries via `arch <group> <action>`. Always prefer this form — it is self-documenting and stable. The underlying `arch-*` binaries still exist on `PATH` and remain safe to read for source.

```bash
# List every documented command and its summary (--all includes hidden commands)
archctl commands

# Show the commands inside a group
archctl theme --help
archctl refresh --help
archctl restart --help

# Show help for a specific command (does not execute it)
archctl theme set --help

# Machine-readable listing (binary, route, summary, args, aliases)
archctl commands --json

# Read a command's source to understand it
cat $(which arch-theme-set)
```

### Command Groups

Run `arch --help` for the full list. The most common groups:

| Group | Purpose | Example |
|-------|---------|---------|
| `archctl refresh` | Reset config to defaults (backs up first) | `archctl refresh shell` |
| `archctl restart` | Restart a service/app | `archctl restart shell` |
| `archctl toggle` | Toggle feature on/off | `archctl toggle nightlight` |
| `archctl theme` | Theme management | `archctl theme set <name>` |
| `archctl bar` | Bar layout and widgets | `archctl bar move arch.clock --section right` |
| `arch plugin` | Manage/clone shell plugins | `arch plugin clone arch.clock` |
| `archctl hook` | Install automation hooks | `archctl hook install theme-set <script>` |
| `archctl install` | Install optional software / packages | `archctl install docker dbs` |
| `archctl launch` | Launch apps | `archctl launch browser` |
| `archctl capture` | Screenshots and recordings | `archctl capture screenshot` |
| `arch reminder` | Desktop notification reminders | `arch reminder 15 "Pickup Jack"` |
| `archctl pkg` | Package management | `archctl pkg add <pkg>` |
| `archctl setup` | Interactive setup wizards | `archctl setup security fingerprint` |
| `archctl update` | System updates | `archctl update` |

## Configuration Locations

Hyprland config lives in `~/.config/hypr/` — see [`hyprland.md`](hyprland.md).
The os shell (bar, notifications, plugins, idle) is configured in
`~/.config/arch/shell.json` — see [`plugins.md`](plugins.md).

### Terminals

```
~/.config/alacritty/alacritty.toml
~/.config/foot/foot.ini
~/.config/kitty/kitty.conf
~/.config/ghostty/config
```

**Command:** `archctl restart terminal`

### Other Configs

| App | Location |
|-----|----------|
| btop | `~/.config/btop/btop.conf` |
| fastfetch | `/etc/fastfetch/config.jsonc` default; `~/.config/fastfetch/config.jsonc` user override |
| lazygit | `~/.config/lazygit/config.yml` |
| starship | `~/.config/starship.toml` |
| git | `~/.config/git/config` |

## Safe Customization Patterns

### Edit User Config Directly

For simple changes, edit files in `~/.config/`:

```bash
# 1. Read current config
cat ~/.config/hypr/bindings.lua

# 2. Backup before changes
cp ~/.config/hypr/bindings.lua ~/.config/hypr/bindings.lua.bak.$(date +%s)

# 3. Make changes with Edit tool

# 4. Apply changes
# - Hyprland: auto-reloads on save, but MUST validate with `hyprctl reload` and `hyprctl configerrors`
# - os shell: shell.json and user plugin code under ~/.config/arch/plugins/ hot-reload on save
# - Menus/launcher: ~/.config/arch/extensions/arch-menu.jsonc hot-reloads on save
# - Terminals: apply with `archctl restart terminal` (reloads running terminals; foot picks changes up in new windows)
```

### Reset to Defaults -- ALWAYS SEEK USER CONFIRMATION BEFORE RUNNING

When customizations go wrong:

```bash
# Reset specific config (creates backup automatically)
archctl refresh shell
archctl refresh hyprland

# The refresh command:
# 1. Backs up current config with timestamp
# 2. Copies default from $ARCH_PATH/config/
# 3. Restarts the component where the refresh needs it (e.g. `refresh shell`)
```

## System Commands

```bash
archctl update                  # Full system update
archctl version                 # Show os version
archctl debug --no-sudo --print # Debug info (ALWAYS use these flags)
archctl system lock             # Lock screen
archctl system shutdown         # Shutdown
archctl system reboot           # Reboot
```

**IMPORTANT:** Always run `archctl debug` with `--no-sudo --print` flags to avoid interactive sudo prompts that will hang the terminal.

## Troubleshooting

```bash
# Get debug information (ALWAYS use these flags to avoid interactive prompts)
archctl debug --no-sudo --print

# Reset specific config to defaults
archctl refresh <app>

# Refresh specific config file
# config-file path is relative to ~/.config/
# eg. `archctl refresh config hypr/hyprland.lua` will refresh ~/.config/hypr/hyprland.lua
archctl refresh config <config-file>

# Full reinstall of configs (nuclear option)
arch reinstall
```

## Decision Framework

When user requests system changes:

1. **Is it a stock archctl command?** Use it directly
2. **Is it a config edit?** Edit in `~/.config/`, never `/usr/share/arch/`
3. **Is it a theme customization?** Follow [`theming.md`](theming.md); create a NEW custom theme directory
4. **Is it automation?** Follow [`hooks.md`](hooks.md); use `archctl hook install` and the hook `.d` directories
5. **Is it a package install?** Use `archctl pkg add <pkgs...>` (or `archctl pkg aur add <pkgs...>` for AUR-only packages)
6. **Is it built-in shell/plugin code?** Follow [`plugins.md`](plugins.md); clone it with `arch plugin clone`, never edit the packaged copy
7. **Unsure if command exists?** Run `archctl commands` (or `arch <group> --help` for one group)

### Reminder Requests

When the user asks to set a reminder, use `arch reminder <minutes> [message]` directly. Convert natural language durations to minutes and title-case short reminder labels when appropriate.

```bash
arch reminder 15 "Pickup Jack"
arch reminder 60 "Check laundry"
arch reminder show
arch reminder clear
```

## Out of Scope

This skill intentionally does not cover os source development. Do not use this skill for:
- Editing files in `/usr/share/arch/` (`bin/`, `config/`, `default/`, `shell/`, `themes/`, `migrations/`, etc.)
- Creating or editing migrations
- Running `arch dev ...` commands

## Example Requests

- "Change my theme to catppuccin" -> `archctl theme set catppuccin`
- "Add a keybinding for Super+E to open file manager" -> Check existing bindings first, then use `o.rebind` to replace one or `o.bind` to add one in `~/.config/hypr/bindings.lua`
- "Configure my external monitor" -> Edit `~/.config/hypr/monitors.lua`
- "Make the window gaps smaller" -> Edit `~/.config/hypr/looknfeel.lua`
- "Turn on night light" -> `archctl toggle nightlight` (for time-based schedules, edit `~/.config/hypr/hyprsunset.conf` profiles, then `archctl restart hyprsunset`)
- "Set a reminder to pickup jack in 15 minutes" -> `arch reminder 15 "Pickup Jack"`
- "Show my reminders" -> `arch reminder show`
- "Clear all reminders" -> `arch reminder clear`
- "Customize the catppuccin theme colors" -> Overlay: put an edited `colors.toml` in `~/.config/arch/themes/catppuccin/`, then re-apply the theme (see `theming.md`)
- "Run a script every time I change themes" -> Install it with `archctl hook install theme-set <script>`
- "Change how workspace labels are rendered" -> Clone `arch.workspaces`, which switches the bar to `<username>.workspaces`, then edit the clone
- "Lock after ten minutes" -> Set `idle.lock` to `600` in `~/.config/arch/shell.json`
- "Reset shell/bar to defaults" -> `archctl refresh shell`
- "Record my screen" -> `arch screenrecord --fullscreen`, then `arch screenrecord --stop-recording` (see `capture.md`)
- "Report this bug to os" -> Gather diagnostics and a capture of the problem, then file it (see `contributing.md`)
