# Desktop Product Quality

Use this skill for default applications, desktop panels, theme previews, visual assets, and user-facing tools.

## Defaults and tool selection

- Keep the default installation focused. Remove obsolete Omarchy branding, applications, configuration, and migration debris when no installed-system compatibility depends on them.
- Choose one default tool for each category. Do not ship multiple tools that solve the same job unless a documented user need requires them.
- Keep enabled top and side bars autohiding. Revealing a bar must expose its configured features; autohide must not silently remove widgets or controls.
- Keep workspace labels numeric, including the active workspace; do not replace its number with a dot or layout glyph.
- Design the vertical side bar for its edge placement with compact spacing and clear controls; verify its hidden and revealed states.
- Keep configured top bar indicators visible while the bar is shown; inactive controls may be dimmed, but must not require hover to discover or reach.
- Keep theme previews focused on the theme itself, without open application windows or unrelated desktop clutter.

## Visual assets and verification

- Do not generate photographic backgrounds or preview imagery. Capture the actual running desktop when a screenshot is required.
- Inspect the screenshot for the requested theme, visible artifacts, clipping, overlap, stale windows, and layout errors before calling the work complete.
- Use the Arch Braille mark in Fastfetch and verify that the actual terminal renders it legibly.
- Restore the established icon theme when theme integration changes cause GNOME or Cosmic icons to replace it unexpectedly.

## Completion

- Verify defaults from package composition and the resulting installed configuration, not only from a source file.
- For visual changes, capture and inspect the running interface using `.agents/skills/visual-verification.md`.
- Record unfinished cleanup and its evidence in `sprint.md`.
