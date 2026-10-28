-- Essential application bindings.
o.bind("SUPER + RETURN", "Terminal", o.launch_terminal())
o.bind("SUPER + SHIFT + RETURN", "Browser", { arch = "browser" })
o.bind("SUPER + SHIFT + F", "File manager", { arch = "nautilus" })
o.bind("SUPER + ALT + SHIFT + F", "File manager (cwd)", { arch = "nautilus-cwd" })
o.bind("SUPER + SHIFT + B", "Browser", { arch = "browser" })
o.bind("SUPER + SHIFT + ALT + B", "Browser (private)", { arch = "browser --private" })
o.bind("SUPER + SHIFT + N", "Editor", { arch = "editor" })

if o.cmd_present("lazydocker") then
  o.bind("SUPER + SHIFT + D", "Docker", { tui = "arch-launch-docker-tui" })
end
