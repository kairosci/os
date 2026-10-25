echo "Remove titlebars used by floating workspaces"

# No shipped window mode can float anymore, so the titlebar plugin has no
# remaining purpose. arch-pkg-drop safely skips it when it is not installed.
arch-pkg-drop arch-hyprland-titlebars
