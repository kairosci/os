o.bind("SUPER + SPACE", "Menu", { menu = "root" })
o.bind("SUPER + CTRL + E", "Emojis", { panel = "arch.emojis" })
o.bind("SUPER + CTRL + C", "Capture menu", { menu = "capture" })
o.bind("SUPER + CTRL + O", "Toggle menu", { menu = "toggle" })
o.bind("SUPER + CTRL + H", "Hardware menu", { menu = "hardware" })
o.bind("SUPER + SHIFT + code:201", "Menu", { menu = "root" })
o.bind("SUPER + ESCAPE", "System menu", { menu = "system" })
o.bind("XF86PowerOff", "Power menu", { menu = "system" }, { locked = true })
o.bind("SUPER + K", "Keybindings", "arch-menu-keybindings")
o.bind("SUPER + ALT + K", "Tmux keybindings", "arch-menu-tmux-keybindings")
o.bind("SUPER + CTRL + K", "Herdr keybindings", "arch-menu-herdr-keybindings")
o.bind_toggle("SUPER + SHIFT + SPACE", "Toggle top bar", "bar")
o.bind("SUPER + CTRL + SPACE", "Background switcher", { menu = "background" })
o.bind("SUPER + CTRL + W", "Background switcher", { menu = "background" })
o.bind("SUPER + SHIFT + CTRL + SPACE", "Theme menu", { menu = "theme" })
o.bind("SUPER + CTRL + T", "Theme menu", { menu = "theme" })
o.bind("SUPER + BACKSPACE", "Toggle transparency on a window", "arch-hyprland-window-transparency-toggle")
o.bind("SUPER + SHIFT + BACKSPACE", "Toggle window gaps", "arch-hyprland-window-gaps-toggle")
o.bind("SUPER + CTRL + BACKSPACE", "Toggle single-window square aspect", "arch-hyprland-window-single-square-aspect-toggle")
o.bind_toggle("SUPER + CTRL + ALT + F", "Toggle full screen desktop", "fullscreen-desktop")

-- xkbcommon names the comma keysym "comma"; the upper-case "COMMA" does not match.
o.bind("SUPER + comma", "Dismiss last notification", { ipc = "notifications.dismissOne" })
o.bind("SUPER + SHIFT + comma", "Dismiss all notifications", { ipc = "notifications.dismissAll" })
o.bind_toggle("SUPER + CTRL + comma", "Toggle silencing notifications", "notification-silencing")
o.bind("SUPER + ALT + comma", "Invoke last notification", { ipc = "notifications.invokeLast" })
o.bind("SUPER + SHIFT + ALT + comma", "Open notification history", { ipc = "notifications.showHistory" })

o.bind_toggle("SUPER + CTRL + I", "Toggle locking on idle", "idle")
o.bind("SUPER + CTRL + Delete", "Toggle laptop display", "arch-hyprland-monitor-internal toggle")
o.bind("SUPER + CTRL + ALT + Delete", "Toggle laptop display mirroring", "arch-hyprland-monitor-internal-mirror toggle")
o.bind("switch:on:Lid Switch", nil, "arch-system-lid-close", { locked = true })
o.bind("switch:off:Lid Switch", nil, "arch-hyprland-monitor-clamshell", { locked = true })
-- Apple Silicon reports its lid through the SMC, under its own switch name.
o.bind("switch:on:Apple SMC power/lid events", nil, "arch-system-lid-close", { locked = true })
o.bind("switch:off:Apple SMC power/lid events", nil, "arch-hyprland-monitor-clamshell", { locked = true })

o.bind("PRINT", "Screenshot", "arch-capture-screenshot")
o.bind("SUPER + CTRL + ALT + C", "Screenshot", "arch-capture-screenshot")
o.bind("ALT + PRINT", "Screenrecording", "arch-capture-screenrecording --stop-recording || arch-menu toggle trigger.capture.screenrecord")
o.bind("SUPER + ALT + code:34", "Make webcam overlay smaller", "arch-capture-webcam-resize smaller")
o.bind("SUPER + ALT + code:35", "Make webcam overlay larger", "arch-capture-webcam-resize larger")
o.bind("SUPER + PRINT", "Color picker", "pkill hyprpicker || hyprpicker -a")
o.bind("SUPER + CTRL + PRINT", "Extract text (OCR) from screenshot", "arch-capture-text")

-- Keyboard control for the slurp region picker (see arch-capture-region).
-- The binds live exactly as long as a selection layer is on screen (slurp
-- opens one per monitor), so they cannot leak or get stuck.
-- Unbinding by key would take a same-key binding out of the user's own config
-- with it, so each handle is kept and removed individually.
local selection_layers = 0
local selection_binds = {}

hl.on("layer.opened", function(layer)
  if layer.namespace == "selection" then
    selection_layers = selection_layers + 1
    if selection_layers == 1 then
      selection_binds = {
        hl.bind("RETURN", hl.dsp.exec_cmd("arch-capture-region --take-window"), { description = "Capture highlighted window" }),
        hl.bind("CTRL + RETURN", hl.dsp.exec_cmd("arch-capture-region --take-fullscreen"), { description = "Capture entire screen" }),
        hl.bind("TAB", hl.dsp.exec_cmd("arch-capture-region --select-window next"), { description = "Select next window to capture" }),
        hl.bind("CTRL + TAB", hl.dsp.exec_cmd("arch-capture-region --select-window prev"), { description = "Select previous window to capture" }),
      }
      for _, direction in ipairs({ "left", "right", "up", "down" }) do
        table.insert(
          selection_binds,
          hl.bind(direction:upper(), hl.dsp.exec_cmd("arch-capture-region --select-window " .. direction), { description = "Select window to capture" })
        )
      end
    end
  end
end)

hl.on("layer.closed", function(layer)
  if layer.namespace == "selection" and selection_layers > 0 then
    selection_layers = selection_layers - 1
    if selection_layers == 0 then
      for _, keybind in ipairs(selection_binds) do
        keybind:unbind()
      end
      selection_binds = {}
    end
  end
end)

o.bind("SUPER + CTRL + S", "Share", { menu = "share" })

o.bind("SUPER + CTRL + PERIOD", "Transcode", "arch-transcode")

o.bind("SUPER + CTRL + R", "Set reminder", { menu = "reminder-set" })
o.bind("SUPER + CTRL + ALT + R", "Show reminders", "arch-reminder show")
o.bind("SUPER + SHIFT + CTRL + R", "Clear reminders", "arch-reminder clear")

o.bind("SUPER + CTRL + ALT + T", "Show time", "arch-notification-time")
o.bind("SUPER + CTRL + ALT + B", "Show battery remaining", "arch-notification-battery")
o.bind("SUPER + CTRL + ALT + W", "Toggle weather", "arch-notification-weather")

o.bind("SUPER + SHIFT + CTRL + A", "Agent", "arch-agent --pick")
o.bind("SUPER + CTRL + A", "Audio", { panel = "arch.audio" })
o.bind("SUPER + CTRL + B", "Bluetooth", { panel = "arch.bluetooth" })
o.bind("SUPER + CTRL + D", "Display", { panel = "arch.monitor" })
o.bind("SUPER + CTRL + ALT + D", "Calendar", { panel = "arch.clock" })
o.bind("SUPER + CTRL + ALT + E", "World clock", { panel = "arch.elsewhen" })
o.bind("SUPER + CTRL + N", "Network", { panel = "arch.network" })
o.bind("SUPER + CTRL + P", "Power", { panel = "arch.power" })
o.bind("SUPER + SHIFT + T", "Activity", { tui = "btop" })

-- The letters above name a panel; the numbers count them. 1 is the leftmost
-- panel in the bar's right section, and a widget with no panel of its own (the
-- tray) is not counted, so the number matches the icon a user would point at.
-- A bar with fewer panels than this leaves the tail of the range doing nothing.
for panel = 1, 9 do
  o.bind(
    "SUPER + CTRL + code:" .. tostring(panel + 9),
    "Bar panel " .. panel,
    "arch-shell -q shell togglePanelAt right " .. panel
  )
end

o.bind("SUPER + CTRL + Z", "Zoom in", function()
  local zoom = hl.get_config("cursor.zoom_factor") or 1
  hl.config({ cursor = { zoom_factor = zoom + 1 } })
end)

o.bind("SUPER + CTRL + ALT + Z", "Reset zoom", function()
  hl.config({ cursor = { zoom_factor = 1 } })
end)

o.bind("SUPER + CTRL + L", "Lock system", "arch-system-lock")
