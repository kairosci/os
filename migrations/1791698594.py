from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml


def load_config(root: Path) -> dict[str, Any]:
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("invalid workspace layout migration configuration")
  return value


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  print(subprocess.run(
    [*config["commands"]["i18n"], config["message"]],
    check=False,
    capture_output=True,
    text=True,
  ).stdout.rstrip("\n"))

  home = Path(os.environ["HOME"])
  environment_name = config["paths"]["state_home_environment"]
  state_homes = [home / config["paths"]["default_state_home"]]
  xdg_state_home = os.environ.get(environment_name)
  if xdg_state_home:
    state_homes.append(Path(xdg_state_home))

  pattern = re.compile(config["rewrite"]["pattern"])
  replacement = config["rewrite"]["replacement"]
  for state_home in dict.fromkeys(state_homes):
    directory = state_home / config["paths"]["layout_directory"]
    for path in directory.glob(config["paths"]["file_pattern"]):
      if not path.is_file():
        continue
      content = path.read_text(encoding="utf-8")
      updated = pattern.sub(replacement, content)
      if updated != content:
        with path.open("r+", encoding="utf-8") as output:
          output.write(updated)
          output.truncate()

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
