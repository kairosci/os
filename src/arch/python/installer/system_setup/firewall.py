from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  ap = Path(os.environ["ARCH_PATH"])
  with (ap / "data/installer/firewall-setup.yml").open(encoding="utf-8") as stream:
    settings = yaml.safe_load(stream)
  if not isinstance(settings, dict):
    raise ValueError("invalid firewall setup settings")
  return settings["firewall"]


def _install_docker_rules(settings: dict[str, Any]) -> None:
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


def _set_enabled(settings: dict[str, Any]) -> None:
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


def main() -> None:
  settings = _settings()
  for command in settings["rules"]:
    subprocess.run(command, check=True)
  _install_docker_rules(settings)
  _set_enabled(settings)
  subprocess.run(settings["enable_command"], check=True)


if __name__ == "__main__":
  main()
