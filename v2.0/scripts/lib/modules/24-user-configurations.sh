#!/usr/bin/env bash
set -euo pipefail

_application_rows=$(jq -er 'keys | if length > 0 then .[] else empty end' "$PROJECT_DIR/data/component/application/policy.json") || err "defaults.app_failed" "application policy"
mapfile -t _applications <<< "$_application_rows"
for user_home in /home/*; do
    [[ -d "$user_home" ]] || continue
    _user=$(basename "$user_home")
    for _application in "${_applications[@]}"; do
        user_as "$_user" lua -E "$PROJECT_DIR/src/main.lua" "$PROJECT_DIR" apply-settings "$_application" || err "defaults.app_failed" "$_application"
    done
    user_as "$_user" lua -E "$PROJECT_DIR/src/main.lua" "$PROJECT_DIR" install-wallpapers || err "defaults.app_failed" "wallpapers"
    for _installer in "$PROJECT_DIR"/modules/conf/*/install.sh; do
        [[ -f "$_installer" ]] || continue
        user_as "$_user" bash "$_installer" || err "defaults.app_failed" "$(basename "$(dirname "$_installer")")"
    done
    if [[ -f "$user_home/.config/hypr/hyprland.lua" ]]; then
        user_as "$_user" "$PROJECT_DIR/script/os-lua" install-settings || err "defaults.app_failed" "Settings"
    fi
done
