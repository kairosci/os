from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
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


def main() -> int:
  config = load_config()
  translated = subprocess.run(
    [*config["commands"]["i18n"], config["messages"]["reason"]],
    check=True,
    capture_output=True,
    text=True,
  )
  print(translated.stdout.rstrip("\n"))

  for package in config["packages"]["add"]:
    subprocess.run([*config["commands"]["package_add"], package], check=True)
  for package in config["packages"]["drop"]:
    subprocess.run([*config["commands"]["package_drop"], package], check=True)

  paths = config["paths"]
  data_home_value = os.environ.get(paths["xdg_data_environment"])
  data_home = Path(data_home_value) if data_home_value else Path.home() / paths["default_data_directory"]
  if data_home.is_absolute():
    try:
      resolved_data_home = data_home.resolve(strict=True)
      applications = resolved_data_home / paths["applications_directory"]
      resolved_applications = applications.resolve(strict=True)
    except FileNotFoundError:
      resolved_applications = None
      applications = None

    if resolved_applications is not None and resolved_applications.is_relative_to(resolved_data_home):
      desktop_file = applications / paths["desktop_file"]
      if remove_exact_desktop_entry(desktop_file, config["desktop"]["generated_entries"]):
        translated = subprocess.run(
          [*config["commands"]["i18n"], config["messages"]["removed"]],
          check=True,
          capture_output=True,
          text=True,
        )
        print(translated.stdout.rstrip("\n"))
      subprocess.run(
        [*config["commands"]["update_database"], str(applications)], check=True
      )

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
