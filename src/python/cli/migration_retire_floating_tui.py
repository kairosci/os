from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError(f"Invalid migration configuration: {path}")
  return value


def desktop_entry(path: Path) -> dict[str, str] | None:
  fields: dict[str, str] = {}
  in_entry = False
  for line in path.read_text(encoding="utf-8").splitlines():
    if line.startswith("["):
      if in_entry:
        break
      in_entry = line == "[Desktop Entry]"
      continue
    if not in_entry or "=" not in line:
      continue
    key, value = line.split("=", 1)
    key = key.strip()
    if key in fields:
      return None
    fields[key] = value.strip()
  return fields if in_entry else None


def main(migration_path: Path) -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_yaml(root / "data/migrations" / f"{migration_path.stem}.yml")
  data_home_value = os.environ.get("XDG_DATA_HOME")
  data_home = Path(data_home_value) if data_home_value else Path.home() / config["paths"]["default_data_directory"]
  if not data_home.is_absolute():
    return int(config["statuses"]["success"])
  try:
    resolved_data_home = data_home.resolve(strict=True)
    applications = resolved_data_home / config["paths"]["applications_directory"]
    resolved_applications = applications.resolve(strict=True)
  except FileNotFoundError:
    return int(config["statuses"]["success"])
  if not resolved_applications.is_relative_to(resolved_data_home):
    return int(config["statuses"]["success"])

  desktop_file = applications / config["paths"]["desktop_file"]
  if desktop_file.is_symlink() or not desktop_file.is_file():
    return int(config["statuses"]["success"])
  if desktop_entry(desktop_file) != config["desktop"]["generated_entry"]:
    return int(config["statuses"]["success"])

  desktop_file.unlink()
  translated = subprocess.run(
    [*config["commands"]["i18n"], config["messages"]["removed"]],
    check=True,
    capture_output=True,
    text=True,
  )
  print(translated.stdout.rstrip("\n"))
  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
