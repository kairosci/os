from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  value = yaml.safe_load(
    (root / "data/migrations" / f"{Path(__file__).stem}.yml").read_text(encoding="utf-8")
  )
  if not isinstance(value, dict):
    raise ValueError("Invalid migration configuration")
  return value


def is_managed_target(target: Path, markers: list[list[str]]) -> bool:
  parts = target.parts
  for marker in markers:
    length = len(marker)
    if any(parts[index:index + length] == tuple(marker) for index in range(len(parts) - length + 1)):
      return True
  return False


def main() -> int:
  config = load_config()
  home = Path.home().resolve(strict=True)
  removed = 0

  for pattern in config["search"]["roots"]:
    roots = sorted(home.glob(pattern))
    for root in roots:
      if root.is_symlink() or not root.is_dir():
        continue
      resolved_root = root.resolve(strict=True)
      if not resolved_root.is_relative_to(home):
        continue
      for link in sorted(root.iterdir()):
        if not link.is_symlink():
          continue
        target_text = os.readlink(link)
        target_path = Path(target_text)
        if not target_path.is_absolute():
          target_path = link.parent / target_path
        normalized = Path(os.path.normpath(target_path))
        if is_managed_target(normalized, config["search"]["target_path_segments"]):
          link.unlink()
          removed += 1

  if removed:
    result = subprocess.run(
      [
        *config["commands"]["i18n"],
        config["messages"]["removed"],
        str(removed),
      ],
      check=True,
      capture_output=True,
      text=True,
    )
    print(result.stdout.rstrip("\n"))
  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
