-- Learn how to configure Hyprland: https://wiki.hypr.land/Configuring/Start/

-- os's bootstrap keeps path setup out of this user config.
dofile((os.getenv("ARCH_PATH") or "/usr/share/arch") .. "/default/hypr/bootstrap.lua")

-- Disable all os default bindings. Add your own in hypr/bindings.lua.
-- arch_default_bindings = false
--
-- Or disable only bindings for os's preinstalled apps/web apps while
-- keeping core window-manager bindings:
-- arch_preinstalled_bindings = false

-- Load os defaults.
require("default.hypr.arch")

-- Put your personal overrides in these files. They're loaded after os's
-- defaults so package updates can improve the defaults without rewriting your
-- ~/.config/hypr files.
require("hypr.monitors")
require("hypr.input")
require("hypr.bindings")
require("hypr.looknfeel")
require("hypr.autostart")

-- Toggle config flags dynamically.
require("default.hypr.toggles")

-- Add any other personal Hyprland configuration below.
-- o.window("qemu", { workspace = "5" })
