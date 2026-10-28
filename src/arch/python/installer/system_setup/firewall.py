from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

import yaml


class DockerSettings(TypedDict):
  executable: str
  install_arguments: list[str]
  path_pattern: str
  search_path: list[str]
  status_command: list[str]
  active_status: str
  executable_command: list[str]


class FirewallConfig(TypedDict):
  path: str
  environment_override: str
  enabled_pattern: str
  enabled_replacement: str


class Settings(TypedDict):
  rules: list[list[str]]
  docker: DockerSettings
  configuration: FirewallConfig
  enable_command: list[str]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid firewall setup settings: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid firewall setup settings: {label} must be a string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value:
    raise TypeError(f"invalid firewall setup settings: {label} must be a non-empty list")
  return [_text(item, f"{label} item") for item in value]


def _command_groups(value: object, label: str) -> list[list[str]]:
  if not isinstance(value, list):
    raise TypeError(f"invalid firewall setup settings: {label} must be a list")
  return [_text_list(command, f"{label} item") for command in value]


def _pattern(value: object, label: str) -> str:
  pattern = _text(value, label)
  try:
    re.compile(pattern)
  except re.error as error:
    raise ValueError(f"invalid firewall setup settings: {label} is not a valid pattern") from error
  return pattern


def _settings() -> Settings:
  ap = Path(os.environ["AP"])
  with (ap / "data/installer/firewall-setup.yml").open(encoding="utf-8") as stream:
    raw: object = yaml.safe_load(stream)
  root = _mapping(raw, "configuration")
  firewall = _mapping(root.get("firewall"), "firewall")
  docker = _mapping(firewall.get("docker"), "docker")
  config = _mapping(firewall.get("configuration"), "configuration")
  return {
    "rules": _command_groups(firewall.get("rules"), "rules"),
    "docker": {
      "executable": _text(docker.get("executable"), "docker.executable"),
      "install_arguments": _text_list(docker.get("install_arguments"), "docker.install_arguments"),
      "path_pattern": _pattern(docker.get("path_pattern"), "docker.path_pattern"),
      "search_path": _text_list(docker.get("search_path"), "docker.search_path"),
      "status_command": _text_list(docker.get("status_command"), "docker.status_command"),
      "active_status": _text(docker.get("active_status"), "docker.active_status"),
      "executable_command": _text_list(docker.get("executable_command"), "docker.executable_command"),
    },
    "configuration": {
      "path": _text(config.get("path"), "configuration.path"),
      "environment_override": _text(config.get("environment_override"), "configuration.environment_override"),
      "enabled_pattern": _pattern(config.get("enabled_pattern"), "configuration.enabled_pattern"),
      "enabled_replacement": _text(config.get("enabled_replacement"), "configuration.enabled_replacement"),
    },
    "enable_command": _text_list(firewall.get("enable_command"), "enable_command"),
  }


def _install_docker_rules(settings: Settings) -> None:
  docker = settings["docker"]
  executable = shutil.which(docker["executable"])
  if executable is None:
    raise FileNotFoundError(docker["executable"])
  original = Path(executable).read_text(encoding="utf-8")
  with tempfile.TemporaryDirectory(prefix="arch-firewall-") as temporary:
    directory = Path(temporary)
    path_pattern = re.compile(docker["path_pattern"], re.MULTILINE)
    replacement_path = os.pathsep.join([str(directory), *docker["search_path"]])
    updated, count = path_pattern.subn(f'PATH="{replacement_path}"', original, count=1)
    if count != 1:
      raise ValueError("ufw-docker PATH assignment was not found")

    ufw_shim = directory / "ufw"
    ufw_command = shlex.join(docker["executable_command"])
    status_arguments = shlex.quote(" ".join(docker["status_command"][1:]))
    active_status = shlex.quote(docker["active_status"])
    ufw_shim.write_text(
      "#!/bin/bash\n"
      f"if [[ $* == {status_arguments} ]]; then\n"
      f"  echo {active_status}\n"
      "  exit 0\n"
      "fi\n"
      f"exec {ufw_command} \"$@\"\n",
      encoding="utf-8",
    )
    ufw_shim.chmod(0o755)
    docker_shim = directory / docker["executable"]
    docker_shim.write_text(updated, encoding="utf-8")
    docker_shim.chmod(0o755)
    subprocess.run([str(docker_shim), *docker["install_arguments"]], check=True)


def _set_enabled(settings: Settings) -> None:
  config = settings["configuration"]
  path = Path(os.environ.get(config["environment_override"], config["path"]))
  content = path.read_text(encoding="utf-8")
  updated, _ = re.subn(config["enabled_pattern"], config["enabled_replacement"], content, count=1, flags=re.MULTILINE)
  if updated == content:
    return
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
      stream.write(updated)
      stream.flush()
      os.fsync(stream.fileno())
    shutil.copystat(path, temporary, follow_symlinks=False)
    os.replace(temporary, path)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def main() -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load firewall setup configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    for command in settings["rules"]:
      subprocess.run(command, check=True)
    _install_docker_rules(settings)
    _set_enabled(settings)
    subprocess.run(settings["enable_command"], check=True)
  except subprocess.CalledProcessError as error:
    print(f"Firewall setup command failed: {error}", file=sys.stderr)
    return error.returncode
  except (OSError, ValueError, subprocess.SubprocessError) as error:
    print(f"Could not apply firewall setup: {error}", file=sys.stderr)
    return os.EX_SOFTWARE
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
