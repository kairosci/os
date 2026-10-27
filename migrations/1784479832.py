from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess

import yaml


def load_config(root: Path) -> dict:
  config_path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError()
  return config


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  subprocess.run([*config["commands"]["i18n"], config["messages"]["reason"]], check=False)

  kitty_config = Path.home() / config["paths"]["kitty_config"]
  if not kitty_config.is_file():
    return int(config["statuses"]["success"])

  content = kitty_config.read_text(encoding="utf-8")
  if re.search(config["patterns"]["listen_on"], content, re.MULTILINE):
    return int(config["statuses"]["success"])

  with kitty_config.open("a", encoding="utf-8") as stream:
    stream.write(config["append"]["block"])
    stream.write(config["values"]["listen_on"])
    stream.write("\n")

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
