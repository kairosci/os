from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import sys
from typing import TypedDict

import yaml


class ExitCodes(TypedDict):
  usage: int
  invalid_name: int
  hook_failed: int
  file_missing: int
  install_failed: int


class InstallConfig(TypedDict):
  temporary_prefix: str
  mode: str


class HookConfig(TypedDict):
  default_language: str
  hooks_directory: str
  collection_suffix: str
  sample_suffix: str
  hidden_prefix: str
  python_suffix: str
  invalid_names: list[str]
  python_interpreter: str
  shell_interpreter: str
  python_options: list[str]
  install_arguments: int
  install: InstallConfig
  exit_codes: ExitCodes
  messages: dict[str, dict[str, str]]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid hook configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid hook configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid hook configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid hook configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _config() -> HookConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hooks.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  interpreters = _mapping(config.get("interpreters"), "interpreters")
  arguments = _mapping(config.get("argument_counts"), "argument_counts")
  install = _mapping(config.get("install"), "install")
  codes = _mapping(config.get("exit_codes"), "exit_codes")
  raw_messages = _mapping(config.get("messages"), "messages")
  messages: dict[str, dict[str, str]] = {}
  for language, raw_table in raw_messages.items():
    locale = _text(language, "messages language")
    table = _mapping(raw_table, f"messages.{locale}")
    messages[locale] = {
      _text(key, f"messages.{locale} key"): _text(value, f"messages.{locale} value")
      for key, value in table.items()
    }
  return {
    "default_language": _text(config.get("default_language"), "default_language"),
    "hooks_directory": _text(config.get("hooks_directory"), "hooks_directory"),
    "collection_suffix": _text(config.get("collection_suffix"), "collection_suffix"),
    "sample_suffix": _text(config.get("sample_suffix"), "sample_suffix"),
    "hidden_prefix": _text(config.get("hidden_prefix"), "hidden_prefix"),
    "python_suffix": _text(config.get("python_suffix"), "python_suffix"),
    "invalid_names": _text_list(config.get("invalid_names"), "invalid_names"),
    "python_interpreter": _text(interpreters.get("python"), "interpreters.python"),
    "shell_interpreter": _text(interpreters.get("shell"), "interpreters.shell"),
    "python_options": _text_list(config.get("python_options"), "python_options"),
    "install_arguments": _integer(arguments.get("install"), "argument_counts.install"),
    "install": {
      "temporary_prefix": _text(install.get("temporary_prefix"), "install.temporary_prefix"),
      "mode": _text(install.get("mode"), "install.mode"),
    },
    "exit_codes": {
      "usage": _integer(codes.get("usage"), "exit_codes.usage"),
      "invalid_name": _integer(codes.get("invalid_name"), "exit_codes.invalid_name"),
      "hook_failed": _integer(codes.get("hook_failed"), "exit_codes.hook_failed"),
      "file_missing": _integer(codes.get("file_missing"), "exit_codes.file_missing"),
      "install_failed": _integer(codes.get("install_failed"), "exit_codes.install_failed"),
    },
    "messages": messages,
  }


def _message(config: HookConfig, key: str, **values: str) -> str:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  messages = config["messages"]
  selected_language = language if language in messages else config["default_language"]
  return messages[selected_language][key].format(**values)


def _run(path: Path, arguments: list[str], config: HookConfig) -> None:
  is_python = path.suffix == config["python_suffix"]
  interpreter = config["python_interpreter"] if is_python else config["shell_interpreter"]
  options = config["python_options"] if is_python else []
  try:
    status = subprocess.run([interpreter, *options, str(path), *arguments], check=False).returncode
  except OSError:
    status = config["exit_codes"]["hook_failed"]
  if status != 0:
    print(_message(config, "hook_failed", hook=str(path)), file=sys.stderr)


def _load_config() -> HookConfig | None:
  try:
    return _config()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load hook configuration: {error}", file=sys.stderr)
    return None


def run_main() -> int:
  config = _load_config()
  if config is None:
    return 1
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
  config = _load_config()
  if config is None:
    return 1
  install = config["install"]
  if len(sys.argv) != config["install_arguments"]:
    print(_message(config, "install_usage"), file=sys.stderr)
    return config["exit_codes"]["usage"]

  hook_type, source_name = sys.argv[1:]
  if not hook_type or "/" in hook_type or hook_type in config["invalid_names"]:
    print(_message(config, "invalid_hook_name", name=hook_type), file=sys.stderr)
    return config["exit_codes"]["invalid_name"]

  source = Path(source_name)
  if not source.is_file():
    print(_message(config, "hook_file_missing", file=str(source)), file=sys.stderr)
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
    print(_message(config, "hook_install_failed", path=str(destination)), file=sys.stderr)
    return config["exit_codes"]["install_failed"]
  finally:
    if temporary is not None:
      temporary.unlink(missing_ok=True)

  print(_message(config, "hook_installed", hook_type=hook_type, path=str(destination)))
  return 0
