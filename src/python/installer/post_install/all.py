from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

import yaml


def _load(arch_path: Path) -> tuple[list[Path], dict[str, str]]:
  config_path = arch_path / "data/installer/post-install.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  steps = config.get("steps") if isinstance(config, dict) else None
  if not isinstance(steps, list):
    raise ValueError(f"Invalid post-install configuration: {config_path}")

  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  messages = config.get("messages", {})
  localized = messages.get(language, messages.get("en", {}))
  if not isinstance(localized, dict):
    raise ValueError(f"Invalid post-install messages: {config_path}")

  scripts = []
  for step in steps:
    relative = Path(step) if isinstance(step, str) else Path("/")
    if relative.is_absolute() or ".." in relative.parts or relative.suffix not in {".py", ".sh"}:
      raise ValueError(f"Invalid post-install step: {step!r}")
    script = arch_path / relative
    if not script.is_file():
      raise FileNotFoundError(script)
    scripts.append(script)
  return scripts, localized


def _log(messages: dict[str, str], key: str, script: Path, status: int | None = None) -> None:
  template = messages[key]
  values = {"step": str(script)}
  if status is not None:
    values["status"] = str(status)
  timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
  print(f"[{timestamp}] {template.format(**values)}", flush=True)


def main() -> int:
  arch_path = Path(os.environ["ARCH_PATH"])
  scripts, messages = _load(arch_path)
  for script in scripts:
    _log(messages, "starting", script)
    if script.suffix == ".py":
      command = ["python3", "-I", str(script)]
      environment = None
    else:
      shell_flags = ["-x", "-eE"] if os.environ.get("ARCH_INSTALL_DEBUG") == "1" else ["-eE"]
      command = ["bash", *shell_flags, "-c", 'source "$1"', "bash", str(script)]
      environment = os.environ.copy()
      if os.environ.get("ARCH_INSTALL_DEBUG") == "1":
        environment["PS4"] = "+ ${BASH_SOURCE[0]##*/}:${LINENO}:${FUNCNAME[0]:-main}: "
    status = subprocess.run(command, check=False, env=environment).returncode
    if status:
      _log(messages, "failed", script, status)
      return status
    _log(messages, "completed", script)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
