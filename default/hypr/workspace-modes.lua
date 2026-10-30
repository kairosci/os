-- Restore tiled workspace layouts saved by arch-hyprland-workspace-layout-toggle.
local M = {}
local modes = {}
local default_mode = "scrolling"
local hyprland_layouts = { tiling = "dwindle", scrolling = "scrolling" }

function o.workspace_mode(spec)
  local mode = spec.default or spec.mode
  if mode == "floating" then mode = "scrolling" end
  if mode == "dwindle" then mode = "tiling" end
  local layout = hyprland_layouts[mode]
  if not layout then return end

  if spec.default then
    default_mode = mode
    hl.config({ general = { layout = layout } })
  else
    local workspace = tostring(spec.workspace)
    modes[workspace] = mode
    hl.workspace_rule({ workspace = workspace, layout = layout })
  end
end

function M.apply()
  if not hyprland_layouts[default_mode] then
    default_mode = "scrolling"
  end
  hl.config({ general = { layout = hyprland_layouts[default_mode] } })
  for workspace, mode in pairs(modes) do
    local layout = hyprland_layouts[mode]
    if layout then
      hl.workspace_rule({ workspace = workspace, layout = layout })
    end
  end
end

return M
