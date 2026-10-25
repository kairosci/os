echo "Theme the Fcitx candidate window with the current Arch theme"

# Activation selects the theme; the refresh then renders it, since the current
# theme was staged before its template existed.
arch-theme-set-fcitx5 --activate
arch-theme-refresh
