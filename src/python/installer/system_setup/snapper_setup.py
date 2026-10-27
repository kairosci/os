from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  arch_path = Path(os.environ["ARCH_PATH"])
  with (arch_path / "data/installer/snapper-setup.yml").open(encoding="utf-8") as stream:
    settings = yaml.safe_load(stream)
  if not isinstance(settings, dict):
    raise ValueError("invalid Snapper setup settings")
  return settings["snapper"]


def _path(settings: dict[str, Any], key: str) -> Path:
  value = settings["paths"][key]
  override = os.environ.get(value["environment_override"])
  if override:
    return Path(override)
  if key == "template":
    return Path(os.environ["ARCH_PATH"]) / value["default"]
  return Path(value["default"])


def _atomic_write(path: Path, content: bytes, mode: int, directory_mode: str) -> None:
  path.parent.mkdir(mode=int(directory_mode, 8), parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "wb") as stream:
      stream.write(content)
      stream.flush()
      os.fsync(stream.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def _create_config_if_missing(config_path: Path, settings: dict[str, Any]) -> None:
  if config_path.is_file():
    return
  config_path.parent.mkdir(mode=int(settings["directory_mode"], 8), parents=True, exist_ok=True)
  test = settings["test_mode"]
  if os.environ.get(test["environment_variable"], test["disabled_value"]) == test["enabled_value"]:
    _atomic_write(config_path, b"", int(settings["file_mode"], 8), settings["directory_mode"])
    return

  primary = subprocess.run(settings["commands"]["create_config_primary"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  if primary.returncode:
    subprocess.run(settings["commands"]["create_config_fallback"], check=True, stdout=subprocess.DEVNULL)


def _run_optional(commands: list[list[str]]) -> None:
  for command in commands:
    subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
  settings = _settings()
  config_path = _path(settings, "config")
  conf_path = _path(settings, "conf")
  template_path = _path(settings, "template")
  _create_config_if_missing(config_path, settings)
  _atomic_write(config_path, template_path.read_bytes(), int(settings["file_mode"], 8), settings["directory_mode"])
  _atomic_write(conf_path, settings["config_file_contents"].encode(), int(settings["file_mode"], 8), settings["directory_mode"])
  _run_optional(settings["commands"]["disable_timeline"])
  _run_optional(settings["commands"]["enable_cleanup"])
  _run_optional(settings["commands"]["disable_legacy_snapshot_sync"])


if __name__ == "__main__":
  main()
