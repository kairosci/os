#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
require_command python3

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

python3 "$ROOT/scripts/modules.py" validate
python3 "$ROOT/scripts/modules.py" graph >"$stage/graph.json"
python3 - "$stage/graph.json" "$ROOT/src/cli" <<'PY'
import json
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
command_modules = {
    module_id: module for module_id, module in modules.items()
    if module_id.startswith("desktop.commands.")
}
command_sources = {
    source for module_id, module in modules.items()
    if module_id.startswith("desktop.commands")
    for source in module["sources"]
}
cli_files = {
    f"src/cli/{path.name}" for path in cli_directory.iterdir() if path.is_file()
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
assert stages <= modules.keys(), stages - modules.keys()
assert settings <= modules.keys(), settings - modules.keys()
assert set(command_modules) == expected_groups, (set(command_modules) ^ expected_groups)
assert command_sources == cli_files, (cli_files - command_sources, command_sources - cli_files)
for module_id in stages:
    module = modules[module_id]
    assert module["package"] == "arch", module_id
    assert module["requires"] == ["system.installation"], (module_id, module["requires"])
for module_id in settings:
    module = modules[module_id]
    assert module["package"] == "arch-settings", module_id
    assert module["requires"] == ["system.settings"], (module_id, module["requires"])
for module_id in command_modules:
    module = command_modules[module_id]
    assert module["package"] == "arch", module_id
    assert module["requires"] == ["desktop.commands"], (module_id, module["requires"])
    assert len(module["sources"]) == len(module["outputs"]), module_id
    for source, output in zip(module["sources"], module["outputs"]):
        assert output == [source, f"usr/share/arch/src/cli/{Path(source).name}"], (module_id, source, output)
assert modules["desktop.commands"]["sources"] == ["src/cli/archctl"]
PY
pass "installation stages are declared as submodules of the shared installer contract"
pass "settings, applications, and pre-install branding have independent module ownership"
pass "CLI capabilities are owned by explicit command modules"

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
  diff -r --no-dereference "$ROOT/$path" "$stage/settings/usr/share/arch/$path"
done
diff -r --no-dereference --exclude=skel "$ROOT/etc" "$stage/settings/etc"
for path in \
  etc/skel/.config/arch/branding/screensaver.txt \
  etc/skel/.config/arch/branding/about.txt \
  usr/share/icons/hicolor/256x256/apps/arch.png; do
  [[ -f $stage/settings/$path ]] || fail "settings module assembles $path"
done
pass "the settings package assembles user configuration and defaults from their declared modules"
