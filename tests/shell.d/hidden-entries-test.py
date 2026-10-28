"""Check desktop-entry visibility and precedence for the application library."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from base_test import ROOT, test_environment

SCANNER = ROOT / "src/arch/shell/services/hidden-entries.py"


class HiddenEntriesTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="hidden-entries-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.home = self.scratch / "home"
    self.system = self.scratch / "system"
    self.vendor = self.scratch / "ven[dor]*"
    self.home.mkdir()
    self.system.mkdir()
    self.vendor.mkdir()
    self.environment = test_environment(
      HOME=self.home,
      XDG_DATA_DIRS=f"{self.system}:{self.vendor}",
      LC_ALL="C",
    )

  def entry(self, path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"[Desktop Entry]\n{contents}\n", encoding="utf-8")

  def scan(self, *, cwd: Path | None = None) -> list[str]:
    result = subprocess.run(
      [str(SCANNER), "Hyprland:os"],
      check=False,
      capture_output=True,
      text=True,
      env=self.environment,
      cwd=cwd,
    )
    self.assertEqual(result.returncode, 0, result.stderr)
    return result.stdout.splitlines()

  def test_hidden_ids_preserve_precedence_and_desktop_visibility(self) -> None:
    user = self.home / ".local/share/applications"
    system = self.system / "applications"
    vendor = self.vendor / "applications"
    self.entry(user / "override.desktop", "Name=Visible override")
    self.entry(user / "kde-foo.desktop", "Name=Visible nested override")
    self.entry(system / "kde/foo.desktop", "Hidden=true")
    self.entry(system / "override.desktop", "Hidden=true")
    self.entry(user / "user-hidden.desktop", "Hidden=true")
    self.entry(system / "user-hidden.desktop", "Name=Visible system entry")
    self.entry(system / "nested/space name.desktop", "NoDisplay=true")
    self.entry(system / "nested/deeper/app.desktop", "OnlyShowIn=GNOME;")
    self.entry(system / "visible.desktop", "OnlyShowIn=Hyprland;GNOME;")
    self.entry(system / "not-hyprland.desktop", "NotShowIn=Hyprland;")
    self.entry(system / "other-section.desktop", "Name=Visible\n[Desktop Action Hidden]\nHidden=true")
    self.entry(system / 'quote" app.desktop', "NoDisplay=true")
    self.entry(vendor / "vendor.desktop", "Hidden=true")
    self.entry(self.home / ".nix-profile/share/applications/nix.desktop", "NoDisplay=true")

    self.assertEqual(
      self.scan(),
      [
        "user-hidden",
        "nested-deeper-app",
        "nested-space name",
        "not-hyprland",
        'quote" app',
        "vendor",
        "nix",
      ],
    )

  def test_empty_data_directory_does_not_scan_a_relative_applications_path(self) -> None:
    self.environment["XDG_DATA_DIRS"] = f":{self.system}"
    relative = self.scratch / "applications/relative.desktop"
    self.entry(relative, "Hidden=true")
    output = self.scan(cwd=self.scratch)
    self.assertNotIn("relative", output)

  def test_malformed_configuration_fails_at_the_command_boundary(self) -> None:
    invalid_root = self.scratch / "invalid"
    config_directory = invalid_root / "data/shell"
    config_directory.mkdir(parents=True)
    (config_directory / "hidden-entries.yml").write_text("paths: [\n", encoding="utf-8")
    result = subprocess.run(
      [str(SCANNER)],
      check=False,
      capture_output=True,
      text=True,
      env=test_environment(AP=invalid_root),
    )
    self.assertEqual(result.returncode, 78)
    self.assertIn("Could not load hidden-entries configuration", result.stderr)
    self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
  unittest.main()
