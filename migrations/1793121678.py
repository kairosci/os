from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml


def load_yaml(root: Path, relative_path: str) -> dict[str, Any]:
  value = yaml.safe_load((root / relative_path).read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError
  return value


def localized(config: dict[str, Any], name: str) -> str:
  result = subprocess.run(
    [*config["commands"]["i18n"], config["messages"][name]],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_yaml(root, f"data/migrations/{Path(__file__).stem}.yml")
  hardware = load_yaml(root, "data/installer/hardware/pacman-repositories.yml")
  settings = config["configuration"]
  path = Path(os.environ.get(settings["environment"]) or settings["default"])
  if path.is_symlink() or (path.exists() and not path.is_file()):
    print(localized(config, "invalid_config"), file=sys.stderr)
    return int(config["statuses"]["failure"])
  if not path.exists():
    return int(config["statuses"]["success"])

  content = path.read_text(encoding="utf-8")
  lines = content.splitlines()
  if settings["section_header"] not in lines:
    return int(config["statuses"]["success"])
  if re.search(hardware["legacy_signature_pattern"], content) is None:
    return int(config["statuses"]["success"])

  print(localized(config, "changed"))
  result = subprocess.run(
    [
      *config["commands"]["edit_config"],
      settings["signature_expression"],
      str(path),
    ],
    check=False,
  )
  return result.returncode


if __name__ == "__main__":
  raise SystemExit(main())
