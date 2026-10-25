require("default.hypr.startup-cursor")

hl.on("hyprland.start", function()
  -- Applications inherit the user's cursor; only the compositor starts blank.
  if arch_startup_cursor_pending then
    hl.env("XCURSOR_PATH", arch_startup_cursor.path)
    hl.env("XCURSOR_THEME", arch_startup_cursor.xcursor)
  end

  -- Slow app launch fix -- set systemd and D-Bus activation vars before
  -- starting session services.
  hl.exec_cmd("dbus-update-activation-environment --systemd --all")

  hl.exec_cmd("arch-launch-shell")
  hl.exec_cmd("arch-provision-first-run")
  hl.exec_cmd("arch-powerprofiles-init")
  hl.exec_cmd(o.launch("arch-hyprland-monitor-watch"))
  hl.exec_cmd(o.launch("udiskie --automount --no-notify --no-tray"))

  -- Run post-boot hooks after startup config has loaded.
  hl.exec_cmd("sleep 2 && arch-hook post-boot")
end)
