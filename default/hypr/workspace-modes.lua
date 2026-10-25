-- Restore tiled workspace layouts saved by arch-hyprland-workspace-layout-toggle.
local M = {}
local modes = {}
local default_mode = "dwindle"

function o.workspace_mode(spec)
  local mode = spec.default or spec.mode
  if mode == "floating" then mode = "dwindle" end
  if mode ~= "dwindle" and mode ~= "scrolling" then return end

  if spec.default then
    default_mode = mode
    hl.config({ general = { layout = mode } })
  else
    local workspace = tostring(spec.workspace)
    modes[workspace] = mode
    hl.workspace_rule({ workspace = workspace, layout = mode })
  end
end

function M.apply()
  if default_mode ~= "dwindle" and default_mode ~= "scrolling" then
    default_mode = "dwindle"
  end
  hl.config({ general = { layout = default_mode } })
  for workspace, mode in pairs(modes) do
    if mode == "dwindle" or mode == "scrolling" then
      hl.workspace_rule({ workspace = workspace, layout = mode })
    end
  end
end

return M
