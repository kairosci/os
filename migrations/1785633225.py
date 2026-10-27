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

  foot_config = Path.home() / config["paths"]["foot_config"]
  if not foot_config.is_file():
    return int(config["statuses"]["success"])

  content = foot_config.read_text(encoding="utf-8")
  if re.search(config["patterns"]["scroll_multiplier"], content, re.MULTILINE):
    return int(config["statuses"]["success"])

  lines = content.splitlines()
  section = config["values"]["scrollback_section"]
  if section in lines:
    index = lines.index(section) + int(config["values"]["insert_after_section"])
    lines.insert(index, config["values"]["multiplier_setting"])
    foot_config.write_text("\n".join(lines) + "\n", encoding="utf-8")
  else:
    with foot_config.open("a", encoding="utf-8") as stream:
      stream.write(config["values"]["append_block"])

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
