#!/usr/bin/env bash

DESKTOP_WORKFLOW_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_WORKFLOW_PORTALS="${DESKTOP_WORKFLOW_PORTALS:-$DESKTOP_WORKFLOW_LIB_DIR/../../modules/conf/xdg-desktop-portal/data/portals.conf}"
DESKTOP_WORKFLOW_MPV_ENTRY="${DESKTOP_WORKFLOW_MPV_ENTRY:-$DESKTOP_WORKFLOW_LIB_DIR/../../data/component/application/desktop/mpv.desktop}"
[[ -f "$DESKTOP_WORKFLOW_MPV_ENTRY" ]] || DESKTOP_WORKFLOW_MPV_ENTRY="$DESKTOP_WORKFLOW_LIB_DIR/mpv.desktop"

desktop_workflow_defaults() {
    local user="$1" home="$2" mime config
    install -d -m 755 -o "$user" -g "$user" "$home/.local/share/applications" || return 1
    install -m 644 -o "$user" -g "$user" "$DESKTOP_WORKFLOW_MPV_ENTRY" "$home/.local/share/applications/mpv.desktop" || return 1
    for config in "$home/.config/mimeapps.list" "$home/.local/share/applications/mimeapps.list"; do
        [[ -f "$config" ]] || continue
        sed -i -e 's/geany\.desktop/dev.zed.Zed.desktop/g' -e 's/geany-project\.desktop;//g' "$config" || return 1
        chown "$user:$user" "$config" || return 1
    done
    user_as "$user" env -u BROWSER xdg-settings set default-web-browser brave-origin.desktop || return 1
    for mime in x-scheme-handler/http x-scheme-handler/https text/html; do
        user_as "$user" xdg-mime default brave-origin.desktop "$mime" || return 1
    done
    user_as "$user" xdg-mime default org.gnome.Nautilus.desktop inode/directory || return 1
    user_as "$user" gio mime inode/directory org.gnome.Nautilus.desktop || return 1
    user_as "$user" xdg-mime default dev.zed.Zed.desktop text/plain text/x-shellscript text/x-python text/markdown \
        text/x-c text/x-c++ text/x-csrc text/x-chdr text/x-c++src text/x-c++hdr text/x-java \
        text/javascript application/javascript application/json application/xml text/xml application/x-yaml text/yaml || return 1
    user_as "$user" xdg-mime default org.gnome.Papers.desktop application/pdf || return 1
    user_as "$user" xdg-mime default onlyoffice-desktopeditors.desktop \
        application/msword application/vnd.openxmlformats-officedocument.wordprocessingml.document \
        application/vnd.openxmlformats-officedocument.wordprocessingml.template \
        application/vnd.ms-word.document.macroEnabled.12 application/vnd.ms-word.template.macroEnabled.12 \
        application/vnd.oasis.opendocument.text application/vnd.oasis.opendocument.text-template application/rtf text/rtf \
        application/vnd.ms-excel application/vnd.openxmlformats-officedocument.spreadsheetml.sheet \
        application/vnd.openxmlformats-officedocument.spreadsheetml.template \
        application/vnd.ms-excel.sheet.macroEnabled.12 application/vnd.ms-excel.template.macroEnabled.12 \
        application/vnd.oasis.opendocument.spreadsheet application/vnd.oasis.opendocument.spreadsheet-template text/csv \
        application/vnd.ms-powerpoint application/vnd.openxmlformats-officedocument.presentationml.presentation \
        application/vnd.openxmlformats-officedocument.presentationml.template \
        application/vnd.openxmlformats-officedocument.presentationml.slideshow \
        application/vnd.ms-powerpoint.presentation.macroEnabled.12 application/vnd.ms-powerpoint.template.macroEnabled.12 \
        application/vnd.ms-powerpoint.slideshow.macroEnabled.12 \
        application/vnd.oasis.opendocument.presentation application/vnd.oasis.opendocument.presentation-template || return 1
    user_as "$user" xdg-mime default org.gnome.Loupe.desktop image/png image/jpeg image/gif image/webp image/avif \
        image/bmp image/tiff image/svg+xml image/heif image/heic image/jxl || return 1
    user_as "$user" xdg-mime default io.github.celluloid_player.Celluloid.desktop video/mp4 video/x-matroska video/webm \
        video/mpeg video/quicktime video/x-msvideo video/x-ms-wmv video/ogg video/mp2t \
        audio/mpeg audio/flac audio/ogg audio/mp4 audio/aac audio/x-wav audio/x-opus+ogg application/ogg || return 1
    user_as "$user" xdg-mime default org.gnome.FileRoller.desktop application/zip application/x-7z-compressed \
        application/x-tar application/gzip application/x-bzip2 application/x-xz application/zstd \
        application/vnd.rar application/x-rar application/x-rar-compressed application/x-compressed-tar || return 1
    install -d -m 700 -o "$user" -g "$user" "$home/.local/state/omarchy/defaults" || return 1
    printf 'nautilus\n' > "$home/.local/state/omarchy/defaults/file-manager" || return 1
    chown "$user:$user" "$home/.local/state/omarchy/defaults/file-manager" || return 1
    printf 'zed\n' > "$home/.local/state/omarchy/defaults/editor" || return 1
    printf 'celluloid\n' > "$home/.local/state/omarchy/defaults/media-player" || return 1
    chown "$user:$user" "$home/.local/state/omarchy/defaults/editor" "$home/.local/state/omarchy/defaults/media-player" || return 1
}

desktop_workflow_portals() {
    local user="$1" home="$2" name backend uid
    local config="$home/.config/xdg-desktop-portal"
    install -d -m 700 -o "$user" -g "$user" "$config" || return 1
    for name in portals.conf hyprland-portals.conf; do
        install -m 644 -o "$user" -g "$user" "$DESKTOP_WORKFLOW_PORTALS" "$config/$name" || return 1
    done
    uid=$(id -u "$user") || return 1
    [[ -S "/run/user/$uid/bus" ]] || return 0
    user_as "$user" systemctl --user unmask xdg-desktop-portal-gtk.service || return 1
    for backend in termfilechooser gnome; do
        if user_as "$user" systemctl --user cat "xdg-desktop-portal-$backend.service" >/dev/null 2>&1; then
            user_as "$user" systemctl --user stop "xdg-desktop-portal-$backend.service" || return 1
            user_as "$user" systemctl --user mask "xdg-desktop-portal-$backend.service" || return 1
        fi
    done
    user_as "$user" systemctl --user restart xdg-desktop-portal-gtk.service xdg-desktop-portal.service || return 1
}
