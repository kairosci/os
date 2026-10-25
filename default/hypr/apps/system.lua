-- Fullscreen screensaver.
o.window("org.arch.screensaver", { fullscreen = true })
o.window("org.arch.screensaver", { animation = "slide" })
-- The launcher picks each screensaver's workspace. A terminal mapped again as it closes lands out of sight instead,
-- where its fullscreen rule cannot take fullscreen from a window.
o.window("org.arch.screensaver", { workspace = "special:screensaver silent" })

-- Prevent idle while open.
o.window({ tag = "noidle" }, { idle_inhibit = "always" })
