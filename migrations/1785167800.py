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


def show_message(config: dict, key: str, *args: str) -> None:
  subprocess.run([*config["commands"]["i18n"], key, *args], check=False)


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  show_message(config, config["messages"]["reason"])

  subprocess.run(config["commands"]["daemon_reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

  service = config["paths"]["service"]
  enabled = subprocess.run([*config["commands"]["enable_service"], service], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
  if enabled.returncode != 0:
    wants_dir = Path.home() / config["paths"]["user_config"] / config["paths"]["wants_dir"]
    wants_dir.mkdir(parents=True, exist_ok=True)
    enablement = wants_dir / service
    service_file = config["paths"]["service_file"]
    if not enablement.is_symlink() or os.readlink(enablement) != service_file:
      enablement.unlink(missing_ok=True)
      enablement.symlink_to(service_file)

  graphical_session = subprocess.run(
    [*config["commands"]["check_graphical_session"], config["values"]["graphical_session_target"]],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
  )
  if graphical_session.returncode == 0:
    subprocess.run(
      [*config["commands"]["stop_process"], config["values"]["process_name"]],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      check=False,
    )
    start = subprocess.run([*config["commands"]["start_service"], service], capture_output=True, text=True, check=False)
    if start.returncode != 0:
      error = (start.stdout + start.stderr).strip()
      show_message(config, config["messages"]["start_failed"], service, error)
      show_message(config, config["messages"]["compose_unavailable"])

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
