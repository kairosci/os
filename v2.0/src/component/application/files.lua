local File = require("core.file")
local Files = {}
Files.__index = Files

function Files.new(root, paths, publisher, process, registry)
    return setmetatable({root=root, paths=paths, publisher=publisher, process=process, registry=registry}, Files)
end

function Files:apply(name)
    local policy = assert(self.registry[name], "unknown_application")
    assert(policy.kind == "file" or policy.kind == "launcher", "unsupported_file")
    local source = policy.sourceRoot == "project" and self.root .. "/" .. policy.source or policy.source
    local content = File.read(source)
    if policy.kind == "launcher" then
        assert(content:find("[Desktop Entry]", 1, true), "invalid_desktop_entry")
        content = content:gsub("([^\n]+)", function(line)
            if line:match("^Exec=") then return "Exec=" .. policy.execPrefix .. line:sub(6) end
            return line
        end)
    end
    self.publisher:publish(self.paths:resolve(policy.root, policy.destination), content, policy.mode)
    if policy.refresh then self.process:run(policy.refresh.command, {self.paths:resolve(policy.root, policy.refresh.directory)}) end
    return policy.display
end

return Files
