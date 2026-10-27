"""Verify Omasnap packaging, screenshot routing, and safe legacy migration."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import yaml

from base_test import ROOT, fail_check, pass_check, test_environment


MIGRATION = ROOT / "migrations/1788129995.py"
MIGRATION_CONFIG = yaml.safe_load(
  (ROOT / "data/migrations/1788129995.yml").read_text(encoding="utf-8")
)
SCREENSHOT_COMMAND = ROOT / "src/cli/arch-capture-screenshot"


def write_stub(directory: Path, name: str, body: str) -> None:
  path = directory / name
  path.write_text(f"#!/bin/bash\nset -euo pipefail\n{body}", encoding="utf-8")
  path.chmod(0o755)


def run(command: list[str], environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
  return subprocess.run(command, env=environment, check=False, capture_output=True, text=True)


def main() -> None:
  packages = (ROOT / "installer/arch-base.packages").read_text(encoding="utf-8").splitlines()
  if "omasnap" not in packages or "tensaku" in packages or "satty" in packages:
    fail_check("fresh installs use Omasnap instead of Satty and Tensaku")
  pass_check("fresh installs use Omasnap as the screenshot tool")

  screenshot_rule = (ROOT / "default/hypr/apps/screenshot-selection.lua").read_text(encoding="utf-8")
  system_rules = (ROOT / "default/hypr/apps/system.lua").read_text(encoding="utf-8")
  if 'namespace = "^omasnap$"' not in screenshot_rule or "no_screen_share = true" not in screenshot_rule:
    fail_check("Omasnap overlay policy is present")
  if "dev.tensaku.Tensaku" in system_rules:
    fail_check("removed Tensaku window rules are absent")
  pass_check("Hyprland applies Omasnap overlay policy without stale Tensaku rules")

  with tempfile.TemporaryDirectory(prefix="omasnap-test-") as temporary:
    scratch = Path(temporary)
    home = scratch / "home"
    bin_dir = scratch / "bin"
    bin_dir.mkdir()
    capture_log = scratch / "capture.log"
    migration_log = scratch / "migration.log"
    write_stub(
      bin_dir,
      "omasnap",
      'printf "%s\\t%s\\n" "${OMASNAP_SCREENSHOT_DIR:-}" "$*" >>"$OMASNAP_TEST_LOG"\n',
    )
    write_stub(
      bin_dir,
      "arch-i18n",
      'printf "i18n\\t%s\\n" "$1" >>"$OMASNAP_MIGRATION_LOG"; printf "%s\\n" "$1"\n',
    )
    write_stub(
      bin_dir,
      "arch-pkg-add",
      'printf "add\\t%s\\n" "$*" >>"$OMASNAP_MIGRATION_LOG"\n'
      'exit "${OMASNAP_PACKAGE_STATUS:-0}"\n',
    )
    write_stub(
      bin_dir,
      "arch-pkg-drop",
      'printf "drop\\t%s\\n" "$*" >>"$OMASNAP_MIGRATION_LOG"\n',
    )

    path = f"{bin_dir}:{ROOT / 'src/cli'}:{os.environ.get('PATH', '')}"

    def screenshot(args: list[str], **updates: str) -> subprocess.CompletedProcess[str]:
      environment = test_environment(
        HOME=str(home),
        PATH=path,
        OMASNAP_TEST_LOG=str(capture_log),
        **updates,
      )
      return run([str(SCREENSHOT_COMMAND), *args], environment)

    capture_cases = [
      ([], {}, "\t"),
      (["windows", "copy"], {"ARCH_SCREENSHOT_DIR": str(scratch / "legacy")}, f"{scratch / 'legacy'}\twindows --copy"),
      (["fullscreen", "save"], {
        "ARCH_SCREENSHOT_DIR": str(scratch / "legacy"),
        "OMASNAP_SCREENSHOT_DIR": str(scratch / "native"),
      }, f"{scratch / 'native'}\tfullscreen --save"),
      (["region", "slurp"], {}, "\tregion"),
      (["scroll", "--save"], {}, "\tscroll --save"),
    ]
    for index, (arguments, updates, expected) in enumerate(capture_cases):
      capture_log.write_text("", encoding="utf-8")
      result = screenshot(arguments, **updates)
      actual = capture_log.read_text(encoding="utf-8").rstrip("\n")
      if result.returncode != 0 or actual != expected:
        fail_check(f"screenshot route {index} forwards its supported arguments: {actual!r} {result.stderr}")
    pass_check("the os screenshot route delegates compatible arguments to Omasnap")

    config_home = home / ".config"
    data_home = home / ".local/share"
    applications = data_home / "applications"
    dotfiles = home / "dotfiles"
    (config_home / "imv").mkdir(parents=True)
    applications.mkdir(parents=True)
    dotfiles.mkdir()
    dotfile_config = dotfiles / "imv.config"
    original_config = (
      "[binds]\n\n"
      "# Edit the current image in Tensaku and quit the viewer\n"
      '<Ctrl+e> = exec tensaku-edit "$imv_current_file" & ; quit\n'
      '<Ctrl+x> = exec custom-editor "$imv_current_file" & ; quit\n'
    )
    dotfile_config.write_text(original_config, encoding="utf-8")
    config_link = config_home / "imv/config"
    config_link.symlink_to(dotfile_config)
    desktop = applications / ".".join(MIGRATION_CONFIG["paths"]["desktop_file"])
    generated_entry = "[Desktop Entry]\n" + "".join(
      f"{key}={value}\n" for key, value in MIGRATION_CONFIG["desktop"]["generated_entry"].items()
    )
    desktop.write_text(generated_entry, encoding="utf-8")

    def migrate(**updates: str) -> subprocess.CompletedProcess[str]:
      environment = test_environment(
        ARCH_PATH=str(ROOT),
        HOME=str(home),
        XDG_CONFIG_HOME=str(config_home),
        XDG_DATA_HOME=str(data_home),
        PATH=path,
        OMASNAP_MIGRATION_LOG=str(migration_log),
        **updates,
      )
      return run(["python3", "-I", str(MIGRATION)], environment)

    migration_log.write_text("", encoding="utf-8")
    failed_install = migrate(OMASNAP_PACKAGE_STATUS="1")
    if failed_install.returncode == 0:
      fail_check("an Omasnap installation failure stops the migration")
    if dotfile_config.read_text(encoding="utf-8") != original_config or desktop.read_text(encoding="utf-8") != generated_entry:
      fail_check("installation failure preserves the old screenshot setup")
    if migration_log.read_text(encoding="utf-8").splitlines() != [
      "i18n\tmigration.replaceScreenshotEditor",
      "add\tomasnap",
    ]:
      fail_check("installation failure does not remove Satty or Tensaku")
    pass_check("Omasnap install failure preserves the previous screenshot setup")

    migration_log.write_text("", encoding="utf-8")
    result = migrate()
    if result.returncode != 0 or "migration.replaceScreenshotEditor" not in result.stdout:
      fail_check(f"migration succeeds with a localized status: {result.stderr}{result.stdout}")
    expected_config = original_config.replace(
      "# Edit the current image in Tensaku and quit the viewer",
      "# Edit the current image in Omasnap and quit the viewer",
    ).replace(
      '<Ctrl+e> = exec tensaku-edit "$imv_current_file" & ; quit',
      '<Ctrl+e> = exec omasnap "$imv_current_file" & ; quit',
    )
    if dotfile_config.read_text(encoding="utf-8") != expected_config or not config_link.is_symlink():
      fail_check("migration updates only stock imv bindings and preserves the dotfile symlink")
    if desktop.exists():
      fail_check("the exact obsolete user-local launcher is removed")
    if migration_log.read_text(encoding="utf-8").splitlines() != [
      "i18n\tmigration.replaceScreenshotEditor",
      "add\tomasnap",
      "drop\tsatty tensaku",
    ]:
      fail_check("Omasnap installs before old screenshot packages are removed")
    if MIGRATION.stat().st_mode & 0o777 != 0o644:
      fail_check("Python migration is mode 0644")
    pass_check("migration swaps packages and updates only the stock imv binding")

    migrated_config = dotfile_config.read_text(encoding="utf-8")
    result = migrate()
    if result.returncode != 0 or dotfile_config.read_text(encoding="utf-8") != migrated_config:
      fail_check("repeating the migration leaves the updated imv config unchanged")
    pass_check("the migration can be rerun without changing the updated config")

    desktop.write_text(generated_entry.replace("NoDisplay=true", "NoDisplay=false"), encoding="utf-8")
    result = migrate()
    if result.returncode != 0 or not desktop.exists():
      fail_check("a customized launcher with the same name is preserved")
    pass_check("a customized launcher with the same name is preserved")

    dotfile_config.write_text('<Ctrl+e> = exec custom-editor "$imv_current_file" & ; quit\n', encoding="utf-8")
    custom_config = dotfile_config.read_text(encoding="utf-8")
    result = migrate()
    if result.returncode != 0 or dotfile_config.read_text(encoding="utf-8") != custom_config:
      fail_check("a custom imv edit shortcut remains unchanged")
    pass_check("custom imv edit shortcuts remain unchanged")


if __name__ == "__main__":
  main()
