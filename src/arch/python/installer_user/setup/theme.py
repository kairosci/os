from __future__ import annotations

import os
import re
import secrets
import subprocess
import tempfile
from pathlib import Path

import yaml


def _run(command: list[str], environment: dict[str, str] | None = None) -> int:
  return subprocess.run(command, env=environment, check=False).returncode


def _write_icon_theme(settings: dict[str, object], home: Path) -> None:
  source = Path(str(settings["icon_source"]))
  if not source.is_file():
    return
  content = source.read_text(encoding="utf-8")
  pattern = str(settings["icon_pattern"])
  if re.search(pattern, content, flags=re.MULTILINE) is None:
    return

  directory = home / str(settings["icon_directory"])
  directory.mkdir(parents=True, exist_ok=True)
  destination = directory / str(settings["icon_filename"])
  replacement = str(settings["icon_replacement"])
  updated = re.sub(pattern, lambda _: replacement, content, flags=re.MULTILINE)
  descriptor, temporary = tempfile.mkstemp(dir=directory)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(updated)
    os.chmod(temporary, int(str(settings["icon_mode"]), 8))
    os.replace(temporary, destination)
  finally:
    Path(temporary).unlink(missing_ok=True)


def _link_btop_theme(settings: dict[str, object], home: Path) -> None:
  directory = home / str(settings["btop_directory"])
  directory.mkdir(parents=True, exist_ok=True)
  destination = directory / str(settings["btop_link"])
  temporary = directory / f".{destination.name}.{secrets.token_hex(8)}"
  os.symlink(home / str(settings["btop_target"]), temporary)
  try:
    os.replace(temporary, destination)
  finally:
    temporary.unlink(missing_ok=True)


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["theme_setup"]
  home = Path.home()
  (home / str(settings["directory"])).mkdir(parents=True, exist_ok=True)

  selected = home / str(settings["selected_theme_file"])
  if not selected.is_file() or selected.stat().st_size == 0:
    command = [*settings["set_command"], str(settings["default_theme"])]
    context = os.environ.get(str(settings["context_environment"]), str(settings["runtime_context"]))
    environment = None
    if context != settings["runtime_context"]:
      environment = {**os.environ, **settings["headless_environment"]}
    status = _run(command, environment)
    if status:
      return status
    if environment is not None:
      (home / str(settings["chromium_lock"])).unlink(missing_ok=True)

  for command in settings["activation_commands"]:
    status = _run(command)
    if status:
      return status

  _write_icon_theme(settings, home)
  _link_btop_theme(settings, home)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
