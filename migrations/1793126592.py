from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config(root: Path, migration_name: str) -> dict[str, Any]:
  config = yaml.safe_load((root / "data/migrations" / f"{migration_name}.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError(f"Invalid migration configuration: {migration_name}")
  return config


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root, Path(__file__).stem)
  commands = config["commands"]
  reason = subprocess.run(
    [*commands["i18n"], config["messages"]["reason"]],
    check=True,
    capture_output=True,
    text=True,
  )
  print(reason.stdout.rstrip("\n"))

  unit = config["unit"]
  state = subprocess.run(
    [*commands["is_active"], unit], check=False, capture_output=True, text=True
  )
  if state.stdout.strip() not in config["inactive_states"]:
    subprocess.run([*commands["stop"], unit], check=True)

  home = Path.home().resolve()
  for relative_directory in config["user_unit_directories"]:
    directory = home / relative_directory
    if not directory.is_dir():
      continue
    for suffix in config["link_suffixes"]:
      for link in directory.glob(f"*.{suffix}/{unit}"):
        if link.parent.resolve(strict=False).is_relative_to(home) and link.is_symlink():
          link.unlink()

  subprocess.run(commands["daemon_reload"], check=True)
  subprocess.run([*commands["package_drop"], *config["packages"]], check=True)
  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
