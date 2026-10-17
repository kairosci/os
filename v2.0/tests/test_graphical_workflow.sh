#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/test_lib.sh"

WORKFLOW_SANDBOX=$(mktemp -d)
WORKFLOW_USER=$(id -un)
trap 'rm -rf "$WORKFLOW_SANDBOX"' EXIT
mkdir -p "$WORKFLOW_SANDBOX/home/.config/gtk-3.0" "$WORKFLOW_SANDBOX/home/.config/gtk-4.0"
printf '%s\n' 'label { font-weight: bold; }' > "$WORKFLOW_SANDBOX/home/.config/gtk-3.0/gtk.css"
cat > "$WORKFLOW_SANDBOX/colors.toml" <<'COLORS'
mode = "dark"
background = "#112233"
foreground = "#eeeeee"
accent = "#88aaff"
selection = "#334455"
COLORS

run_gtk_hook() {
    HOME="$WORKFLOW_SANDBOX/home" XDG_CONFIG_HOME="$WORKFLOW_SANDBOX/home/.config" XDG_DATA_HOME="$WORKFLOW_SANDBOX/home/.local/share" \
        OS_THEME_COLORS="$WORKFLOW_SANDBOX/colors.toml" bash "$PROJECT_DIR/hooks/theme-set.d/gtk-theme"
}

component_transition_policy() {
    awk '
        /transition:[[:space:]]/ {
            value=$0
            sub(/^.*transition:[[:space:]]*/, "", value)
            sub(/;.*/, "", value)
            if (value == "none") next
            count++
            size=split(value, transitions, ",")
            for (i=1; i<=size; i++) {
                sub(/^[[:space:]]*/, "", transitions[i])
                split(transitions[i], parts, /[[:space:]]+/)
                if (parts[1] !~ /^(background-color|color|border-color|outline-color)$/) exit 1
                if (parts[2] !~ /^[0-9]+ms$/) exit 1
                duration=parts[2]+0
                if (duration < 60 || duration > 160) exit 1
            }
        }
        END { if (count < 2) exit 1 }
    ' "$1"
}

test_section "Graphical Desktop Workflow"
assert_true "GTK palette hook succeeds with valid colors" "run_gtk_hook"
assert_file_contains_literal "GTK hook preserves existing user CSS" "$WORKFLOW_SANDBOX/home/.config/gtk-3.0/gtk.css" 'label { font-weight: bold; }'
assert_file_contains_literal "GTK 3 uses the supplied palette" "$WORKFLOW_SANDBOX/home/.config/gtk-3.0/os.css" '@define-color theme_bg_color #112233;'
assert_file_contains_literal "GTK 4 uses the supplied accent" "$WORKFLOW_SANDBOX/home/.config/gtk-4.0/os.css" '@define-color accent_bg_color #88aaff;'
assert_file_contains_literal "libadwaita receives the exact background" "$WORKFLOW_SANDBOX/home/.config/gtk-4.0/os.css" '--window-bg-color: #112233;'
assert_file_contains "GTK selects a generated palette theme" "$WORKFLOW_SANDBOX/home/.config/gtk-3.0/settings.ini" '^gtk-theme-name=OS-[0-9a-f]+$'
assert_true "generated GTK theme uses Materia dark as its base" \
    "grep -q 'Materia-dark/gtk-3.0/gtk.css' '$WORKFLOW_SANDBOX/home/.local/share/themes/'*/gtk-3.0/gtk.css"
assert_true "GTK hook is idempotent" "before=\$(sha256sum '$WORKFLOW_SANDBOX/home/.config/gtk-3.0/'*.css); run_gtk_hook; after=\$(sha256sum '$WORKFLOW_SANDBOX/home/.config/gtk-3.0/'*.css); [[ \"\$before\" == \"\$after\" ]]"
for version in 3 4; do
    generated="$WORKFLOW_SANDBOX/home/.config/gtk-$version.0/os.css"
    assert_file_contains_literal "GTK $version preserves selected rows while hovered" "$generated" 'row:selected, row:selected:hover, .sidebar row:selected, .navigation-sidebar row:selected { background-color: #334455; color: #eeeeee; }'
    assert_file_contains_literal "GTK $version uses the exact accent for suggested actions" "$generated" 'button.suggested-action { background-color: #88aaff; color: #112233; border-color: #88aaff; }'
    assert_file_contains_literal "GTK $version clears inherited negative scrollbar margins" "$generated" 'min-width: 8px; min-height: 8px; margin: 0; padding: 0;'
done
for version in 3 4; do
    assert_true "GTK $version component transitions preserve geometry and avoid double fades" "component_transition_policy '$WORKFLOW_SANDBOX/home/.config/gtk-$version.0/os.css'"
done
printf '%s\n' 'button { transition: color 120ms ease-out; }' 'entry { transition: border-color 120ms ease-out; }' 'row { transition: transform 120ms ease-out; }' > "$WORKFLOW_SANDBOX/unsafe-motion.css"
assert_false "animation policy rejects geometry transitions" "component_transition_policy '$WORKFLOW_SANDBOX/unsafe-motion.css'"
mkdir -p "$WORKFLOW_SANDBOX/icons/Qogir-Dark/scalable/places"
printf '[Icon Theme]\nName=Qogir Dark\n' > "$WORKFLOW_SANDBOX/icons/Qogir-Dark/index.theme"
printf '<svg xmlns="http://www.w3.org/2000/svg"><path fill="#6ba4e7" stroke="#003579"/></svg>\n' > "$WORKFLOW_SANDBOX/icons/Qogir-Dark/scalable/places/folder.svg"
ln -s folder.svg "$WORKFLOW_SANDBOX/icons/Qogir-Dark/scalable/places/folder-documents.svg"
ln -s folder.svg "$WORKFLOW_SANDBOX/icons/Qogir-Dark/scalable/places/fileopen.svg"
mkdir -p "$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/places"
cp "$WORKFLOW_SANDBOX/icons/Qogir-Dark/scalable/places/fileopen.svg" "$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/places/fileopen.svg"
run_folder_hook() {
    HOME="$WORKFLOW_SANDBOX/home" XDG_DATA_HOME="$WORKFLOW_SANDBOX/home/.local/share" \
        OS_ICON_ROOT="$WORKFLOW_SANDBOX/icons" OS_THEME_COLORS="$WORKFLOW_SANDBOX/colors.toml" \
        bash "$PROJECT_DIR/hooks/theme-set.d/folder-color"
}
assert_true "folder icon hook accepts the supplied palette" "run_folder_hook"
assert_file_contains_literal "folder icons use the exact accent" "$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/places/folder.svg" '#88aaff'
assert_file_contains_literal "folder overlay inherits the complete dark Qogir set" "$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/index.theme" 'Inherits=Qogir-Dark,hicolor'
assert_file_contains_literal "folder variants resolve upstream symlinks" "$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/places/folder-documents.svg" '#88aaff'
assert_false "folder overlay leaves toolbar actions at their native size" "[[ -e '$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/places/fileopen.svg' ]]"
for size in 16 22 24 32 48 96 128 scalable; do
    assert_true "terminal folder outlines match across $size pixel aliases" "cmp '$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/$size/places/folder.svg' '$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/$size/places/inode-directory.svg' && cmp '$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/$size/places/folder.svg' '$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/places/folder.svg'"
done
assert_file_contains_literal "terminal MIME icons use the palette foreground" "$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/mimetypes/application-pdf.svg" 'fill="#eeeeee"'
assert_true "terminal MIME aliases share the same outline" "cmp '$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/mimetypes/image-png.svg' '$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/mimetypes/image-jpeg.svg'"
sed -i 's/#eeeeee/invalid/' "$WORKFLOW_SANDBOX/colors.toml"
assert_false "invalid foreground stops icon generation" "run_folder_hook"
assert_file_contains_literal "invalid foreground preserves existing MIME icons" "$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/mimetypes/application-pdf.svg" 'fill="#eeeeee"'
sed -i 's/invalid/#eeeeee/' "$WORKFLOW_SANDBOX/colors.toml"
assert_true "folder overlay is idempotent" "before=\$(sha256sum '$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/places/folder.svg'); run_folder_hook; after=\$(sha256sum '$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/places/folder.svg'); [[ \"\$before\" == \"\$after\" ]]"
cp -r "$WORKFLOW_SANDBOX/icons/Qogir-Dark" "$WORKFLOW_SANDBOX/icons/Qogir"
sed -i 's/mode = "dark"/mode = "light"/' "$WORKFLOW_SANDBOX/colors.toml"
assert_true "folder overlay accepts light palettes" "run_folder_hook"
assert_file_contains_literal "folder overlay inherits Qogir for light palettes" "$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/index.theme" 'Inherits=Qogir,hicolor'
sed -i 's/#88aaff/invalid/' "$WORKFLOW_SANDBOX/colors.toml"
assert_false "folder overlay rejects invalid accents" "run_folder_hook"
assert_file_contains_literal "invalid accent preserves the existing folder icon" "$WORKFLOW_SANDBOX/home/.local/share/icons/OS-Qogir/scalable/places/folder.svg" '#88aaff'
assert_false "GTK hook rejects invalid colors" "run_gtk_hook"
assert_file_contains_literal "invalid GTK palette leaves the previous style intact" "$WORKFLOW_SANDBOX/home/.config/gtk-3.0/os.css" '@define-color accent_bg_color #88aaff;'

source "$PROJECT_DIR/scripts/lib/desktop-workflow.sh"
# shellcheck disable=SC2329
user_as() {
    shift
    printf '%s\n' "$*" >> "$WORKFLOW_SANDBOX/commands"
}
printf '[Default Applications]\ntext/x-c=geany.desktop;\n[Added Associations]\ninode/directory=geany-project.desktop;org.gnome.Nautilus.desktop;\n' > "$WORKFLOW_SANDBOX/home/.config/mimeapps.list"
assert_true "desktop defaults apply with an isolated home" "desktop_workflow_defaults '$WORKFLOW_USER' '$WORKFLOW_SANDBOX/home'"
assert_file_contains_literal "browser defaults bypass the inherited BROWSER override" "$WORKFLOW_SANDBOX/commands" 'env -u BROWSER xdg-settings set default-web-browser brave-origin.desktop'
assert_file_contains_literal "existing source associations migrate to Zed" "$WORKFLOW_SANDBOX/home/.config/mimeapps.list" 'text/x-c=dev.zed.Zed.desktop;'
assert_file_contains_literal "retired project launcher leaves Nautilus associations intact" "$WORKFLOW_SANDBOX/home/.config/mimeapps.list" 'inode/directory=org.gnome.Nautilus.desktop;'
assert_file_contains_literal "desktop defaults use the graphical directory handler" "$WORKFLOW_SANDBOX/commands" 'xdg-mime default org.gnome.Nautilus.desktop inode/directory'
assert_file_contains_literal "desktop defaults keep Brave for HTTPS" "$WORKFLOW_SANDBOX/commands" 'xdg-mime default brave-origin.desktop x-scheme-handler/https'
assert_file_contains_literal "text defaults use Zed" "$WORKFLOW_SANDBOX/commands" 'xdg-mime default dev.zed.Zed.desktop text/plain'
assert_file_contains_literal "OS editor state records Zed" "$WORKFLOW_SANDBOX/home/.local/state/omarchy/defaults/editor" 'zed'
assert_file_contains_literal "PDF defaults use Papers" "$WORKFLOW_SANDBOX/commands" 'xdg-mime default org.gnome.Papers.desktop application/pdf'
assert_file_contains_literal "office documents use OnlyOffice" "$WORKFLOW_SANDBOX/commands" 'xdg-mime default onlyoffice-desktopeditors.desktop application/msword'
assert_file_contains_literal "backend launcher is hidden" "$WORKFLOW_SANDBOX/home/.local/share/applications/mpv.desktop" 'Hidden=true'
assert_file_contains_literal "image defaults use Loupe" "$WORKFLOW_SANDBOX/commands" 'xdg-mime default org.gnome.Loupe.desktop image/png'
assert_file_contains_literal "media defaults use Celluloid" "$WORKFLOW_SANDBOX/commands" 'xdg-mime default io.github.celluloid_player.Celluloid.desktop video/mp4'
assert_file_contains "OS file manager state records Nautilus" "$WORKFLOW_SANDBOX/home/.local/state/omarchy/defaults/file-manager" '^nautilus$'

user_as() { return 1; }
assert_false "desktop default failures propagate to callers" "desktop_workflow_defaults '$WORKFLOW_USER' '$WORKFLOW_SANDBOX/home'"
assert_false "preview capture refuses direct session changes" "bash '$PROJECT_DIR/modules/theme-previews/rebuild-previews.sh' fake-theme"

binding_home="$WORKFLOW_SANDBOX/$WORKFLOW_USER"
mkdir -p "$binding_home/.config/hypr"
printf '%s\n' '-- os-thunar-fm' '-- os-graphical-apps' \
    'o.bind("SUPER + SHIFT + F", "File manager", "thunar")' \
    'o.bind("SUPER + SHIFT + N", "Editor", "geany")' \
    'o.window("^(geany|Geany|org.gnome.Nautilus)$", { opacity = "1 1" })' \
    'o.bind("SUPER + SHIFT + ALT + B", "Private browser", { launch = "brave-origin --incognito" })' \
    > "$binding_home/.config/hypr/bindings.lua"
awk -v home="$binding_home" '
    /^log "defaults.rebind"/ { inside=1; next }
    /^log "defaults.podman"/ { exit }
    inside { gsub("/home/\\*", home); print }
' "$PROJECT_DIR/scripts/lib/modules/20-defaults.sh" > "$WORKFLOW_SANDBOX/rebind.sh"
assert_true "editor bindings migrate through the defaults stage" "bash '$WORKFLOW_SANDBOX/rebind.sh'"
assert_file_contains_literal "file manager shortcut migrates to Nautilus" "$binding_home/.config/hypr/bindings.lua" '"File manager", "nautilus"'
assert_file_contains_literal "editor shortcut opens Zed" "$binding_home/.config/hypr/bindings.lua" '"Editor", "zed"'
assert_file_not_contains "Geany window rules are retired" "$binding_home/.config/hypr/bindings.lua" 'geany|Geany'
assert_true "editor binding migration is idempotent" "before=\$(sha256sum '$binding_home/.config/hypr/bindings.lua'); bash '$WORKFLOW_SANDBOX/rebind.sh'; [[ \"\$before\" == \"\$(sha256sum '$binding_home/.config/hypr/bindings.lua')\" ]]"

CONFIG_STAGE="$PROJECT_DIR/scripts/lib/modules/24-user-configurations.sh"
mkdir -p "$WORKFLOW_SANDBOX/project/modules/conf/brave" "$WORKFLOW_SANDBOX/project/modules/conf/new-app"
mkdir -p "$WORKFLOW_SANDBOX/project/data/component/application"
printf '{"fixture":{},"another":{}}\n' > "$WORKFLOW_SANDBOX/project/data/component/application/policy.json"
printf '#!/bin/bash\nprintf "brave loaded\\n"\n' > "$WORKFLOW_SANDBOX/project/modules/conf/brave/install.sh"
printf '#!/bin/bash\nprintf "new app loaded\\n"\n' > "$WORKFLOW_SANDBOX/project/modules/conf/new-app/install.sh"
run_config_stage() (
    PROJECT_DIR="$WORKFLOW_SANDBOX/project"
    # shellcheck disable=SC2329
    user_as() {
        shift
        if [[ "$1" == lua ]]; then
            if read -r -t 0.01 _discarded; then :; fi
            [[ "${CONFIG_LUA_FAIL:-0}" == 0 ]] || return 7
            if [[ "${5:-}" == apply-settings ]]; then printf 'lua settings loaded\n'; else printf 'lua wallpaper stage loaded\n'; fi
        else
            "$@"
        fi
    }
    # shellcheck disable=SC2329
    err() { exit 1; }
    # shellcheck source=../scripts/lib/modules/24-user-configurations.sh
    source "$CONFIG_STAGE"
)
assert_true "config discovery installs Brave and a newly added app automatically" \
    "run_config_stage > '$WORKFLOW_SANDBOX/config-log'; grep -q 'brave loaded' '$WORKFLOW_SANDBOX/config-log' && grep -q 'new app loaded' '$WORKFLOW_SANDBOX/config-log'"
assert_true "every Lua application runs even when a child reads standard input" '[[ $(grep -c "lua settings loaded" "$WORKFLOW_SANDBOX/config-log") == 2 ]]'
assert_true "the wallpaper stage runs once for the user" '[[ $(grep -c "lua wallpaper stage loaded" "$WORKFLOW_SANDBOX/config-log") == 1 ]]'
printf '#!/bin/bash\nexit 7\n' > "$WORKFLOW_SANDBOX/project/modules/conf/new-app/install.sh"
assert_false "failed app configuration stops provisioning" "run_config_stage"
assert_false "failed Lua settings stop provisioning" "CONFIG_LUA_FAIL=1 run_config_stage"
assert_false "Yazi is absent from the live package database" "command -v pacman >/dev/null && pacman -Q yazi >/dev/null 2>&1"

mkdir -p "$WORKFLOW_SANDBOX/resources-bin"
cat > "$WORKFLOW_SANDBOX/resources-bin/gsettings" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
case "$1" in
    list-schemas) printf '%s\n' "$RESOURCES_SCHEMA" ;;
    set)
        [[ "$2" == "$RESOURCES_SCHEMA" ]] || exit 1
        [[ "$3" != sidebar-details || "$2" == net.nokyan.Resources ]] || exit 1
        printf '%s\n' "$*" >> "$RESOURCES_SETTINGS_LOG"
        ;;
    *) exit 1 ;;
esac
MOCK
chmod 755 "$WORKFLOW_SANDBOX/resources-bin/gsettings"
assert_true "Resources GNOME schema applies supported preferences without retired keys" 'PATH="$WORKFLOW_SANDBOX/resources-bin:$PATH" RESOURCES_SCHEMA=org.gnome.Resources RESOURCES_SETTINGS_LOG="$WORKFLOW_SANDBOX/resources-modern" lua "$PROJECT_DIR/tests/lua/apply_settings.lua" "$PROJECT_DIR" resources && [[ $(wc -l < "$WORKFLOW_SANDBOX/resources-modern") == 2 ]]'
assert_true "legacy Resources retains its detailed sidebar preference" 'PATH="$WORKFLOW_SANDBOX/resources-bin:$PATH" RESOURCES_SCHEMA=net.nokyan.Resources RESOURCES_SETTINGS_LOG="$WORKFLOW_SANDBOX/resources-legacy" lua "$PROJECT_DIR/tests/lua/apply_settings.lua" "$PROJECT_DIR" resources && grep -qx "set net.nokyan.Resources sidebar-details true" "$WORKFLOW_SANDBOX/resources-legacy" && [[ $(wc -l < "$WORKFLOW_SANDBOX/resources-legacy") == 3 ]]'
assert_false "missing Resources schema stops configuration visibly" 'PATH="$WORKFLOW_SANDBOX/resources-bin:$PATH" RESOURCES_SCHEMA=missing RESOURCES_SETTINGS_LOG="$WORKFLOW_SANDBOX/resources-missing" lua "$PROJECT_DIR/tests/lua/apply_settings.lua" "$PROJECT_DIR" resources'

test_summary
