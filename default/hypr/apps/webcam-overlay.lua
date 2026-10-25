-- Keep the dedicated capture surface tiled and prevent it from stealing focus.
o.window({ class = "^WebcamOverlay-(small|medium|large)$", title = "^WebcamOverlay$" }, {
  no_initial_focus = true,
  no_dim = true,
})
