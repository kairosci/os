local File = require("core.file")
local Json = require("core.json")
local Process = require("core.process")
local Catalog = require("core.catalog")
local Menu = require("component.boot.menu")
local Publisher = require("core.publisher")
local Application = {}
Application.__index = Application

function Application.new(root)
    local layout = File.json(root .. "/data/core/layout.json")
    return setmetatable({
        root=root,
        layout=layout,
        process=Process.new(File.json(root .. "/" .. layout.commands)),
        catalog=Catalog.new(File.json(root .. "/" .. layout.locale), root .. "/" .. layout.catalog)
    }, Application)
end

function Application:apply(names, single)
    local Settings = require("component.application.settings")
    local Paths = require("core.paths")
    local Configuration = require("component.application.configuration")
    local registry = File.json(self.root .. "/" .. self.layout.applications)
    local settings = Settings.new(self.root, self.process, registry)
    local paths = Paths.new(File.json(self.root .. "/" .. self.layout.paths))
    local publisher = Publisher.new(self.process)
    local configuration = Configuration.new(self.root, paths, publisher, registry)
    local files = require("component.application.files").new(self.root, paths, publisher, self.process, registry)
    local applications = {}
    if single or (names and names ~= "") then applications[1] = assert(names, "application_required")
    else for name in pairs(registry) do applications[#applications + 1] = name end; table.sort(applications) end
    for _, name in ipairs(applications) do
        local policy = assert(registry[name], "unknown_application")
        local application
        if policy.kind == "neovim" then application = require("component.editor.neovim.installer").new(self.root, paths, publisher, self.process, File.json(self.root .. "/" .. policy.policy), self.catalog):install()
        elseif policy.kind == "terminal" then application = require("component.terminal.installer").new(self.root, paths, publisher, self.process, File.json(self.root .. "/" .. policy.policy)):install()
        elseif policy.kind == "plugin" then application = require("component.media.plugin").new(self.root, paths, publisher, self.process, registry):apply(name)
        elseif policy.kind == "settings" then application = settings:apply(name)
        elseif policy.kind == "ini" then application = configuration:apply(name)
        elseif policy.kind == "native-panel" then application = require("component.application.panel").new(self.root, paths, publisher, registry):apply(name)
        elseif policy.kind == "retirement" or policy.kind == "json-provider" then application = require("component.application.retirement").new(paths, publisher, self.process, registry):apply(name)
        elseif policy.kind == "file" or policy.kind == "launcher" then application = files:apply(name)
        elseif policy.kind == "desktop" then application = require("component.application.desktop").new(self.root, paths, publisher, self.process, self.catalog, File.json(self.root .. "/" .. policy.policy)):apply()
        else error("unknown_application_kind") end
        io.write(self.catalog:text("gui.install_done", application), "\n")
    end
end

function Application:publish_grub(menu)
    assert(self.process:run("identity"):match("^0%s*$"), "root_required")
    local policy = File.json(self.root .. "/" .. self.layout.bootPolicy)
    local files = File.json(self.root .. "/" .. self.layout.bootFiles)
    local entries = menu:verify(menu:read(File.read(policy.esp .. "/" .. files.inventory)), policy.esp)
    local uuid = self.process:run("mountUuid", {policy.esp}):gsub("\n$", "")
    Publisher.new(self.process):publish(policy.esp .. "/" .. files.menu, menu:render(entries, uuid, policy.menu), files.mode, function(path)
        self.process:run("validateGrub", {path})
    end)
end

function Application:run(arguments)
    local mode, config, esp, uuid, policy_path = table.unpack(arguments)
    if mode and mode:match("^project-") then
        local interface = require("component.project.interface").new(self.root, self.process, self.catalog,
            File.json(self.root .. "/data/component/project/policy.json"), File.json(self.root .. "/" .. self.layout.locale))
        local values = {}; for index = 2, #arguments do values[#values + 1] = arguments[index] end
        if mode == "project-help" then assert(#values == 0, "invalid_project_arguments"); return interface:help() end
        if mode == "project-languages" then assert(#values == 0, "invalid_project_arguments"); return interface:languages() end
        if mode == "project-locale-status" then assert(#values == 0, "invalid_project_arguments"); return interface:locale_status() end
        return interface:launch(mode, values)
    end
    if mode == "repository-pre-push" or mode == "repository-policy-check" or mode == "repository-policy-apply" then
        local policy = require("component.repository.policy").new(self.root, self.process, self.catalog, File.json(self.root .. "/data/repository/policy.json"))
        if mode == "repository-pre-push" then assert(config == nil, "invalid_push_guard_arguments"); return policy:pre_push() end
        assert(#arguments <= 2, "invalid_repository_policy_arguments")
        return policy:reconcile(config, mode == "repository-policy-apply")
    end
    if mode == "terminal-helper" then
        local values = {}; for index = 2, #arguments do values[#values + 1] = arguments[index] end
        return require("component.terminal.helper").new(self.root, self.catalog, File.json(self.root .. "/data/component/terminal/policy.json")):run(values)
    end
    if mode == "terminal-theme" then
        assert(config == nil, "invalid_terminal_theme_arguments")
        local paths = require("core.paths").new(File.json(self.root .. "/" .. self.layout.paths))
        return require("component.terminal.theme").new(self.root, paths, Publisher.new(self.process), File.json(self.root .. "/data/component/terminal/policy.json")):apply()
    end
    if mode == "arch-report" or mode == "arch-check" then
        assert(config == nil, "invalid_arch_assessment_arguments")
        local policy = File.json(self.root .. "/data/component/platform/parity.json")
        local report = require("component.platform.assessment").new(self.root, self.process, policy):report()
        io.write(Json.encode(report), "\n")
        if mode == "arch-check" then assert(report.readyToRemoveRuntime and report.readyToRemoveRepository, "arch_parity_unverified") end
        return
    end
    if mode == "documentation-report" or mode == "verify-documentation" then
        assert(config == nil, "invalid_documentation_arguments")
        local report = require("component.documentation.catalog").new(self.root, self.process, File.json(self.root .. "/data/component/documentation/policy.json")):report()
        io.write(Json.encode(report), "\n")
        if mode == "verify-documentation" then assert(report.complete, "documentation_incomplete") end
        return
    end
    if mode == "boot-assessment" or mode == "boot-trial-select" then
        assert(config == nil, "invalid_boot_assessment_arguments")
        local boot = File.json(self.root .. "/" .. self.layout.bootPolicy)
        local assessment = require("component.boot.assessment").new(self.root, self.process, File.json(self.root .. "/data/component/boot/assessment.json"), boot, File.json(self.root .. "/" .. self.layout.bootFormat))
        io.write(Json.encode(assessment:record()), "\n")
        if mode == "boot-trial-select" then
            self.process:run("validateGrub", {boot.esp .. "/" .. boot.grubConfiguration})
            local entry = require("component.boot.trial").new(self.process, boot):select()
            io.write(self.catalog:text("bootloader.trial_selected", entry), "\n")
        end
        return
    end
    if mode == "install-cli" or mode == "install-cli-user" then
        assert(config == nil, "invalid_cli_install_arguments")
        local paths = require("core.paths").new(File.json(self.root .. "/" .. self.layout.paths))
        local installer = require("component.cli.installer").new(self.root, self.process, File.json(self.root .. "/data/component/cli/installation.json"), paths)
        if mode == "install-cli" then
            installer:system()
            io.write(self.catalog:text("os.changelog_installed", installer.policy.systemChangelog), "\n")
            io.write(self.catalog:text("os.cli_installed", installer.policy.systemExecutable), "\n")
            return
        end
        return installer:user()
    end
    if mode == "cli" then
        local values = {}; for index = 2, #arguments do values[#values + 1] = arguments[index] end
        return require("component.cli.application").new(self.root, self.process, self.catalog, File.json(self.root .. "/data/component/cli/policy.json")):run(values)
    end
    if mode == "boot-appearance-diagnostics" then
        assert(self.process:run("identity"):match("^0%s*$"), "root_required")
        local policy = File.json(self.root .. "/" .. self.layout.bootAppearance)
        io.write(File.read(policy.lastAttempt), "\n")
        return
    end
    if mode == "grub-repair" then
        local policy = File.json(self.root .. "/" .. self.layout.bootCandidate)
        local boot = File.json(self.root .. "/" .. self.layout.bootPolicy)
        io.write(Json.encode(require("component.boot.candidate").new(self.process, policy, boot):repair()), "\n")
        return
    end
    if mode == "boot-diagnostics" then
        assert(self.process:run("identity"):match("^0%s*$"), "root_required")
        local policy = File.json(self.root .. "/" .. self.layout.bootPolicy)
        local image = policy.esp .. "/EFI/" .. policy.candidateId .. "/" .. policy.candidateFile
        local configuration = policy.esp .. "/" .. policy.grubConfiguration
        self.process:run("validateGrub", {configuration})
        local prefixes = Json.array({})
        for line in self.process:run("bootImageStrings", {image}):gmatch("[^\r\n]+") do
            if line:find("/grub", 1, true) then prefixes[#prefixes + 1] = line end
        end
        local files = File.json(self.root .. "/" .. self.layout.bootFiles)
        local inventory = require("component.boot.menu").new(self.process, File.json(self.root .. "/" .. self.layout.bootFormat)):read(File.read(policy.esp .. "/" .. files.inventory))
        for _, entry in ipairs(inventory) do entry.observedDigest = self.process:run("digest", {policy.esp .. entry.path}):match("^(%x+)") end
        io.write(Json.encode({inventory=inventory, firmware=self.process:run("bootFirmware"), imageSections=self.process:run("bootCandidateInspect", {image}), prefixes=prefixes, configuration=File.read(configuration), espUuid=self.process:run("mountUuid", {policy.esp}):gsub("\n$", ""), hardwareBootVerified=false}), "\n")
        return
    end
    if mode == "boot-appearance" then
        assert(config == nil, "invalid_boot_appearance_arguments")
        local policy = File.json(self.root .. "/" .. self.layout.bootAppearance)
        local result = require("component.boot.appearance").new(self.root, self.process, policy):apply()
        io.write(Json.encode(result), "\n")
        return
    end
    if mode == "settings-snapshot" or mode == "settings-set" or mode == "settings-write" or mode == "settings-set-session" or mode == "settings-write-session" or mode == "install-settings" then
        local Paths = require("core.paths")
        local paths = Paths.new(File.json(self.root .. "/" .. self.layout.paths))
        local policy = File.json(self.root .. "/" .. self.layout.settings)
        local model = require("component.settings.model").new(self.root, self.process, paths, Publisher.new(self.process), policy, self.catalog)
        if mode == "install-settings" then return require("component.settings.installer").new(model):apply() end
        if mode == "settings-set" or mode == "settings-set-session" then
            assert(config and esp and uuid == nil, "invalid_settings_arguments")
            local lock = paths:resolve("state", policy.lock)
            self.process:run("directory", {assert(lock:match("^(.*)/[^/]+$"))})
            io.write(self.process:run("settingsSerialized", {lock, self.root .. "/script/os-lua", mode == "settings-set-session" and "settings-write-session" or "settings-write", config, esp}))
            return
        end
        local result
        if mode == "settings-write-session" then
            assert(config and esp and uuid == nil, "invalid_settings_arguments")
            require("component.settings.session").new(paths, Publisher.new(self.process), policy):write(config, Json.decode(esp))
            result = model:snapshot()
        elseif mode == "settings-write" then
            assert(config and esp and uuid == nil, "invalid_settings_arguments")
            result = model:write(config, Json.decode(esp))
        else result = model:snapshot() end
        io.write(Json.encode(result), "\n")
        return
    end
    if mode == "secure-home" then
        assert(config and esp == nil, "invalid_home_arguments")
        return require("core.paths").new(File.json(self.root .. "/" .. self.layout.paths)):protectHome(self.process, config)
    end
    if mode == "apply-build-environment" then
        assert((config == nil or config == "--defer") and esp == nil, "invalid_environment_arguments")
        local Paths = require("core.paths")
        return require("component.performance.environment").new(self.process, Paths.new(File.json(self.root .. "/" .. self.layout.paths)), Publisher.new(self.process), File.json(self.root .. "/" .. self.layout.performance)):apply(config == "--defer")
    end
    if mode == "render-zed-settings" then
        local performance = require("component.performance.editor").new(self.root, self.process, File.json(self.root .. "/" .. self.layout.performance))
        io.write(Json.encode(performance:render(config)), "\n")
        return
    end
    if mode == "migration-report" or mode == "verify-full-lua" then
        local inventory = require("component.migration.inventory").new(self.root, self.process, File.json(self.root .. "/" .. self.layout.migration))
        local report = inventory:report()
        io.write(Json.encode(report), "\n")
        if mode == "verify-full-lua" then assert(report.complete, "migration_incomplete") end
        return
    end
    if mode == "render-wallpaper" or mode == "install-wallpapers" then
        local Renderer = require("component.wallpaper.renderer")
        local Paths = require("core.paths")
        local paths = Paths.new(File.json(self.root .. "/" .. self.layout.paths))
        local policy = File.json(self.root .. "/" .. self.layout.wallpaper)
        local renderer = Renderer.new(self.root, self.process, paths, policy, self.catalog)
        if mode == "render-wallpaper" then return renderer:render(config) end
        return require("component.wallpaper.installer").new(renderer):apply()
    end
    if mode == "restore-native" then
        assert(config == nil, "invalid_desktop_arguments")
        local paths = require("core.paths").new(File.json(self.root .. "/" .. self.layout.paths))
        local registry = File.json(self.root .. "/" .. self.layout.applications)
        local policy = assert(registry.desktop, "unknown_application")
        require("component.application.desktop").new(self.root, paths, Publisher.new(self.process), self.process, self.catalog, File.json(self.root .. "/" .. policy.policy)):restore()
        return
    end
    if mode == "apply-settings" or mode == "apply-applications" then return self:apply(config, mode == "apply-settings") end
    local menu = Menu.new(self.process, File.json(self.root .. "/" .. self.layout.bootFormat))
    if mode == "publish-grub" then return self:publish_grub(menu) end
    assert((mode == "report" or mode == "grub") and config and esp and (mode ~= "grub" or uuid), "invalid_arguments")
    local entries = menu:verify(menu:read(File.read(config)), esp)
    if mode == "report" then io.write(Json.encode({entries=entries, trialBootVerified=false}), "\n")
    else io.write(menu:render(entries, uuid, File.json(policy_path or self.root .. "/" .. self.layout.bootPolicy).menu)) end
end

function Application:report(failure)
    io.stderr:write(self.catalog:text("runtime.operation_failed", tostring(failure)), "\n")
end

return Application
