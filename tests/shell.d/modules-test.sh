#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
require_command python3

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

python3 "$ROOT/scripts/modules.py" validate
python3 "$ROOT/scripts/modules.py" graph >"$stage/graph.json"
python3 - "$stage/graph.json" <<'PY'
import json
import sys

modules = {module["id"]: module for module in json.load(open(sys.argv[1]))}
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
assert stages <= modules.keys(), stages - modules.keys()
assert settings <= modules.keys(), settings - modules.keys()
for module_id in stages:
    module = modules[module_id]
    assert module["package"] == "arch", module_id
    assert module["requires"] == ["system.installation"], (module_id, module["requires"])
for module_id in settings:
    module = modules[module_id]
    assert module["package"] == "arch-settings", module_id
    assert module["requires"] == ["system.settings"], (module_id, module["requires"])
PY
pass "installation stages are declared as submodules of the shared installer contract"
pass "settings, applications, and pre-install branding have independent module ownership"

python3 "$ROOT/scripts/modules.py" assemble --package arch --destination "$stage/arch"
for path in installer migrations src/cli; do
  diff -r --no-dereference "$ROOT/$path" "$stage/arch/usr/share/arch/$path"
done
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
