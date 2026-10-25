echo "Remove the retired external wallpaper renderer"

# Stop and unlink the old per-user renderer before removing its packages.
systemctl --user stop owed.service >/dev/null 2>&1 || true
systemctl --user disable owed.service >/dev/null 2>&1 || true
systemctl --user daemon-reload >/dev/null 2>&1 || true

wants_dir="$HOME/.config/systemd/user/graphical-session.target.wants"
if [[ -L $wants_dir/owed.service && $(readlink "$wants_dir/owed.service") == /usr/lib/systemd/user/owed.service ]]; then
  rm -f "$wants_dir/owed.service"
fi
rmdir "$wants_dir" 2>/dev/null || true

hook="$HOME/.config/arch/hooks/theme-set.d/10-owe-sync"
if [[ -f $hook && $(<"$hook") == *'owe theme-set hook'* && $(<"$hook") == *'/owe/owed.sock'* ]]; then
  rm -f "$hook"
fi
rmdir "$HOME/.config/arch/hooks/theme-set.d" 2>/dev/null || true

arch-pkg-drop owe owe-lockfeed
