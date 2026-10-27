-- Essential application bindings.
o.bind("SUPER + RETURN", "Terminal", o.launch_terminal())
o.bind("SUPER + SHIFT + RETURN", "Browser", { arch = "browser" })
o.bind("SUPER + SHIFT + F", "File manager", { arch = "nautilus" })
o.bind("SUPER + ALT + SHIFT + F", "File manager (cwd)", { arch = "nautilus-cwd" })
o.bind("SUPER + SHIFT + B", "Browser", { arch = "browser" })
o.bind("SUPER + SHIFT + ALT + B", "Browser (private)", { arch = "browser --private" })
o.bind("SUPER + SHIFT + N", "Editor", { arch = "editor" })

if o.preinstalled_bindings_enabled() then
  -- Bindings for preinstalled os applications, TUIs, and web apps.
  o.bind("SUPER + ALT + RETURN", "Tmux", { arch = "terminal-tmux" })
  o.bind("SUPER + CTRL + RETURN", "Herdr", { arch = "terminal-herdr" })
  o.bind("SUPER + SHIFT + Q", "Calculator", "omacalc")
  o.bind("XF86Calculator", "Calculator", "omacalc")
  o.bind("SUPER + SHIFT + M", "Music", { arch = "spotify" })
  o.bind("SUPER + SHIFT + ALT + M", "Music TUI", { tui = "cliamp", focus = true })
  if o.cmd_present("lazydocker") then
    o.bind("SUPER + SHIFT + D", "Docker", { tui = "arch-launch-docker-tui" })
  end
  o.bind("SUPER + SHIFT + G", "Signal", { arch = "signal" })
  o.bind("SUPER + SHIFT + O", "Obsidian", { launch = "obsidian", focus = "^obsidian$" })
  o.bind("SUPER + SHIFT + W", "Omawrite", { launch = "omawrite" })
  o.bind("SUPER + SHIFT + SLASH", "Passwords", { arch = "1password" })

  o.bind("SUPER + SHIFT + C", "Calendar", { webapp = "https://app.hey.com/calendar/weeks/" })
  o.bind("SUPER + SHIFT + E", "Email", { webapp = "https://app.hey.com" })
  o.bind("SUPER + SHIFT + ALT + E", "New email", { webapp = "https://app.hey.com/messages/new?display=standalone&new_window=true" })
  o.bind("SUPER + SHIFT + Y", "YouTube", { webapp = "https://youtube.com/" })
  o.bind("SUPER + SHIFT + ALT + G", "WhatsApp", { webapp = "https://web.whatsapp.com/", focus = true })
  o.bind( "SUPER + SHIFT + CTRL + G", "Google Messages", { webapp = "https://messages.google.com/web/conversations", focus = true })
  o.bind("SUPER + SHIFT + P", "Google Photos", { webapp = "https://photos.google.com/", focus = true })
  o.bind("SUPER + SHIFT + S", "Google Maps", { webapp = "https://maps.google.com/", focus = true })
  o.bind("SUPER + SHIFT + X", "X", { webapp = "https://x.com/" })
  o.bind("SUPER + SHIFT + ALT + X", "X Post", { webapp = "https://x.com/compose/post" })
end
