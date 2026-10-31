-- Application window and layer behavior is user-editable YAML. Python only
-- reads and validates the data, then emits a Lua table; this module applies it.
local paths = require("default.hypr.paths")

local function shell_quote(value)
  return "'" .. value:gsub("'", "'\\''") .. "'"
end

local command = "python3 -I " .. shell_quote(paths.ap .. "/default/hypr/app_rules.py")
local handle = io.popen(command, "r")
local source = handle and handle:read("*a") or ""
local success
local close_reason
local status
if handle then
  success, close_reason, status = handle:close()
end

if not success then
  print(
    "Hyprland app rules were not loaded: "
      .. source
      .. " (status "
      .. tostring(status)
      .. ", "
      .. tostring(close_reason)
      .. ")"
  )
else
  local chunk, load_error = loadstring(source, "@Hyprland app rules")
  if not chunk then
    print("Hyprland app rules were not loaded: " .. load_error)
  else
    setfenv(chunk, {})
    local loaded, configuration = pcall(chunk)
    if not loaded or type(configuration) ~= "table" then
      print("Hyprland app rules were not loaded: " .. tostring(configuration))
    else
      o.app_transparency = configuration.transparent_opacity
      o.app_transparency_tag = configuration.transparent_tag
      for _, rule in ipairs(configuration.window_rules or {}) do
        local applied, rule_error = pcall(o.window, rule.match, rule.options)
        if not applied then
          print("Hyprland app rule was not applied: " .. tostring(rule_error))
        end
      end
      for _, rule in ipairs(configuration.layer_rules or {}) do
        local definition = { match = rule.match }
        for key, value in pairs(rule.options) do
          definition[key] = value
        end
        local applied, rule_error = pcall(hl.layer_rule, definition)
        if not applied then
          print("Hyprland layer rule was not applied: " .. tostring(rule_error))
        end
      end
    end
  end
end
