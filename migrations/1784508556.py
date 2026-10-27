from __future__ import annotations

import os
from pathlib import Path
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

  config_dir = Path.home() / config["paths"]["config_dir"]
  for browser in config["browsers"]:
    path = config_dir / f"{browser}{config['values']['file_suffix']}"
    if not path.is_file():
      continue

    content = path.read_text(encoding="utf-8")
    if config["values"]["setting_key"] in content:
      continue
    needs_separator = bool(content and not content.endswith(config["values"]["line_break"]))
    with path.open("a", encoding="utf-8") as stream:
      block = config["values"]["line_break"] if needs_separator else ""
      block += config["values"]["setting"] + config["values"]["line_break"]
      stream.write(block)

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
