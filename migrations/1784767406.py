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

  state_file = Path.home() / config["paths"]["toggle"]
  state_file.unlink(missing_ok=True)
  if os.environ.get(config["environment"]["live_upgrade"]) != config["environment"]["live_value"]:
    subprocess.run(config["commands"]["reload"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
