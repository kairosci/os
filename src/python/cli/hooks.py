from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
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


def install_main() -> int:
  config = _config()
  install = config["install"]
  if len(sys.argv) != config["argument_counts"]["install"]:
    print(_message(config, "install_usage"), file=sys.stderr)
    return config["exit_codes"]["usage"]

  hook_type, source_name = sys.argv[1:]
  if not hook_type or "/" in hook_type or hook_type in config["invalid_names"]:
    print(_message(config, "invalid_hook_name", name=hook_type), file=sys.stderr)
    return config["exit_codes"]["invalid_name"]

  source = Path(source_name)
  if not source.is_file():
    print(_message(config, "hook_file_missing", file=source), file=sys.stderr)
    return config["exit_codes"]["file_missing"]

  directory = Path.home() / config["hooks_directory"] / f"{hook_type}{config['collection_suffix']}"
  destination = directory / source.name
  temporary = None
  try:
    directory.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as input_file:
      descriptor, temporary_name = tempfile.mkstemp(prefix=install["temporary_prefix"], dir=directory)
      temporary = Path(temporary_name)
      with os.fdopen(descriptor, "wb") as output_file:
        shutil.copyfileobj(input_file, output_file)
        output_file.flush()
        os.fchmod(output_file.fileno(), int(install["mode"], 8))
        os.fsync(output_file.fileno())
    os.replace(temporary, destination)
    temporary = None
  except OSError:
    print(_message(config, "hook_install_failed", path=destination), file=sys.stderr)
    return config["exit_codes"]["install_failed"]
  finally:
    if temporary is not None:
      temporary.unlink(missing_ok=True)

  print(_message(config, "hook_installed", hook_type=hook_type, path=destination))
  return 0
