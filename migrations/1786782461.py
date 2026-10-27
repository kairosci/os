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

  foot_config = Path.home() / config["paths"]["foot_config"]
  if not foot_config.is_file():
    return int(config["statuses"]["success"])

  content = foot_config.read_bytes()
  bad_line = config["values"]["malformed_header"].encode("utf-8")
  lines = content.splitlines(keepends=True)
  repaired = []
  changed = False
  for line in lines:
    body = line[:-1] if line.endswith(b"\n") else line
    if body == bad_line:
      changed = True
    else:
      repaired.append(line)

  if changed:
    foot_config.write_bytes(b"".join(repaired))

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
