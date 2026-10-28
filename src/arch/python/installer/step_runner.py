from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def _relative_path(value: object) -> Path:
  if not isinstance(value, str):
    raise ValueError(f"Invalid installer step path: {value!r}")
  path = Path(value)
  if path.is_absolute() or ".." in path.parts or path.suffix not in {".py", ".sh"}:
    raise ValueError(f"Invalid installer step path: {value!r}")
  return path


def _step_path(step: object, arch_path: Path, arch_install: Path) -> Path:
  if isinstance(step, str):
    root = arch_path
    relative = _relative_path(step)
  elif isinstance(step, dict):
    roots = {"arch_path": arch_path, "arch_install": arch_install}
    root_name = step.get("root", "arch_path")
    if root_name not in roots:
      raise ValueError(f"Invalid installer step root: {root_name!r}")
    root = roots[root_name]
    relative = _relative_path(step.get("path"))
  else:
    raise ValueError(f"Invalid installer step: {step!r}")

  script = root / relative
  if not script.is_file():
    raise FileNotFoundError(script)
  return script


def _step_reference(step: object) -> str:
  if isinstance(step, str):
    return str(_relative_path(step))
  if isinstance(step, dict):
    root_name = step.get("root", "arch_path")
    relative = _relative_path(step.get("path"))
    if root_name == "arch_path":
      return str(relative)
    if root_name == "arch_install":
      return str(Path("installer") / relative)
    raise ValueError(f"Invalid installer step root: {root_name!r}")
  raise ValueError(f"Invalid installer step: {step!r}")


def _load_steps(
  arch_path: Path, arch_install: Path, config_relative: Path
) -> tuple[list[Path], dict[str, str]]:
  if config_relative.is_absolute() or ".." in config_relative.parts:
    raise ValueError(f"Invalid installer step configuration: {config_relative}")
  config_path = arch_path / config_relative
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  steps = config.get("steps") if isinstance(config, dict) else None
  if not isinstance(steps, list):
    raise ValueError(f"Invalid installer step configuration: {config_path}")

  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  messages = config.get("messages", {})
  localized = messages.get(language, messages.get("en", {}))
  scripts = [_step_path(step, arch_path, arch_install) for step in steps]
  return scripts, localized


def _load_step_references(
  arch_path: Path, arch_install: Path, config_relative: Path
) -> list[str]:
  _load_steps(arch_path, arch_install, config_relative)
  config_path = arch_path / config_relative
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  return [_step_reference(step) for step in config["steps"]]


def run_steps(arch_path: Path, arch_install: Path, config_relative: Path) -> int:
  scripts, localized = _load_steps(arch_path, arch_install, config_relative)

  for script in scripts:
    _log(localized, "starting", script)
    if script.suffix == ".py":
      command = ["python3", "-I", str(script)]
      environment = None
    else:
      debug = os.environ.get("ARCH_INSTALL_DEBUG") == "1"
      shell_flags = ["-x", "-eE"] if debug else ["-eE"]
      command = ["bash", *shell_flags, "-c", 'source "$1"', "bash", str(script)]
      environment = os.environ.copy()
      if debug:
        environment["PS4"] = "+ ${BASH_SOURCE[0]##*/}:${LINENO}:${FUNCNAME[0]:-main}: "
    status = subprocess.run(command, check=False, env=environment).returncode
    if status:
      _log(localized, "failed", script, status)
      return status
    _log(localized, "completed", script)
  return 0


def _log(messages: dict[str, str], key: str, script: Path, status: int | None = None) -> None:
  values = {"step": str(script)}
  if status is not None:
    values["status"] = str(status)
  timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
  print(f"[{timestamp}] {messages[key].format(**values)}", flush=True)


def main(arguments: list[str] | None = None) -> int:
  arguments = sys.argv[1:] if arguments is None else arguments
  validate = arguments[:1] == ["--validate"]
  list_steps = arguments[:1] == ["--list"]
  if validate:
    arguments = arguments[1:]
  elif list_steps:
    arguments = arguments[1:]
  if len(arguments) != 1:
    return 2
  arch_path = Path(os.environ["ARCH_PATH"])
  arch_install = Path(os.environ.get("ARCH_INSTALL", str(arch_path / "installer")))
  config_relative = Path(arguments[0])
  if validate:
    _load_steps(arch_path, arch_install, config_relative)
    return 0
  if list_steps:
    for step in _load_step_references(arch_path, arch_install, config_relative):
      print(step)
    return 0
  return run_steps(arch_path, arch_install, config_relative)


if __name__ == "__main__":
  raise SystemExit(main())
