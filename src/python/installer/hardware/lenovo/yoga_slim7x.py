"""Install board-specific setup for Lenovo Yoga Slim 7x systems."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def load_config() -> dict:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/lenovo/yoga-slim7x.yml").read_text(encoding="utf-8"),
  )
  return config


def directory(config: dict, key: str) -> Path:
  item = config["directories"][key]
  return Path(os.environ.get(item["environment"]) or item["default"])


def install_file(target: Path, content: str, mode: str) -> None:
  target.parent.mkdir(parents=True, exist_ok=True)
  with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as temporary:
    temporary.write(content)
    temporary_path = Path(temporary.name)
  try:
    temporary_path.chmod(int(mode, 8))
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)


def main() -> int:
  config = load_config()
  statuses = config["statuses"]
  for command in config["hardware_checks"]:
    if subprocess.run(command, check=False).returncode != int(statuses["complete"]):
      return int(statuses["complete"])

  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  messages = config["messages"].get(language, config["messages"]["en"])
  print(messages["detected"])
  for item in config["files"]:
    install_file(
      directory(config, item["directory"]) / item["name"],
      item["content"],
      item["mode"],
    )
  subprocess.run(config["enable_service"], check=True)
  return int(statuses["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
