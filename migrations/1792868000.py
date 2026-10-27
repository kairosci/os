from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml


def load_config(root: Path) -> dict[str, Any]:
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("invalid Wayland session migration configuration")
  return value


def localized(config: dict[str, Any], key: str) -> str:
  result = subprocess.run(
    [*config["commands"]["i18n"], config["messages"][key]],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  paths = config["paths"]
  session_dir = Path(os.environ.get(paths["session_dir_environment"]) or paths["session_dir_default"])
  source = root / paths["source_file"]
  if not source.is_file():
    print(localized(config, "source_missing"), file=sys.stderr)
    return int(config["statuses"]["failure"])

  target = session_dir / ".".join(paths["session_filename"])
  installed = subprocess.run(
    [*config["commands"]["install"], str(source), str(target)],
    check=False,
  )
  if installed.returncode != 0:
    return installed.returncode

  for entry in session_dir.glob(paths["obsolete_sessions_glob"]):
    if entry == target or not entry.exists():
      continue
    removed = subprocess.run([*config["commands"]["remove"], str(entry)], check=False)
    if removed.returncode != 0:
      return removed.returncode

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
