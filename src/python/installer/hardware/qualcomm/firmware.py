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
  if destination.is_file() and destination.read_text(encoding="utf-8") == content:
    return
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


def _run(command: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
  try:
    return subprocess.run(command, check=False, capture_output=capture_output, text=True)
  except OSError:
    return subprocess.CompletedProcess(command, 127, "", "")


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["qualcomm_firmware_setup"]
  if _run(settings["platform_check"]).returncode:
    return 0

  result = _run([*settings["package_command"], *settings["packages"]])
  if result.returncode:
    return result.returncode
  _run(settings["install_command"])

  root_result = _run(settings["root_source_command"], capture_output=True)
  root_source = root_result.stdout.strip() if root_result.returncode == 0 else ""
  usb_root = False
  if root_source:
    transport = _run([*settings["root_transport_command"], root_source], capture_output=True)
    usb_root = transport.returncode == 0 and re.search(
      settings["usb_transport_pattern"], transport.stdout, flags=re.MULTILINE
    ) is not None

  disable_dsp = usb_root
  if not disable_dsp:
    inspection = _run(settings["missing_firmware_command"], capture_output=True)
    disable_dsp = (
      settings["inspection_failure_disables_dsp"] and inspection.returncode != 0
    ) or re.search(settings["adsp_missing_pattern"], inspection.stdout, flags=re.IGNORECASE) is not None

  directory = Path(os.environ.get(settings["directory_environment"]) or settings["directory_default"])
  destination = directory / settings["filename"]
  if disable_dsp:
    content_key = "usb_blacklist_content" if usb_root else "missing_blacklist_content"
    _write_atomically(destination, settings[content_key] + "\n", int(settings["mode"], 8))
  elif destination.exists() or destination.is_symlink():
    destination.unlink()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
