local File = require("core.file")
local Blocks = require("core.blocks")
local Namespace = require("core.user_configuration")
local Desktop = {}
Desktop.__index = Desktop

function Desktop.new(root, paths, publisher, process, catalog, policy, environment)
    return setmetatable({root=assert(root), paths=assert(paths), publisher=assert(publisher), process=assert(process), catalog=assert(catalog), policy=assert(policy), getenv=environment or os.getenv}, Desktop)
end

function Desktop:content(path)
    assert(self.process:status("isLink", {path}) == 1, "redirected_managed_path")
    local handle, failure, code = io.open(path, "rb")
    if not handle then assert(code == 2, failure); return nil end
    local content = assert(handle:read("a")); assert(handle:close())
    return content
end

function Desktop:remove(path)
    if self:content(path) then assert(os.remove(path)) end
end

function Desktop:migrate()
    local policy = self.policy
    Namespace.new(self.paths, self.process, File.json(self.root .. "/" .. policy.namespace)):migrate()
end

function Desktop:shell()
    local policy, shell = self.policy, assert(self.policy.shell, "invalid_desktop_shell")
    local destination = self.paths:resolve("home", shell.file)
    local existing, metadata = self.publisher:inspect(destination)
    if not existing then return end
    local content = existing
    for _, block in ipairs(shell.blocks) do
        local removed = Blocks.remove(content, block.first, block.last)
        if removed then content = removed end
    end
    if content ~= existing then self.publisher:publish(destination, content, ("%o"):format(metadata & 0xFFF)) end
end

function Desktop:retire(retirement)
    for _, name in ipairs(retirement.names) do
        self:remove(self.paths:resolve(retirement.root, retirement.directory .. "/" .. name))
    end
end

function Desktop:publish(entries)
    for _, entry in ipairs(entries) do
        self.publisher:publish(self.paths:resolve(entry.root, entry.destination), File.read(self.root .. "/" .. entry.source), entry.mode)
    end
end

function Desktop:launcher()
    local launcher = assert(self.policy.launcher, "invalid_desktop_launcher")
    local content = File.read(self.root .. "/" .. launcher.source)
    assert(content:find("[Desktop Entry]", 1, true), "invalid_desktop_entry")
    self.publisher:publish(self.paths:resolve(launcher.root, launcher.destination), content, launcher.mode)
    if launcher.refresh then self.process:run(launcher.refresh.command, {self.paths:resolve(launcher.root, launcher.refresh.directory)}) end
end

function Desktop:apply()
    local policy = self.policy
    self:migrate()
    self:shell()
    self:retire(policy.retiredHooks)
    self:launcher()
    self:publish(policy.files)
    self:retire(policy.retiredToggles)
    return policy.display
end

function Desktop:backup(backup, mode, relative)
    local source = self.paths:resolve("config", relative)
    if not self:content(source) then return end
    local destination = backup .. "/" .. relative
    if self:content(destination) then return end
    local parent = assert(destination:match("^(.*)/[^/]+$"), "invalid_backup_path")
    self.process:run("directory", {parent})
    self.process:run("permissions", {mode, backup})
    local directory = backup
    for segment in relative:match("^(.*)/[^/]+$"):gmatch("[^/]+") do
        directory = directory .. "/" .. segment
        self.process:run("permissions", {mode, directory})
    end
    self.process:run("copy", {source, destination})
end

function Desktop:restore()
    local policy = self.policy
    local restore = assert(policy.restore, "invalid_desktop_restore")
    local upstream = self.getenv(restore.upstreamVariable)
    if not upstream or upstream == "" then upstream = restore.upstreamDefault end
    assert(upstream:sub(1, 1) == "/", "absolute_upstream_required")
    local backup = self.paths:resolve("state", restore.backupDirectory)
    self:migrate()
    for _, file in ipairs(restore.terminalFiles) do
        self:backup(backup, restore.backupMode, file)
        self.publisher:publish(self.paths:resolve("config", file), File.read(upstream .. "/" .. restore.upstreamConfig .. "/" .. file), "644")
    end
    for _, asset in ipairs(restore.brandingFiles) do
        local destination = "os/branding/" .. asset
        self:backup(backup, restore.backupMode, destination)
        self.publisher:publish(self.paths:resolve("config", destination), File.read(self.root .. "/" .. restore.brandingSource), "644")
    end
    self.publisher:publish(self.paths:resolve("config", restore.fastfetchDestination), File.read(self.root .. "/" .. restore.fastfetchSource), "644")
    self:retire(policy.retiredToggles)
    io.write(self.catalog:text("recovery.terminals_ready", backup), "\n")
end

return Desktop
