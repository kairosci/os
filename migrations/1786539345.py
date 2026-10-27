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


def run_user_systemctl(config: dict, action: str) -> subprocess.CompletedProcess[bytes]:
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

  run_user_systemctl(config, "daemon_reload")
  enabled = run_user_systemctl(config, "enable")
  if enabled.returncode != int(config["statuses"]["success"]):
    link = Path.home() / config["paths"]["fallback_link"]
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() or link.is_file():
      link.unlink()
    link.symlink_to(config["paths"]["unit_file"])

  active = run_user_systemctl(config, "graphical_session_active")
  if active.returncode == int(config["statuses"]["success"]):
    run_user_systemctl(config, "start")

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
