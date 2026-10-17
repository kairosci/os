local root = assert(arg[1])
package.path = root .. "/src/?.lua;" .. package.path
local Json = require("core.json")
local File = require("core.file")
local Process = require("core.process")
local Catalog = require("core.catalog")
local Menu = require("component.boot.menu")
local Publisher = require("core.publisher")
local Suite = {}
Suite.__index = Suite

function Suite.new()
    return setmetatable({passed=0, failed=0}, Suite)
end

function Suite:test(name, callback)
    local ok, failure = pcall(callback)
    if ok then self.passed = self.passed + 1; print("  pass " .. name)
    else self.failed = self.failed + 1; print("  fail " .. name .. ": " .. tostring(failure)) end
end

function Suite:reject(callback)
    assert(not pcall(callback), "invalid_input_accepted")
end

function Suite:finish()
    print(("Summary: Tests Executed: %d | Passed: %d | Failed: %d | Warnings: 0"):format(self.passed + self.failed, self.passed, self.failed))
    os.exit(self.failed == 0 and 0 or 1)
end

local suite = Suite.new()
local process = Process.new(File.json(root .. "/data/core/commands.json"))
local menu = Menu.new(process, File.json(root .. "/data/component/boot/render.json"))
local policy = File.json(root .. "/data/component/boot/policy.json").menu
local function source(path, command)
    return "/Arch\n //linux\n protocol: efi\n path: boot():" .. path .. "\n cmdline: " .. (command or "cryptdevice=fixture root=/dev/mapper/root rootflags=subvol=@ resume_offset=123 lsm=apparmor") .. "\n"
end

if arg[2] == "repository" then
    assert(loadfile(root .. "/tests/lua/repository.lua"))()(suite, root, process)
elseif arg[2] == "neovim" then
    assert(loadfile(root .. "/tests/lua/neovim.lua"))()(suite, root, process)
elseif arg[2] == "terminal" then
    assert(loadfile(root .. "/tests/lua/terminal.lua"))()(suite, root, process)
elseif arg[2] == "media" then
    assert(loadfile(root .. "/tests/lua/media_plugin.lua"))()(suite, root, process)
elseif arg[2] == "project" then
    assert(loadfile(root .. "/tests/lua/project_interface.lua"))()(suite, root, process)
elseif arg[2] == "cli" then
    assert(loadfile(root .. "/tests/lua/cli_behavior.lua"))()(suite, root, process)
elseif arg[2] == "cli-scope" then
    assert(loadfile(root .. "/tests/lua/cli_scope.lua"))()(suite, root, process)
elseif arg[2] == "cli-install" then
    assert(loadfile(root .. "/tests/lua/cli_install.lua"))()(suite, root, process)
elseif arg[2] == "test-runner" then
    assert(loadfile(root .. "/tests/lua/test_runner.lua"))()(suite, root, process)
elseif arg[2] == "platform" then
    assert(loadfile(root .. "/tests/lua/platform.lua"))()(suite, root)
elseif arg[2] == "boot-trial" then
    assert(loadfile(root .. "/tests/lua/boot_trial.lua"))()(suite, root, process)
elseif arg[2] == "json" then
    assert(loadfile(root .. "/tests/lua/documentation.lua"))()(suite, root, process)
    local cliInstallTests = assert(loadfile(root .. "/tests/lua/cli_install.lua"))()
    cliInstallTests(suite, root, process)
    local settingsTests = assert(loadfile(root .. "/tests/lua/settings.lua"))()
    settingsTests(suite, root, process)
    local appearanceTests = assert(loadfile(root .. "/tests/lua/boot_appearance.lua"))()
    appearanceTests(suite, root, process)
    local candidateTests = assert(loadfile(root .. "/tests/lua/boot_candidate.lua"))()
    candidateTests(suite, root, process)
    assert(loadfile(root .. "/tests/lua/boot_assessment.lua"))()(suite, root, process)
    suite:test("migration inventory cannot certify retained shell algorithms", function()
        local Inventory = require("component.migration.inventory")
        local inventory = Inventory.new(root, process, File.json(root .. "/data/component/migration/policy.json"))
        local report = inventory:report()
        assert(not report.complete and #report.remaining > 0 and #report.starters == 7)
        assert(inventory:classify("module/tool", "#!/usr/bin/env bash\nexit 0\n") == "shell")
        assert(inventory:classify("module/tool", "#!/bin/sh\nexit 0\n") == "shell")
        assert(inventory:classify("module/test.rb", "") == "ruby")
        assert(inventory:classify("data/hidden.sh", "") == "shell")
        suite:reject(function() inventory:classify("v2.0/script/os-lua", "#!/bin/bash\nbash legacy.sh\n") end)
    end)
    suite:test("versioned entry points preserve the entire repository migration inventory", function()
        local Inventory = require("component.migration.inventory")
        local policy = File.json(root .. "/data/component/migration/policy.json")
        local repository = Inventory.new(root, process, policy).root
        local canonical = Inventory.new(repository .. "/v2.0", process, policy):report()
        local legacy = Inventory.new(repository, process, policy):report()
        assert(Json.encode(canonical) == Json.encode(legacy))
        local found = false
        for _, item in ipairs(canonical.remaining) do
            if item.path == "v2.0/scripts/setup.sh" then found = true end
        end
        assert(found and not canonical.complete)
        assert(File.read(root .. "/src/main.lua") == File.read(repository .. "/v2.0/src/main.lua"))
        assert(File.read(root .. "/tests/lua/run.lua") == File.read(repository .. "/v2.0/tests/lua/run.lua"))
    end)
    suite:test("tracked project contents have one active versioned home", function()
        local Inventory = require("component.migration.inventory")
        local repository = Inventory.new(root, process, File.json(root .. "/data/component/migration/policy.json")).root
        local layout = File.json(root .. "/data/component/migration/layout.json")
        local native, links = {}, {}
        for _, path in ipairs(layout.nativeFiles) do native[path] = true end
        for _, path in ipairs(layout.links) do links[path] = true end
        local files = process:run("repositoryFiles", {"-c", "safe.directory=" .. repository, "-C", repository, "ls-files", "-z"})
        for path in files:gmatch("[^%z]+") do
            local allowed = path:sub(1, #layout.active) == layout.active or path:sub(1, #layout.archive) == layout.archive or native[path]
            for _, prefix in ipairs(layout.nativeDirectories) do if path:sub(1, #prefix) == prefix then allowed = true end end
            if links[path] then
                local mode = tonumber(process:run("fileMode", {repository .. "/" .. path}), 16)
                assert(mode and mode & 0xF000 == 0xA000, "root_entry_must_be_link_" .. path)
                local target = process:run("realpath", {repository .. "/" .. path}):gsub("\n$", "")
                assert(target:sub(1, #repository + #layout.active + 1) == repository .. "/" .. layout.active, "root_entry_escapes_active_tree_" .. path)
                allowed = true
            end
            assert(allowed, "unversioned_project_content_" .. path)
        end
    end)
    suite:test("performance planning bounds work by both RAM and processors", function()
        local Editor = require("component.performance.editor")
        local policy = File.json(root .. "/data/component/performance/policy.json")
        assert(Editor.plan("MemTotal: 2097152 kB\n", 2, policy).workers == 1)
        assert(Editor.plan("MemTotal: 16777216 kB\n", 12, policy).workers == 4)
        assert(Editor.plan("MemTotal: 67108864 kB\n", 32, policy).workers == policy.maximumWorkers)
        assert(Editor.plan("MemTotal: 16777216 kB\n", 1, policy).workers == 1)
        suite:reject(function() Editor.plan("invalid", 12, policy) end)
        suite:reject(function() Editor.plan("MemTotal: 100 kB\n", 0, policy) end)
    end)
    suite:test("performance settings preserve unrelated language server options", function()
        local Editor = require("component.performance.editor")
        local settings = Json.decode([[{"lsp":{"rust-analyzer":{"initialization_options":{"cargo":{"extraEnv":{"PERSONAL":"keep"}},"checkOnSave":true}}},"personal":[1,2]}]])
        Editor.assign(settings, {"lsp","rust-analyzer","initialization_options","cargo","extraEnv","CARGO_BUILD_JOBS"}, "3")
        local options = settings.lsp["rust-analyzer"].initialization_options
        assert(options.cargo.extraEnv.PERSONAL == "keep" and options.checkOnSave == true)
        assert(settings.personal[2] == 2 and options.cargo.extraEnv.CARGO_BUILD_JOBS == "3")
        suite:reject(function() Editor.assign({lsp=false}, {"lsp","rust-analyzer"}, {}) end)
    end)
    suite:test("managed blocks preserve personal text and reject incomplete boundaries", function()
        local Blocks = require("core.blocks")
        local result = Blocks.merge("export PERSONAL=1\n", "# begin", "# end", "export CARGO_BUILD_JOBS=3")
        assert(result:find("export PERSONAL=1", 1, true))
        assert(Blocks.merge(result, "# begin", "# end", "export CARGO_BUILD_JOBS=3") == result)
        suite:reject(function() Blocks.merge("# begin\n", "# begin", "# end", "value") end)
        suite:reject(function() Blocks.merge("# end\n", "# begin", "# end", "value") end)
    end)
    suite:test("build environment persists calculated limits without using the real session bus", function()
        local Environment = require("component.performance.environment")
        local Paths = require("core.paths")
        local directory = process:run("temporary", {"-d"}):gsub("\n$", "")
        local policy = File.json(root .. "/data/component/performance/policy.json")
        policy.memoryInfo = directory .. "/memory"
        local publisher = Publisher.new(process)
        publisher:publish(policy.memoryInfo, "MemTotal: 16777216 kB\n", "600")
        publisher:publish(directory .. "/.bashrc", "export PERSONAL=1\n", "600")
        local paths = Paths.new(File.json(root .. "/data/core/paths.json"), function(key) if key == "HOME" then return directory end end)
        local activations = 0
        local backend = {run=function(_, command, arguments)
            if command == "processorCount" then return "12\n"
            elseif command == "userEnvironment" then
                assert(#arguments == 1 and arguments[1] == "CARGO_BUILD_JOBS=4")
                activations = activations + 1
                return ""
            end
            return process:run(command, arguments)
        end}
        local instance = Environment.new(backend, paths, publisher, policy)
        process:run("permissions", {"755", directory})
        instance:apply()
        assert(tonumber(process:run("fileMode", {directory}), 16) & 0x1FF == tonumber("750", 8))
        local shell = File.read(directory .. "/.bashrc")
        assert(shell:find("export PERSONAL=1", 1, true) and shell:find("export CARGO_BUILD_JOBS=4", 1, true))
        assert(tonumber(process:run("fileMode", {directory .. "/.bashrc"}), 16) & 0x1FF == 0x180)
        process:run("permissions", {"700", directory})
        instance:apply()
        assert(tonumber(process:run("fileMode", {directory}), 16) & 0x1FF == tonumber("700", 8))
        assert(File.read(directory .. "/.bashrc") == shell and activations == 2)
        instance:apply(true)
        assert(activations == 2)
        local destination = paths:resolve(policy.environment.root, policy.environment.file)
        local before = File.read(destination)
        publisher:publish(directory .. "/.bashrc", policy.environment.first .. "\n", "600")
        suite:reject(function() instance:apply() end)
        assert(File.read(destination) == before and activations == 2)
        process:run("removeDirectory", {directory})
    end)
    suite:test("JSON round trips arrays false null and Unicode", function()
        local value = Json.decode([[{"values":[false,null,"\uD83D\uDE00",1.25e2]}]])
        assert(value.values[1] == false and value.values[2] == Json.null and value.values[3] == "😀" and value.values[4] == 125)
        assert(Json.encode(Json.decode(Json.encode(value))) == Json.encode(value))
    end)
    for _, invalid in ipairs({'{"key":1,"key":2}', '[1,]', '01', '+1', '1.', '1e+', 'true false', '"\\uD800"', '"\\x"', '{"x" 1}', '"raw\nline"'}) do
        suite:test("JSON rejects invalid input " .. Json.encode(invalid), function() suite:reject(function() Json.decode(invalid) end) end)
    end
    suite:test("process argument quoting never executes shell substitutions", function()
        local runner = Process.new({print={"/usr/bin/printf", "%s"}})
        local argument = "a' b $(exit 43); `exit 44`"
        assert(runner:run("print", {argument}) == argument)
    end)
    suite:test("failed native processes propagate", function()
        local runner = Process.new({fail={"/usr/bin/false"}})
        suite:reject(function() runner:run("fail") end)
        assert(runner:status("fail") == 1)
        local exits = Process.new({exit={"/usr/bin/sh", "-c", "exit 37"}})
        assert(exits:status("exit") == 37)
    end)
elseif arg[2] == "catalog" then
    local locale = File.json(root .. "/data/core/locale.json")
    for _, language in ipairs(locale.languages) do
        suite:test("catalog selects " .. language .. " with environment precedence", function()
            local catalog = Catalog.new(locale, root .. "/data/catalog", function(key)
                return ({OS_LANG=language .. "_XX.UTF-8", LANG="de_DE.UTF-8"})[key]
            end)
            assert(catalog.language == language and catalog:text("boot.validation_failed", "invalid_efi"):find("invalid_efi", 1, true))
        end)
    end
    suite:test("unknown translation keys fail explicitly", function()
        local catalog = Catalog.new(locale, root .. "/data/catalog", function() return "en" end)
        suite:reject(function() catalog:text("missing.key") end)
    end)
    suite:test("unsupported language follows explicit locale policy", function()
        local catalog = Catalog.new(locale, root .. "/data/catalog", function() return "xx" end)
        assert(catalog.language == locale.default)
    end)
elseif arg[2] == "applications" then
    local Settings = require("component.application.settings")
    local registry = File.json(root .. "/data/component/application/policy.json")
    for name, policy_entry in pairs(registry) do
        if policy_entry.kind == "settings" then
        suite:test("Lua applies every declared setting for " .. name, function()
            local calls = {}
            local backend = {run=function(_, command, arguments)
                if arguments[1] == "list-schemas" then return "org.gnome.Resources\n" end
                assert(command == "gsettings" and arguments[1] == "set" and #arguments == 4)
                calls[#calls + 1] = table.concat(arguments, "\t")
                return ""
            end}
            assert(Settings.new(root, backend, registry):apply(name) == policy_entry.display)
            local lines = File.list(root .. "/" .. policy_entry.settings)
            assert(#calls == #lines)
            for index, line in ipairs(lines) do
                if policy_entry.schemaSelection then line = line:gsub("net.nokyan.Resources", "org.gnome.Resources", 1) end
                assert(calls[index] == "set\t" .. line)
            end
        end)
        end
    end
    local Files = require("component.application.files")
    local Paths = require("core.paths")
    local directory = process:run("temporary", {"-d"}):gsub("\n$", "")
    local paths = Paths.new(File.json(root .. "/data/core/paths.json"), function(key) if key == "HOME" then return directory end end)
    local publisher = Publisher.new(process)
    suite:test("Lua installs native browser flags with a backup of existing preferences", function()
        local destination = paths:resolve("config", registry.brave.destination)
        publisher:publish(destination, "--personal\n", "644")
        Files.new(root, paths, publisher, process, registry):apply("brave")
        assert(File.read(destination) == File.read(root .. "/" .. registry.brave.source))
        assert(File.read(destination .. ".bak") == "--personal\n")
        assert(os.remove(destination)); assert(os.remove(destination .. ".bak"))
    end)
    suite:test("Lua Electron integration preserves every packaged action and argument", function()
        local source = directory .. "/fixture.desktop"
        local native = "[Desktop Entry]\nType=Application\nExec=/usr/bin/sample --original %U\n[Desktop Action New]\nExec=/usr/bin/sample --new %F\n"
        publisher:publish(source, native, "644")
        local definition = Json.decode(Json.encode(registry.slack))
        definition.source = source
        local refreshed = 0
        local backend = {run=function(_, command, arguments)
            assert(command == "desktopDatabase" and arguments[1] == paths:resolve("data", "applications"))
            refreshed = refreshed + 1
        end}
        local files = Files.new(root, paths, publisher, backend, {fixture=definition})
        files:apply("fixture")
        local destination = paths:resolve("data", definition.destination)
        local content = File.read(destination)
        assert(content:find("Exec=env GTK_USE_PORTAL=1 /usr/bin/sample --original %U", 1, true))
        assert(content:find("Exec=env GTK_USE_PORTAL=1 /usr/bin/sample --new %F", 1, true))
        assert(not content:find("ozone-platform", 1, true))
        files:apply("fixture")
        assert(File.read(destination) == content and refreshed == 2)
        assert(os.remove(destination)); assert(os.remove(source))
    end)
    local Desktop = require("component.application.desktop")
    local desktopDirectory = process:run("temporary", {"-d"}):gsub("\n$", "")
    local desktopPaths = Paths.new(File.json(root .. "/data/core/paths.json"), function(variable)
        if variable == "HOME" then return desktopDirectory end
        return ""
    end)
    local desktopPolicy = File.json(root .. "/data/component/application/desktop/policy.json")
    local desktopCatalog = Catalog.new(File.json(root .. "/data/core/locale.json"), root .. "/data/catalog")
    local desktop = function()
        return Desktop.new(root, desktopPaths, publisher, process, desktopCatalog, desktopPolicy)
    end
    suite:test("Lua desktop integration retires managed shell helpers and hooks", function()
        local home = desktopPaths:resolve("home", ".bashrc")
        publisher:publish(home, "export PERSONAL=1\n" .. desktopPolicy.shell.blocks[1].first .. "\nfunction mh() { printf old; }\n" .. desktopPolicy.shell.blocks[1].last .. "\n" .. desktopPolicy.shell.blocks[2].first .. "\nfunction dh() { printf old; }\n" .. desktopPolicy.shell.blocks[2].last .. "\n", "600")
        for _, name in ipairs({"micro-theme", "disk-theme", "gtk-theme"}) do
            publisher:publish(desktopPaths:resolve("config", desktopPolicy.retiredHooks.directory .. "/" .. name), "hook\n", "755")
        end
        publisher:publish(desktopPaths:resolve("config", "os/branding/screensaver.txt"), "old screensaver logo\n", "644")
        publisher:publish(desktopPaths:resolve("config", "os/branding/about.txt"), "old About logo\n", "644")
        publisher:publish(desktopPaths:resolve("state", "omarchy/toggles/screensaver-off"), "", "644")
        assert(desktop():apply() == desktopPolicy.display)
        local shell = File.read(home)
        assert(shell:find("export PERSONAL=1", 1, true))
        assert(not shell:find("function mh", 1, true) and not shell:find("function dh", 1, true))
        assert(tonumber(process:run("fileMode", {home}), 16) & 0x1FF == tonumber("600", 8))
        assert(File.read(desktopPaths:resolve("data", desktopPolicy.launcher.destination)):find("[Desktop Entry]", 1, true))
        assert(File.read(desktopPaths:resolve("config", "os/branding/screensaver.txt")) == File.read(root .. "/" .. desktopPolicy.restore.brandingSource))
        assert(File.read(desktopPaths:resolve("config", "os/branding/screensaver.txt.bak")) == "old screensaver logo\n")
        for _, name in ipairs(desktopPolicy.retiredHooks.names) do
            assert(not io.open(desktopPaths:resolve("config", desktopPolicy.retiredHooks.directory .. "/" .. name), "rb"))
        end
        assert(io.open(desktopPaths:resolve("config", desktopPolicy.retiredHooks.directory .. "/gtk-theme"), "rb"))
        assert(not io.open(desktopPaths:resolve("state", "omarchy/toggles/screensaver-off"), "rb"))
        local before = process:run("digest", {home}) .. process:run("digest", {desktopPaths:resolve("data", desktopPolicy.launcher.destination)})
        assert(desktop():apply())
        assert(before == process:run("digest", {home}) .. process:run("digest", {desktopPaths:resolve("data", desktopPolicy.launcher.destination)}))
    end)
    process:run("removeDirectory", {desktopDirectory})
    assert(os.remove(paths:resolve("data", "applications")))
    assert(os.remove(paths:resolve("data", ""):gsub("/$", "")))
    assert(os.remove(paths:resolve("config", ""):gsub("/$", "")))
    assert(os.remove(directory .. "/.local")); assert(os.remove(directory))
    suite:test("unknown application cannot call a native backend", function()
        local backend = {run=function() error("backend_called") end}
        suite:reject(function() Settings.new(root, backend, registry):apply("missing") end)
    end)
    suite:test("native settings errors stop the Lua component", function()
        local count = 0
        local backend = {run=function() count = count + 1; error("native_failure") end}
        suite:reject(function() Settings.new(root, backend, registry):apply("nautilus") end)
        assert(count == 1)
    end)
elseif arg[2] == "publisher" then
    local directory = process:run("temporary", {"-d"}):gsub("\n$", "")
    local destination = directory .. "/hyprland.lua"
    local publisher = Publisher.new(process)
    process:run("permissions", {"700", directory})
    suite:test("publisher creates complete configuration without widening its parent", function()
        assert(publisher:publish(destination, "first", "600"))
        assert(File.read(destination) == "first")
        assert(tonumber(process:run("fileMode", {directory}), 16) & 0x1FF == tonumber("700", 8))
    end)
    suite:test("publisher preserves the previous complete content", function()
        publisher:publish(destination, "second", "600")
        assert(File.read(destination .. ".bak") == "first")
    end)
    suite:test("repeated publication keeps only one backup", function()
        publisher:publish(destination, "third", "600")
        assert(File.read(destination .. ".bak") == "second" and not io.open(destination .. ".bak.bak"))
    end)
    suite:test("unchanged publication does not replace the file", function()
        assert(publisher:publish(destination, "third", "600") == false)
        assert(File.read(destination .. ".bak") == "second")
    end)
    suite:test("failed validation preserves configuration and backup", function()
        suite:reject(function() publisher:publish(destination, "invalid", "600", function() error("validation_failed") end) end)
        assert(File.read(destination) == "third" and File.read(destination .. ".bak") == "second")
    end)
    suite:test("repeated atomic replacements remain complete", function()
        for index = 1, 100 do
            local content = tostring(index):rep(8192)
            publisher:publish(destination, content, "600")
            assert(File.read(destination) == content)
        end
    end)
    suite:test("concurrent readers never see missing or partial Lua configurations", function()
        local first, second = ("a"):rep(131072), ("b"):rep(131072)
        publisher:publish(destination, first, "600")
        local done = directory .. "/complete"
        local words = {"/usr/bin/lua", root .. "/tests/lua/concurrent_writer.lua", root, destination, done}
        for index, word in ipairs(words) do words[index] = Process.quote(word) end
        local writer = assert(io.popen(table.concat(words, " "), "r"))
        local observations = 0
        local ok, failure = pcall(function()
            local deadline = os.time() + 30
            while true do
                local value = File.read(destination)
                assert(value == first or value == second, "partial_configuration")
                observations = observations + 1
                local signal = io.open(done, "r")
                if signal then assert(signal:close()); break end
                assert(os.time() < deadline, "writer_timeout")
            end
        end)
        local success = writer:close()
        assert(ok, failure)
        assert(success and observations > 0 and File.read(done) == "complete")
        assert(os.remove(done))
    end)
    assert(os.remove(destination)); assert(os.remove(destination .. ".bak")); assert(os.remove(directory))
else
    suite:test("boot retains encryption resume security and root arguments", function()
        local output = menu:render(menu:read(source("/kernel.efi")), "ABCD-1234", policy)
        for _, value in ipairs({"cryptdevice=fixture", "resume_offset=123", "lsm=apparmor", "rootflags=subvol=@"}) do assert(output:find(value, 1, true)) end
    end)
    suite:test("snapshot command lines remain distinct", function()
        local entries = menu:read(source("/kernel.efi", "rootflags=subvol=@") .. "//snapshot\nprotocol: efi\npath: boot():/snapshot.efi\ncmdline: rootflags=subvol=@/.snapshots/24/snapshot\n")
        assert(#entries == 2 and entries[1].cmdline ~= entries[2].cmdline)
    end)
    suite:test("duplicate boot fields are rejected", function() suite:reject(function() menu:read(source("/kernel.efi") .. "path: boot():/other.efi\n") end) end)
    suite:test("parent paths cannot escape the ESP", function() suite:reject(function() menu:read(source("/../kernel.efi")) end) end)
    suite:test("unsupported boot protocols are rejected", function() suite:reject(function() menu:read(source("/kernel.efi"):gsub("protocol: efi", "protocol: linux")) end) end)
    suite:test("invalid digest lengths are rejected", function() suite:reject(function() menu:read(source("/kernel.efi#abc")) end) end)
    suite:test("GRUB strings reject line injection", function() suite:reject(function() Menu.quote("line\nreboot") end) end)
    suite:test("kernel quoted arguments survive unchanged", function()
        local command = 'root=/dev/mapper/root parameter="two words"'
        assert(menu:render(menu:read(source("/kernel.efi", command)), "ABCD-1234", policy):find(command, 1, true))
    end)
    suite:test("GRUB quote escapes apostrophes", function() assert(Menu.quote("a'b") == "'a'\\''b'") end)
    suite:test("fractional menu indexes are rejected", function()
        local altered = {}; for key, value in pairs(policy) do altered[key] = value end
        altered.default = 0.5
        suite:reject(function() menu:render(menu:read(source("/kernel.efi")), "ABCD-1234", altered) end)
    end)
    local directory = process:run("temporary", {"-d"}):gsub("\n$", "")
    local image = directory .. "/kernel.efi"
    local binary = "MZ" .. string.rep("\0", 58) .. string.pack("<I4", 64) .. "PE\0\0" .. string.rep("\0", 64)
    local function write(content)
        local file = assert(io.open(image, "wb")); assert(file:write(content)); assert(file:close())
    end
    write(binary)
    local digest = process:run("digest", {image}):match("^(%x+)")
    suite:test("real PE image and BLAKE digest validate", function()
        assert(#menu:verify(menu:read(source("/kernel.efi#" .. digest)), directory) == 1)
    end)
    suite:test("integrity drift is rejected with valid PE headers", function()
        write(binary .. "changed")
        suite:reject(function() menu:verify(menu:read(source("/kernel.efi#" .. digest)), directory) end)
    end)
    suite:test("non PE images are rejected", function()
        write("invalid")
        suite:reject(function() menu:verify(menu:read(source("/kernel.efi")), directory) end)
    end)
    suite:test("missing EFI images cannot render a verified menu", function()
        suite:reject(function() menu:verify(menu:read(source("/missing.efi")), directory) end)
    end)
    suite:test("empty inventory is rejected", function() suite:reject(function() menu:verify({}, directory) end) end)
    assert(os.remove(image)); assert(os.remove(directory))
end
suite:finish()
