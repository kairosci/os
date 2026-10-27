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


def run(config: dict, command: str, *arguments: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run([*config["commands"][command], *arguments], check=False, text=True)


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  run(config, "i18n", config["messages"]["reason"])

  beta_package = config["packages"]["beta"]
  if run(config, "package_present", beta_package).returncode != int(config["statuses"]["present"]):
    return int(config["statuses"]["success"])

  default_browser = subprocess.run(
    [*config["commands"]["default_browser_query"], *config["arguments"]["default_browser_query"]],
    check=False,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
  )
  default_id = default_browser.stdout.rstrip("\n") if default_browser.returncode == int(config["statuses"]["success"]) else ""

  installed = run(config, "aur_add", config["packages"]["stable"])
  if installed.returncode != int(config["statuses"]["success"]):
    return installed.returncode
  removed = run(config, "package_drop", beta_package)
  if removed.returncode != int(config["statuses"]["success"]):
    return removed.returncode

  home = Path.home()
  config_dir = home / config["paths"]["config_dir"]
  config_dir.mkdir(parents=True, exist_ok=True)
  copied = run(
    config,
    "copy",
    "-f",
    str(root / config["paths"]["default_flags"]),
    str(config_dir / config["paths"]["stable_flags_name"]),
  )
  if copied.returncode != int(config["statuses"]["success"]):
    return copied.returncode

  stale_flags = config_dir / config["paths"]["beta_flags_name"]
  stale_flags.unlink(missing_ok=True)
  if default_id == config["desktop"]["beta"]:
    selected = run(config, "set_default_browser", config["desktop"]["stable_name"])
    if selected.returncode != int(config["statuses"]["success"]):
      return selected.returncode

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
