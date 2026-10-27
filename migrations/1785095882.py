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


def systemctl(config: dict, action: str) -> subprocess.CompletedProcess[bytes]:
  return subprocess.run(
    [*config["commands"]["systemctl_user"], *config["actions"][action]],
    check=False,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  subprocess.run([*config["commands"]["i18n"], config["messages"]["reason"]], check=False)

  systemctl(config, "reload_before")
  systemctl(config, "stop_retired_path")

  enabled = systemctl(config, "enable_notifier")
  if enabled.returncode != int(config["statuses"]["success"]):
    wants_dir = Path.home() / config["paths"]["wants_directory"]
    wants_dir.mkdir(parents=True, exist_ok=True)
    link = wants_dir / config["paths"]["notifier_link"]
    if link.is_symlink() or link.is_file():
      link.unlink()
    link.symlink_to(config["paths"]["notifier_unit"])

  wants_dir = Path.home() / config["paths"]["wants_directory"]
  for name in config["paths"]["retired_links"]:
    link = wants_dir / name
    if link.is_symlink() or link.is_file():
      link.unlink()

  systemctl(config, "reset_retired_path")
  systemctl(config, "reload_after")
  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
