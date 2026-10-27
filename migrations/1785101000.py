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


def localized(config: dict, key: str, *arguments: str) -> str:
  result = subprocess.run(
    [*config["commands"]["i18n"], key, *arguments],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  print(localized(config, config["messages"]["reason"]))

  client = subprocess.run(
    [*config["commands"]["command_present"], config["commands"]["network_client"]],
    check=False,
  )
  if client.returncode != int(config["statuses"]["present"]):
    return int(config["statuses"]["success"])

  subprocess.run(
    [*config["commands"]["systemctl_user"], *config["actions"]["daemon_reload"]],
    check=False,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
  enabled = subprocess.run(
    [*config["commands"]["systemctl_user"], *config["actions"]["enable"]],
    check=False,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
  )
  if enabled.returncode != int(config["statuses"]["success"]):
    print(localized(config, config["messages"]["enable_failed"], enabled.stdout.rstrip("\n")))

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
