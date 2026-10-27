"""Verify floating workspace behavior and its retired package are absent."""

from __future__ import annotations

import os
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1792938567.py"


class TilingWorkspaceTest(unittest.TestCase):
  def test_window_configuration_has_no_floating_workspace_behavior(self) -> None:
    paths = [
      ROOT / "default/hypr",
      ROOT / "src/cli/arch-hyprland-workspace-layout-current",
      ROOT / "src/cli/arch-hyprland-workspace-layout-default",
      ROOT / "src/cli/arch-hyprland-workspace-layout-toggle",
    ]
    search = subprocess.run(
      ["rg", "-n", r"float\s*=\s*true|pin\s*=\s*true|floating-window|arch-floating-workspace", *map(str, paths)],
      check=False,
      capture_output=True,
      text=True,
    )
    self.assertEqual(search.returncode, 1, search.stdout)
    tiling_bindings = (ROOT / "default/hypr/bindings/tiling.lua").read_text(encoding="utf-8")
    self.assertNotIn("SUPER + T.*floating", tiling_bindings)
    self.assertNotIn("SUPER + O.*pop", tiling_bindings)
    self.assertFalse((ROOT / "src/cli/arch-hyprland-window-pop").exists())
    module = (ROOT / "modules/desktop/commands/hyprland/module.toml").read_text(encoding="utf-8")
    self.assertNotIn("arch-hyprland-window-pop", module)

  def test_retired_titlebar_package_is_removed(self) -> None:
    with tempfile.TemporaryDirectory(prefix="tiling-titlebar-migration-") as temporary:
      scratch = Path(temporary)
      bin_dir = scratch / "bin"
      bin_dir.mkdir()
      log = scratch / "calls"
      stub = bin_dir / "command"
      stub.write_text(
        "#!/usr/bin/python3 -I\n"
        "import json, os, pathlib, sys\n"
        "name = pathlib.Path(sys.argv[0]).name\n"
        "with open(os.environ['MIGRATION_LOG'], 'a', encoding='utf-8') as stream:\n"
        "  stream.write(json.dumps([name, *sys.argv[1:]]) + '\\n')\n"
        "if name == 'arch-i18n': print(sys.argv[1])\n",
        encoding="utf-8",
      )
      stub.chmod(0o755)
      for name in ("arch-i18n", "arch-pkg-drop"):
        (bin_dir / name).symlink_to(stub)
      environment = test_environment(
        MIGRATION_LOG=log,
        PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
      )
      result = subprocess.run(
        ["/usr/bin/python3", "-I", str(MIGRATION)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
      )
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(result.stdout, "migration.removeWorkspaceTitlebars\n")
      calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
      self.assertEqual(
        calls,
        [
          ["arch-i18n", "migration.removeWorkspaceTitlebars"],
          ["arch-pkg-drop", "arch-hyprland-titlebars"],
        ],
      )


if __name__ == "__main__":
  unittest.main()
