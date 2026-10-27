from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path

import yaml


def _write_atomically(destination: Path, content: str, default_mode: int) -> None:
  if destination.is_symlink():
    destination = destination.resolve(strict=True)
  mode = stat.S_IMODE(destination.stat().st_mode) if destination.is_file() else default_mode
  destination.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary = tempfile.mkstemp(dir=destination.parent)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(content)
      output.flush()
      os.fsync(output.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, destination)
    directory_fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  finally:
    Path(temporary).unlink(missing_ok=True)


def _message(settings: dict[str, object], key: str) -> str:
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  messages = settings["messages"].get(language, settings["messages"]["en"])
  return messages[key].format(support_url=settings["support_url"])


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["nvidia_driver_setup"]
  if subprocess.run(settings["n1x_check"], check=False).returncode == 0:
    print(_message(settings, "n1x"))
    return 0

  try:
    pci = subprocess.run(settings["pci_command"], check=False, stdout=subprocess.PIPE, text=True)
  except OSError:
    return 0
  if re.search(settings["pci_pattern"], pci.stdout, flags=re.IGNORECASE) is None:
    return 0

  if subprocess.run(settings["gsp_check"], check=False).returncode == 0:
    packages = list(settings["gsp_packages"])
    if subprocess.run(settings["x86_check"], check=False).returncode == 0:
      packages.extend(settings["gsp_x86_packages"])
    packages.extend(settings["gsp_common_packages"])
  elif subprocess.run(settings["legacy_check"], check=False).returncode == 0:
    packages = list(settings["legacy_packages"])
    if subprocess.run(settings["x86_check"], check=False).returncode == 0:
      packages.extend(settings["legacy_x86_packages"])
  else:
    print(_message(settings, "unsupported"))
    return 0

  result = subprocess.run([*settings["package_command"], *packages], check=False)
  if result.returncode:
    return result.returncode

  system_root = Path(os.environ.get(settings["system_root_environment"]) or "/").resolve()
  for file_settings in settings["config_files"]:
    destination = system_root / file_settings["path"]
    _write_atomically(destination, file_settings["content"] + "\n", int(file_settings["mode"], 8))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
