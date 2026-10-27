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


def captured_value(pattern: re.Pattern[str], contents: str) -> str:
  for line in contents.split("\n"):
    match = pattern.fullmatch(line)
    if match is not None:
      return match.group(1)
  return ""


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  subprocess.run([*config["commands"]["i18n"], config["messages"]["reason"]], check=False)

  wrapper_dir = Path.home() / config["paths"]["wrapper_dir"]
  if not wrapper_dir.is_dir():
    return int(config["statuses"]["success"])

  package_pattern = re.compile(config["patterns"]["package"])
  binary_pattern = re.compile(config["patterns"]["binary"])
  for wrapper in sorted(wrapper_dir.iterdir()):
    if not wrapper.is_file() or not os.access(wrapper, os.X_OK):
      continue
    contents = wrapper.read_text(encoding="utf-8")
    package = captured_value(package_pattern, contents)
    binary = captured_value(binary_pattern, contents)
    if not package or not binary:
      continue

    installed = subprocess.run(
      [*config["commands"]["install"], package, wrapper.name, binary],
      check=False,
    )
    if installed.returncode != int(config["statuses"]["success"]):
      return installed.returncode

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
