from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("Invalid migration configuration")
  return value


def remove_managed_wrapper(home: Path, config: dict[str, Any], tool: dict[str, str]) -> None:
  wrapper_dir = home / config["wrappers"]["directory"]
  if wrapper_dir.is_symlink() or not wrapper_dir.is_dir():
    return
  try:
    resolved_dir = wrapper_dir.resolve(strict=True)
  except OSError:
    return
  if not resolved_dir.is_relative_to(home):
    return

  wrapper = wrapper_dir / tool["command"]
  if wrapper.is_symlink() or not wrapper.is_file():
    return
  expected = config["wrappers"]["template"].format(**tool)
  try:
    if wrapper.read_bytes() == expected.encode("utf-8"):
      wrapper.unlink()
  except OSError:
    return


def run(command: list[str]) -> None:
  subprocess.run(command, check=True, capture_output=True, text=True)


def main() -> int:
  config = load_config()
  home = Path.home().resolve(strict=True)
  for tool in config["tools"]:
    remove_managed_wrapper(home, config, tool)
    run([*config["commands"]["unuse_global"], tool["tool"]])
  run(config["commands"]["reshim"])
  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
