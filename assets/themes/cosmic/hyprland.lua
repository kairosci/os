-- ────────────────────────────────────────────────────────────
-- Rainy Theme — os 4 / Hyprland 0.55+
-- ────────────────────────────────────────────────────────────

-- Keep the Rainy window geometry, opacity and border styling.
hl.config({
  general = {
    border_size = 2,
    gaps_in = 2,
    gaps_out = 4,

    ["col.active_border"] = "#ffffff",
    ["col.inactive_border"] = "#1a1b26",
  },

  animations = {
    enabled = true,
  },

  decoration = {
    rounding = 0,

    shadow = {
      enabled = false,
      range = 15,
      render_power = 4,
      offset = { 0, 0 },
    },

    -- This is the original Rainy blur, preserved intentionally.
    --
    -- Old config:
    --   size = 1
    --   passes = 4
    --   contrast = 1.1
    --   brightness = 1.1
    --   vibrancy = 0.2
    --   vibrancy_darkness = 0.2
    --   noise = 0.03
    --   ignore_opacity = true
    --   new_optimizations = on
    blur = {
      enabled = true,
      size = 1,
      passes = 4,
      contrast = 1.1,
      brightness = 1.1,
      vibrancy = 0.2,
      vibrancy_darkness = 0.2,
      noise = 0.03,
      ignore_opacity = true,
      new_optimizations = true,
    },

    active_opacity = 0.95,
    inactive_opacity = 0.94,
    fullscreen_opacity = 1.0,
  },

  -- Num Lock must start OFF.
  --input = {
  --  numlock_by_default = false,
  --},
})

-- Original Rainy animation curve:
-- bezier = calm, 0.25, 0.9, 0.35, 1
hl.curve("calm", {
  type = "bezier",
  points = {
    { 0.25, 0.9 },
    { 0.35, 1.0 },
  },
})

hl.animation({ leaf = "windows", enabled = true, speed = 4, bezier = "calm" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 4, bezier = "calm" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 3, bezier = "calm" })
hl.animation({ leaf = "windowsMove", enabled = true, speed = 4, bezier = "calm" })

hl.animation({ leaf = "fade", enabled = true, speed = 3, bezier = "calm" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 3, bezier = "calm" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 2, bezier = "calm" })

hl.animation({ leaf = "layers", enabled = true, speed = 3, bezier = "calm" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 3, bezier = "calm" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 2, bezier = "calm" })

hl.animation({ leaf = "workspaces", enabled = true, speed = 4, bezier = "calm" })

-- ────────────────────────────────────────────────────────────
-- QUICKSHELL GLASS BLUR
-- ────────────────────────────────────────────────────────────
--
-- Quickshell's PanelWindow/WlrLayershell defaults its Wayland
-- namespace to "quickshell". Arch runs the entire desktop
-- shell as one Quickshell process, so this restores the old
-- Waybar/Mako/Walker/SwayOSD layer-blur effect at the compositor
-- level instead of trying to fake blur with shell colors.
--
-- `ignore_alpha = 0.1` lets translucent surfaces expose the blurred
-- desktop behind them. The bar and menu set their own Wayland layer
-- namespaces, so include them explicitly alongside Quickshell's default.
hl.layer_rule({
  match = { namespace = "^(quickshell|arch-(bar|menu|notifications|osd|polkit|reminders|clipboard|emojis|image-selector|keyboard-panel|network-qr))$" },
  blur = true,
  ignore_alpha = 0.1,
  blur_popups = true,
})

-- Keep the old Vicinae blur behavior too.
hl.layer_rule({
  match = { namespace = "vicinae" },
  blur = true,
  ignore_alpha = 0.1,
})

-- Arch / Custom window rules
-- Arch / Quickshell
-- Hyprland Lua configuration

-- Social Stream: disable Hyprland blur
--o.window(
--  { class = "^(socialstream)$" },
--  {
--    no_blur = true,
--  }
--)
