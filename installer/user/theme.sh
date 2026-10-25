# Setup user theme folder and seed the default only when no theme exists yet.
mkdir -p ~/.config/arch/themes

if [[ ! -s $HOME/.local/state/arch/current/theme.name ]]; then
  # iso-chroot and provision-owner both run without a live session to notify.
  if [[ ${ARCH_SETUP_CONTEXT:-runtime} != "runtime" ]]; then
    ARCH_THEME_HEADLESS=1 arch-theme-set "Cosmic"
    rm -f ~/.config/chromium/SingletonLock # otherwise archiso owns the Chromium singleton
  else
    arch-theme-set "Cosmic"
  fi
fi
arch-theme-set-pi --activate
arch-theme-set-fcitx5 --activate

# Cosmic's packaged icon theme inherits Pop, which can fall back to Adwaita.
# Keep Cosmic's own icons first and use Breeze Dark for the remaining glyphs.
icon_theme_source=/usr/share/icons/Cosmic/index.theme
icon_theme_user_dir="$HOME/.local/share/icons/Cosmic"
if [[ -r $icon_theme_source ]] && grep -q '^Inherits=' "$icon_theme_source"; then
  mkdir -p "$icon_theme_user_dir"
  sed 's/^Inherits=.*/Inherits=breeze-dark/' "$icon_theme_source" >"$icon_theme_user_dir/index.theme.tmp"
  chmod 644 "$icon_theme_user_dir/index.theme.tmp"
  mv "$icon_theme_user_dir/index.theme.tmp" "$icon_theme_user_dir/index.theme"
fi

mkdir -p ~/.config/btop/themes
ln -snf "$HOME/.local/state/arch/current/theme/btop.theme" ~/.config/btop/themes/current.theme
