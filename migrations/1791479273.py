from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("Invalid migration configuration")
  return config


def write_default(path: Path, value: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  temporary_path: str | None = None
  try:
    with tempfile.NamedTemporaryFile(
      mode="w", encoding="utf-8", dir=path.parent,
      prefix=f".{path.name}.", delete=False,
    ) as temporary:
      temporary_path = temporary.name
      temporary.write(f"{value}\n")
      temporary.flush()
      os.fsync(temporary.fileno())
    try:
      os.link(temporary_path, path)
    except FileExistsError:
      return
  finally:
    if temporary_path and os.path.exists(temporary_path):
      os.unlink(temporary_path)


def main() -> int:
  config = load_config()
  subprocess.run(
    [*config["commands"]["i18n"], config["messages"]["reason"]], check=True
  )

  home = Path.home()
  path_settings = config["paths"]
  config_home = Path(os.environ.get(path_settings["xdg_config_environment"]) or (
    home / path_settings["default_config_directory"]
  ))
  backend_config = config_home / path_settings["backend_config"]
  if backend_config.exists() or backend_config.is_symlink():
    return int(config["statuses"]["success"])

  package = config["packages"]["voxtype"]
  installed = subprocess.run(
    [*config["commands"]["package_present"], package], check=False
  )
  if installed.returncode == int(config["statuses"]["success"]):
    write_default(backend_config, config["values"]["backend"])

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
