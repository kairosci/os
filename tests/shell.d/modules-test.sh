#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
require_command python3

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

python3 "$ROOT/scripts/modules.py" validate
python3 "$ROOT/scripts/modules.py" graph >"$stage/graph.json"
python3 - "$stage/graph.json" "$ROOT/src/cli" "$ROOT/default" "$ROOT/etc" "$ROOT/config" <<'PY'
import json
import re
import sys
from pathlib import Path

modules = {module["id"]: module for module in json.load(open(sys.argv[1]))}
cli_directory = Path(sys.argv[2])
stages = {
    "system.installation.boot",
    "system.installation.config",
    "system.installation.hardware",
    "system.installation.login",
    "system.installation.packages",
    "system.installation.post-install",
    "system.installation.provisioning",
    "system.installation.user",
}
settings = {
    "system.settings.defaults",
    "system.settings.preinstall-tools",
    "system.settings.system-files",
    "desktop.applications",
    "desktop.branding.preinstall",
}
runtime_data = {
    "system.runtime-data.libalpm-hooks",
}
default_modules = {
    module_id: module for module_id, module in modules.items()
    if module_id.startswith("system.settings.defaults.")
}
system_file_modules = {
    module_id: module for module_id, module in modules.items()
    if module_id.startswith("system.settings.system-files.")
}
command_modules = {
    module_id: module for module_id, module in modules.items()
    if module_id.startswith("desktop.commands.")
}
command_sources = {
    source for module_id, module in modules.items()
    if module_id.startswith("desktop.commands")
    for source in module["sources"]
    if source.startswith("src/cli/")
}
cli_files = {
    f"src/cli/{path.name}" for path in cli_directory.iterdir() if path.is_file()
}
python_cli_files = {
    f"src/python/{path.relative_to(cli_directory.parent / 'python').as_posix()}"
    for path in (cli_directory.parent / "python/cli").rglob("*.py")
    if path.name != "__init__.py"
}
cli_files -= {
    "src/cli/arch-debug",
    "src/cli/arch-debug-idle",
    "src/cli/arch-upload-log",
}
expected_groups = {
    f"desktop.commands.{source.removeprefix('src/cli/arch-').split('-', 1)[0]}"
    for source in cli_files
    if source != "src/cli/archctl"
}
default_roots = Path(sys.argv[3])
etc_roots = Path(sys.argv[4])
config_roots = Path(sys.argv[5])
expected_default_sources = {
    f"default/{path.name}" for path in default_roots.iterdir()
}
declared_default_sources = {
    source for module_id, module in modules.items()
    if module_id == "system.settings.defaults" or module_id in default_modules
    for source in module["sources"]
}
expected_etc_sources = {f"etc/{path.name}" for path in etc_roots.iterdir()}
declared_etc_sources = {
    source for module_id, module in modules.items()
    if module_id == "system.settings.system-files" or module_id in system_file_modules
    for source in module["sources"]
}
config_modules = {
    module_id: module for module_id, module in modules.items()
    if module_id.startswith("system.settings.user-configs.")
}
expected_config_sources = {
    f"config/{path.name}" for path in config_roots.iterdir() if path.is_dir()
}
declared_config_sources = {
    source for module in config_modules.values() for source in module["sources"]
}
root_config_files = {
    f"config/{path.name}" for path in config_roots.iterdir() if path.is_file()
}
declared_root_config_files = set(modules["system.settings"]["sources"])
assert stages <= modules.keys(), stages - modules.keys()
assert settings <= modules.keys(), settings - modules.keys()
assert runtime_data <= modules.keys(), runtime_data - modules.keys()
assert set(command_modules) == expected_groups, (set(command_modules) ^ expected_groups)
expected_command_sources = cli_files | python_cli_files
assert command_sources == expected_command_sources, (expected_command_sources - command_sources, command_sources - expected_command_sources)
assert declared_default_sources == expected_default_sources, (
    expected_default_sources - declared_default_sources,
    declared_default_sources - expected_default_sources,
)
assert declared_etc_sources == expected_etc_sources, (
    expected_etc_sources - declared_etc_sources,
    declared_etc_sources - expected_etc_sources,
)
assert declared_config_sources == expected_config_sources, (
    expected_config_sources - declared_config_sources,
    declared_config_sources - expected_config_sources,
)
assert declared_root_config_files == root_config_files, (
    root_config_files - declared_root_config_files,
    declared_root_config_files - root_config_files,
)
for module_id, module in default_modules.items():
    assert module["package"] == "arch-settings", module_id
    assert module["requires"] == ["system.settings.defaults"], (module_id, module["requires"])
    assert len(module["sources"]) == 1 and len(module["sources"][0].split('/')) == 2, module_id
    expected_id = f"system.settings.defaults.{Path(module['sources'][0]).name.replace('.', '-')}"
    assert module_id == expected_id, (module_id, expected_id)
for module_id, module in system_file_modules.items():
    assert module["package"] == "arch-settings", module_id
    assert module["requires"] == ["system.settings.system-files"], (module_id, module["requires"])
    assert len(module["sources"]) == 1 and len(module["sources"][0].split('/')) == 2, module_id
    slug = re.sub(r"[^a-z0-9]+", "-", Path(module["sources"][0]).name.lower()).strip("-")
    expected_id = f"system.settings.system-files.{slug}"
    assert module_id == expected_id, (module_id, expected_id)
for module_id, module in config_modules.items():
    assert module["package"] == "arch-settings", module_id
    assert module["requires"] == ["system.settings"], (module_id, module["requires"])
    assert len(module["sources"]) == len(module["outputs"]) == 1, module_id
    source = module["sources"][0]
    slug = Path(source).name.lower().replace("_", "-")
    assert module_id == f"system.settings.user-configs.{slug}", (module_id, source)
    assert module["outputs"][0] == [source, f"usr/share/arch/{source}"], (module_id, module["outputs"])
for module_id in stages:
    module = modules[module_id]
    assert module["package"] == "arch", module_id
    assert module["requires"] == ["system.installation"], (module_id, module["requires"])
for module_id in settings:
    module = modules[module_id]
    assert module["package"] == "arch-settings", module_id
    assert module["requires"] == ["system.settings"], (module_id, module["requires"])
assert modules["system.runtime-data"]["package"] == "arch"
assert ["data", "usr/share/arch/data"] in modules["system.runtime-data"]["outputs"]
for module_id in runtime_data:
    module = modules[module_id]
    assert module["package"] == "arch", module_id
    assert module["requires"] == ["system.runtime-data"], (module_id, module["requires"])
for module_id in command_modules:
    module = command_modules[module_id]
    assert module["package"] == "arch", module_id
    assert module["requires"] in (["desktop.commands"], ["desktop.commands", "system.runtime-data"]), (module_id, module["requires"])
    assert len(module["sources"]) == len(module["outputs"]), module_id
    for source, output in zip(module["sources"], module["outputs"]):
        assert output == [source, f"usr/share/arch/{source}"], (module_id, source, output)
assert modules["desktop.commands"]["sources"] == ["src/cli/archctl"]
PY
pass "installation stages are declared as submodules of the shared installer contract"
pass "settings, applications, and pre-install branding have independent module ownership"
pass "CLI capabilities are owned by explicit command modules"
pass "each top-level default configuration has an explicit module owner"
pass "each /etc subsystem has an explicit module owner"
pass "each application configuration tree has an explicit module owner"

python3 - "$ROOT/scripts/modules.py" "$stage/security" <<'PY'
import importlib.util
import sys
from pathlib import Path

script, sandbox = map(Path, sys.argv[1:])
root = sandbox / "repo"
(root / "modules/system/example").mkdir(parents=True)
(root / "payload").mkdir()
(root / "packages/example").mkdir(parents=True)
(root / "packages/example/PKGBUILD").write_text("pkgname=example\n")
manifest = root / "modules/system/example/module.toml"
manifest.write_text(
    'id = "system.example"\ndomain = "system"\npackage = "example"\n'
    'sources = ["payload"]\nrequires = []\n\n'
    '[[output]]\nsource = "payload"\ntarget = "usr/share/example/payload"\n'
)
loader = importlib.util.spec_from_file_location("modules", script)
modules_tool = importlib.util.module_from_spec(loader)
sys.modules[loader.name] = modules_tool
loader.loader.exec_module(modules_tool)
modules_tool.ROOT = root
modules_tool.MODULES = root / "modules"
modules_tool.PACKAGES = root / "packages"
(root / "payload/first").write_text("first")

(root / "packages/example/PKGBUILD").write_text("pkgname=other\n")
_, _, errors = modules_tool.load_modules()
assert any("package directory does not match pkgname" in error for error in errors), errors
(root / "packages/example/PKGBUILD").write_text("pkgname=example\n")

manifest.write_text(manifest.read_text().replace('id = "system.example"', 'id = "system.wrong"'))
_, _, errors = modules_tool.load_modules()
assert any("module id must match its directory" in error for error in errors), errors
manifest.write_text(manifest.read_text().replace('id = "system.wrong"', 'id = "system.example"'))

(root / "packages/second").mkdir(parents=True)
(root / "packages/second/PKGBUILD").write_text("pkgname=second\n")
(root / "payload/second").write_text("second")
(root / "modules/system/second").mkdir()
(root / "modules/system/second/module.toml").write_text(
    'id = "system.second"\ndomain = "system"\npackage = "second"\n'
    'sources = ["payload/second"]\nrequires = []\n\n'
    '[[output]]\nsource = "payload/second"\ntarget = "usr/share/example/payload"\n'
)
_, _, errors = modules_tool.load_modules()
assert any("package output usr/share/example/payload conflicts with a declared output directory" in error for error in errors), errors

outside = sandbox / "outside"
outside.write_text("outside")
(root / "payload/external").symlink_to(outside)
_, _, errors = modules_tool.load_modules()
assert any("source symlink leaves the repository" in error for error in errors), errors

(root / "payload/external").unlink()
(root / "payload/dangling").symlink_to(root / "missing")
_, _, errors = modules_tool.load_modules()
assert any("broken or cyclic symlink" in error for error in errors), errors
PY
pass "module validation rejects source symlinks that escape the repository or have no target"

python3 "$ROOT/scripts/modules.py" assemble --package arch --destination "$stage/arch"
for path in installer migrations; do
  diff -r --no-dereference "$ROOT/$path" "$stage/arch/usr/share/arch/$path"
done
python3 - "$ROOT/src/cli" "$stage/arch/usr/share/arch/src/cli" <<'PY'
import stat
import sys
from pathlib import Path

source, assembled = map(Path, sys.argv[1:])
excluded = {"arch-debug", "arch-debug-idle", "arch-upload-log"}
expected = {path.name for path in source.iterdir() if path.is_file()} - excluded
actual = {path.name for path in assembled.iterdir() if path.is_file() or path.is_symlink()}
assert actual == expected, (expected - actual, actual - expected)
for name in expected:
    original, packaged = source / name, assembled / name
    assert original.read_bytes() == packaged.read_bytes(), name
    assert stat.S_IMODE(original.stat().st_mode) == stat.S_IMODE(packaged.stat().st_mode), name
PY
pass "the runtime package assembles every installer, migration, and CLI source without changing its path"

python3 "$ROOT/scripts/modules.py" assemble --package arch-settings --destination "$stage/settings"
for path in config default; do
  diff -r --no-dereference --exclude=__pycache__ --exclude='*.pyc' --exclude='*.pyo' \
    "$ROOT/$path" "$stage/settings/usr/share/arch/$path"
done
diff -r --no-dereference --exclude=skel "$ROOT/etc" "$stage/settings/etc"
for path in \
  etc/skel/.config/arch/branding/screensaver.txt \
  etc/skel/.config/arch/branding/about.txt \
  usr/share/icons/hicolor/256x256/apps/arch.png; do
  [[ -f $stage/settings/$path ]] || fail "settings module assembles $path"
done

python3 - "$stage/graph.json" "$ROOT" "$stage" <<'PY'
import json
import stat
import sys
from pathlib import Path

graph_path, source_root, stage_root = map(Path, sys.argv[1:])
source_root, stage_root = source_root.resolve(), stage_root.resolve()
package_roots = {
    "arch": stage_root / "arch",
    "arch-settings": stage_root / "settings",
}
expected: dict[str, set[str]] = {name: set() for name in package_roots}

for module in json.loads(graph_path.read_text()):
    package = module["package"]
    for source, target in module["outputs"]:
        source_path = source_root / source
        target_root = package_roots[package]
        if source_path.is_dir() and not source_path.is_symlink():
            entries = (entry for entry in source_path.rglob("*") if "__pycache__" not in entry.parts and entry.suffix not in {".pyc", ".pyo"})
            for entry in entries:
                if entry.is_dir() and not entry.is_symlink():
                    continue
                relative = entry.relative_to(source_path)
                destination = target_root / target / relative
                original = entry
                expected[package].add(destination.relative_to(target_root).as_posix())
                assert destination.is_symlink() if original.is_symlink() else destination.is_file(), destination
                if original.is_symlink():
                    assert destination.readlink() == original.readlink(), destination
                else:
                    assert destination.read_bytes() == original.read_bytes(), destination
                    assert stat.S_IMODE(destination.stat().st_mode) == stat.S_IMODE(original.stat().st_mode), destination
        else:
            destination = target_root / target
            expected[package].add(destination.relative_to(target_root).as_posix())
            assert destination.is_symlink() if source_path.is_symlink() else destination.is_file(), destination
            if source_path.is_symlink():
                assert destination.readlink() == source_path.readlink(), destination
            else:
                assert destination.read_bytes() == source_path.read_bytes(), destination
                assert stat.S_IMODE(destination.stat().st_mode) == stat.S_IMODE(source_path.stat().st_mode), destination

for package, package_root in package_roots.items():
    actual = {
        entry.relative_to(package_root).as_posix()
        for entry in package_root.rglob("*")
        if "__pycache__" not in entry.parts and entry.suffix not in {".pyc", ".pyo"}
        if entry.is_file() or entry.is_symlink()
    }
    assert actual == expected[package], (package, expected[package] - actual, actual - expected[package])
PY
pass "the settings package assembles user configuration and defaults from their declared modules"
pass "module outputs exactly cover both package trees with matching file contents and modes"
