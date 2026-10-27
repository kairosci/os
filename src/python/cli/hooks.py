from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


def _config() -> dict:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/hooks.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid hook configuration")
  return config


def _message(config: dict, key: str, **values: str) -> str:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  messages = config["messages"]
  language = language if language in messages else config["default_language"]
  return messages[language][key].format(**values)


def _run(path: Path, arguments: list[str], config: dict) -> None:
  is_python = path.suffix == config["python_suffix"]
  interpreter = config["interpreters"]["python"] if is_python else config["interpreters"]["shell"]
  options = config["python_options"] if is_python else []
  try:
    status = subprocess.run([interpreter, *options, str(path), *arguments], check=False).returncode
  except OSError:
    status = config["exit_codes"]["hook_failed"]
  if status != 0:
    print(_message(config, "hook_failed", hook=path), file=sys.stderr)


def run_main() -> int:
  config = _config()
  if len(sys.argv) < 2:
    print(_message(config, "usage"), file=sys.stderr)
    return config["exit_codes"]["usage"]

  name, *arguments = sys.argv[1:]
  if not name or "/" in name or name in config["invalid_names"]:
    print(_message(config, "invalid_hook_name", name=name), file=sys.stderr)
    return config["exit_codes"]["invalid_name"]

  hooks = Path.home() / config["hooks_directory"]
  hook = hooks / name
  directory = hooks / f"{name}{config['collection_suffix']}"
  if hook.is_file():
    _run(hook, arguments, config)

  if directory.is_dir():
    for entry in sorted(directory.iterdir()):
      if (
        not entry.name.startswith(config["hidden_prefix"])
        and not entry.name.endswith(config["sample_suffix"])
        and entry.is_file()
      ):
        _run(entry, arguments, config)
  return 0
