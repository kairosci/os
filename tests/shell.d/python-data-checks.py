import importlib.util
import json
import os
from pathlib import Path
import sys
import types

ROOT = Path(os.environ["ARCH_PATH"])

# Nautilus imports its extension against GNOME's system Python. Provide the
# lightweight module surface at import time so this test needs no desktop.
gi = types.ModuleType("gi")
gi.require_version = lambda *_args: None
repository = types.ModuleType("gi.repository")
repository.GObject = types.SimpleNamespace(GObject=type("GObject", (), {}))
repository.Gio = types.SimpleNamespace()
repository.Nautilus = types.SimpleNamespace(MenuProvider=type("MenuProvider", (), {}))
gi.repository = repository
sys.modules["gi"] = gi
sys.modules["gi.repository"] = repository


def load(name, path):
  spec = importlib.util.spec_from_file_location(name, path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


transcode = load("arch_transcode", ROOT / "default/nautilus-python/extensions/transcode.py")
assert transcode.SUPPORTED_MIME_PREFIXES == ("image/", "video/")
assert {".jpg", ".mp4"} <= transcode.SUPPORTED_EXTENSIONS
assert ".pdf" not in transcode.SUPPORTED_EXTENSIONS

dropbox = load("arch_dropbox_status", ROOT / "src/arch/shell/plugins/panels/dropbox/status.py")
assert dropbox.PLAN_QUOTAS["basic"] == 2_000_000_000
assert dropbox.PLAN_QUOTAS["professional"] == 3_000_000_000_000

sys.path.insert(0, str(ROOT / "default/input-methods"))
configure = load("arch_input_method_configure", ROOT / "default/input-methods/configure.py")
assert configure.PRESETS["mozc"]["packages"] == ["fcitx5-mozc"]
assert configure.FONT_VARIANTS == ("JP", "KR", "SC", "TC", "HK")
assert configure.CONTROLLER == ["busctl", "--user", "call", "org.fcitx.Fcitx5", "/controller", "org.fcitx.Fcitx.Controller1"]
assert {"ara", "ru", "th"} <= configure.NON_LATIN

for path in ROOT.joinpath("data").rglob("*.json"):
  json.loads(path.read_text(encoding="utf-8"))
sync = load("arch_i18n_sync", ROOT / "scripts/i18n-sync.py")
assert sync.SYNC_SETTINGS["regional_notes"]["pt-BR"] == "Brazilian Portuguese."
assert sync.MODEL == os.environ.get("MUSE_MODEL", sync.SYNC_SETTINGS["model"])
assert configure.SETTINGS["stock_lists"]["TriggerKey"]["0"] == "Super+grave"
print("ok - Python runtime catalogs and tool settings load from the root data directory")
