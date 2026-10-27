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

  autostart_file = Path.home() / config["paths"]["autostart_file"]
  autostart_file.parent.mkdir(parents=True, exist_ok=True)
  autostart_file.write_text(config["files"]["hidden_desktop_entry"], encoding="utf-8")

  for action in config["commands"]["user_systemctl_actions"]:
    subprocess.run(
      [*config["commands"]["user_systemctl"], *action],
      check=False,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
    )

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
