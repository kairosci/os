-- Hyprland bootstrap for os's Lua module path.

local home = os.getenv("HOME")
local arch_path = rawget(_G, "ARCH_PATH") or os.getenv("ARCH_PATH") or "/usr/share/arch"
local inherited_arch_path = os.getenv("ARCH_PATH")
local reload_prefixes = {
  "default.hypr",
  "hypr",
  "arch.current.theme",
}

local function should_reload_module(module)
  for _, prefix in ipairs(reload_prefixes) do
    if module == prefix or module:sub(1, #prefix + 1) == prefix .. "." then
      return true
    end
  end

  return false
end

local modules_to_reload = {}
for module in pairs(package.loaded) do
  if should_reload_module(module) then
    table.insert(modules_to_reload, module)
  end
end

for _, module in ipairs(modules_to_reload) do
  package.loaded[module] = nil
end

local inherited_package_paths = {}
for entry in package.path:gmatch("[^;]+") do
  local stale_prefix = inherited_arch_path and inherited_arch_path .. "/"
  if not stale_prefix or entry:sub(1, #stale_prefix) ~= stale_prefix then
    table.insert(inherited_package_paths, entry)
  end
end

-- Load generated state from ~/.local/state, user modules from ~/.config, and
-- os defaults from $ARCH_PATH.
package.path = home
  .. "/.local/state/?.lua;"
  .. home
  .. "/.config/?.lua;"
  .. arch_path
  .. "/?.lua;"
  .. table.concat(inherited_package_paths, ";")
