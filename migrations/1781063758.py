from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile

import yaml


def load_config(root: Path) -> dict:
  config_path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError()
  return config


def migrated_lines(lines: list[str], config: dict) -> list[str]:
  old = config["source"]
  replacement = config["replacement"]
  output = []
  replaced = False
  index = 0

  while index < len(lines):
    if not replaced and lines[index] == old["comment"]:
      if index + 1 < len(lines) and lines[index + 1] == old["package_path"]:
        output.extend([replacement["comment"], replacement["bootstrap"]])
        replaced = True
        index += 2
        while index < len(lines):
          line = lines[index]
          index += 1
          if re.fullmatch(old["path_terminator_pattern"], line):
            break
        continue

      output.append(lines[index])
      index += 1
      if index < len(lines):
        output.append(lines[index])
        index += 1
      continue

    output.append(lines[index])
    index += 1

  return output


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  subprocess.run([*config["commands"]["i18n"], config["messages"]["reason"]], check=False)

  user_config = Path.home() / config["paths"]["hyprland_config"]
  if not user_config.is_file():
    return int(config["statuses"]["success"])

  source = user_config.read_text(encoding="utf-8")
  if config["values"]["bootstrap_marker"] in source:
    return int(config["statuses"]["success"])

  lines = migrated_lines(source.splitlines(), config)
  migrated = "\n".join(lines) + ("\n" if lines else "")
  temporary_path = None
  try:
    with tempfile.NamedTemporaryFile(
      mode="w",
      encoding="utf-8",
      dir=user_config.parent,
      delete=False,
    ) as temporary:
      temporary_path = Path(temporary.name)
      temporary.write(migrated)
      temporary.flush()
      os.fsync(temporary.fileno())
    temporary_path.replace(user_config)
  finally:
    if temporary_path is not None:
      temporary_path.unlink(missing_ok=True)

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
