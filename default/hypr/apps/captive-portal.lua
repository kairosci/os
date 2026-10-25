-- Captive portal sign-in; arch-network-captive-portal closes it once online.
local captive_portal = "^chrome-ping\\.omacom\\.io__.*$"
o.window(captive_portal, { tag = "-chromium-based-browser" })
