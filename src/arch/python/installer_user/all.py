from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


def setup_steps(arch_path: Path) -> list[Path]:
  config_path = arch_path / "data/installer/user-setup.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  steps = config.get("steps") if isinstance(config, dict) else None
  if not isinstance(steps, list):
    raise ValueError(f"Invalid user setup configuration: {config_path}")

  scripts = []
  for step in steps:
    relative = Path(step) if isinstance(step, str) else Path("/")
    if relative.is_absolute() or relative.suffix != ".py" or ".." in relative.parts:
      raise ValueError(f"Invalid user setup step: {step!r}")
    script = arch_path / "src/arch/python/installer_user" / relative
    if not script.is_file():
      raise FileNotFoundError(script)
    scripts.append(script)
  return scripts


def main(arguments: list[str] | None = None) -> int:
  arch_path = Path(os.environ["ARCH_PATH"])
  scripts = setup_steps(arch_path)
  arguments = sys.argv[1:] if arguments is None else arguments
  if arguments == ["--count"]:
    print(len(scripts))
    return 0
  if arguments:
    return 2

  for script in scripts:
    result = subprocess.run(["python3", "-I", str(script)], check=False)
    if result.returncode:
      return result.returncode
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
