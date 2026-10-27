from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import yaml


def load_config(root: Path) -> dict:
  config_path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError()
  return config


def run(config: dict, command: str, *args: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run([*config["commands"][command], *args], capture_output=True, text=True, check=False)


def report(config: dict, key: str, *args: str, error: bool = False) -> None:
  result = subprocess.run(
    [*config["commands"]["i18n"], key, *args],
    capture_output=True,
    text=True,
    check=False,
  )
  message = result.stdout.rstrip("\n")
  if message:
    print(message, file=sys.stderr if error else sys.stdout)


def command_error(result: subprocess.CompletedProcess[str]) -> str:
  return (result.stdout + result.stderr).strip()


def deferred(config: dict, result: subprocess.CompletedProcess[str]) -> int:
  report(config, config["messages"]["deferred"], command_error(result), error=True)
  return int(config["statuses"]["retry"])


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  report(config, config["messages"]["reason"])

  paths = config["paths"]
  values = config["values"]
  home = Path.home()
  config_home = Path(os.environ.get(paths["config_home_variable"]) or home / paths["default_config_home"])
  sleep_lock_unit = config_home / paths["sleep_lock_unit"]
  if sleep_lock_unit.is_file():
    dropin = config_home / paths["sleep_lock_dropin"]
    dropin.parent.mkdir(parents=True, exist_ok=True)
    dropin.write_text(values["dropin_contents"], encoding="utf-8")

  runtime_dir = Path(
    os.environ.get(paths["runtime_dir_variable"])
    or Path(paths["fallback_runtime_directory"]) / str(os.getuid())
  )
  user_manager_socket = runtime_dir / paths["user_manager_socket"]
  environment = run(config, "show_environment")
  if environment.returncode != 0:
    if user_manager_socket.is_socket():
      return deferred(config, environment)
    return int(config["statuses"]["success"])

  reload = run(config, "daemon_reload")
  if reload.returncode != 0:
    return deferred(config, reload)

  graphical_session = run(config, "show_active_state", values["graphical_session_target"])
  if graphical_session.returncode != 0:
    return deferred(config, graphical_session)

  service = paths["sleep_lock_service"]
  if graphical_session.stdout.strip() == values["active_state"]:
    reset = run(config, "reset_failed", service)
    if reset.returncode != 0:
      return deferred(config, reset)

    restart = run(config, "restart_service", service)
    if restart.returncode != 0:
      return deferred(config, restart)

    service_state = run(config, "show_active_state", service)
    if service_state.returncode != 0:
      return deferred(config, service_state)
    if service_state.stdout.strip() != values["active_state"]:
      report(config, config["messages"]["service_not_active"], service, error=True)
      return int(config["statuses"]["retry"])
  else:
    stop = run(config, "stop_service", service)
    if stop.returncode != 0:
      return deferred(config, stop)

    reset = run(config, "reset_failed", service)
    if reset.returncode != 0:
      return deferred(config, reset)

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
