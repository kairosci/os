from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any

import yaml

sys.path.insert(0, str(Path(os.environ["ARCH_PATH"]) / "src/python"))
from cli.desktop_entry import remove_exact_desktop_entry


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("Invalid migration configuration")
  return config


def rewrite_config(path: Path, replacements: list[dict[str, str]]) -> None:
  if not path.is_file():
    return
  target = path.resolve(strict=True)
  try:
    original = target.read_text(encoding="utf-8")
  except (OSError, UnicodeError):
    return

  replacement_map = {item["from"]: item["to"] for item in replacements}
  updated_lines: list[str] = []
  for line in original.splitlines(keepends=True):
    content = line.rstrip("\r\n")
    ending = line[len(content):]
    updated_lines.append(f"{replacement_map.get(content, content)}{ending}")
  updated = "".join(updated_lines)
  if updated == original:
    return

  temporary_path: str | None = None
  try:
    with tempfile.NamedTemporaryFile(
      mode="w", encoding="utf-8", dir=target.parent,
      prefix=f".{target.name}.", delete=False,
    ) as temporary:
      temporary_path = temporary.name
      temporary.write(updated)
      temporary.flush()
      os.fsync(temporary.fileno())
    os.chmod(temporary_path, stat.S_IMODE(target.stat().st_mode))
    os.replace(temporary_path, target)
  finally:
    if temporary_path and os.path.exists(temporary_path):
      os.unlink(temporary_path)


def main() -> int:
  config = load_config()
  commands = config["commands"]
  messages = config["messages"]
  translated = subprocess.run(
    [*commands["i18n"], messages["reason"]],
    check=True,
    capture_output=True,
    text=True,
  )
  print(translated.stdout.rstrip("\n"))

  subprocess.run([*commands["package_add"], *config["packages"]["add"]], check=True)

  paths = config["paths"]
  config_home = Path(os.environ.get(paths["xdg_config_environment"]) or (
    Path.home() / paths["default_config_directory"]
  ))
  if not config_home.is_absolute():
    config_home = Path.home() / paths["default_config_directory"]
  rewrite_config(config_home / paths["imv_config"], config["imv"]["replacements"])

  data_home = Path(os.environ.get(paths["xdg_data_environment"]) or (
    Path.home() / paths["default_data_directory"]
  ))
  if not data_home.is_absolute():
    data_home = Path.home() / paths["default_data_directory"]
  try:
    resolved_data_home = data_home.resolve(strict=True)
    applications = resolved_data_home / paths["applications_directory"]
    resolved_applications = applications.resolve(strict=True)
  except FileNotFoundError:
    resolved_applications = None
    applications = None
  if resolved_applications is not None and resolved_applications.is_relative_to(resolved_data_home):
    remove_exact_desktop_entry(
      applications / ".".join(paths["desktop_file"]),
      [config["desktop"]["generated_entry"]],
    )

  subprocess.run([*commands["package_drop"], *config["packages"]["drop"]], check=True)

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
