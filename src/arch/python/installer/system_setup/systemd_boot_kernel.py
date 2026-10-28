from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


def _settings() -> tuple[Path, dict[str, Any]]:
  ap = Path(os.environ["ARCH_PATH"])
  with (ap / "data/installer/systemd-boot-kernel.yml").open(encoding="utf-8") as stream:
    document = yaml.safe_load(stream)
  if not isinstance(document, dict):
    raise ValueError("invalid systemd-boot kernel setup settings")
  return ap, document["systemd_boot_kernel"]


def _messages(settings: dict[str, Any]) -> dict[str, str]:
  language = os.environ.get("LC_MESSAGES", os.environ.get("LANG", "en")).split("_", 1)[0].lower()
  return settings["messages"].get(language, settings["messages"]["en"])


def _configured_path(
  settings: dict[str, Any], key: str, ap: Path, relative_base: Path | None = None,
) -> Path:
  config = settings["paths"][key]
  override = os.environ.get(config["environment_override"])
  if override:
    return Path(override)
  if "default" in config:
    return Path(config["default"])
  base = relative_base if relative_base is not None else ap
  return base / config["relative_default"]


def _atomic_write(path: Path, content: bytes, mode: int) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
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


def _write_preset_if_safe(
  settings: dict[str, Any], ap: Path, messages: dict[str, str], preset_path: Path, template_path: Path,
) -> bool:
  files = settings["files"]
  template = template_path.read_bytes()
  if preset_path.exists() and preset_path.read_bytes() != template:
    known_presets = [files["legacy_preset"].encode() + b"\n"]
    default_preset = _configured_path(settings, "default_preset", ap)
    if default_preset.is_file():
      default_content = default_preset.read_text(encoding="utf-8")
      known_presets.append(
        default_content.replace(files["preset_package_base"], files["preset_package_name"]).encode()
      )
    if not any(preset_path.read_bytes() == known for known in known_presets):
      print(messages["custom_preset"].format(path=preset_path), file=sys.stderr)
      return False
  _atomic_write(preset_path, template, int(files["installed_mode"], 8))
  return True


def _merged_command_line(
  settings: dict[str, Any], messages: dict[str, str], uki: Path, command_line_file: Path,
) -> bytes | None:
  with tempfile.TemporaryDirectory(prefix="arch-kernel-cmdline-") as temporary:
    embedded_file = Path(temporary) / "cmdline"
    result = subprocess.run(
      [*settings["commands"]["objcopy"], str(uki), str(embedded_file)],
      check=False,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
    )
    if result.returncode:
      print(messages["objcopy_failed"].format(path=uki), file=sys.stderr)
      return None
    embedded = embedded_file.read_bytes().replace(b"\0", b"").decode("utf-8").split()

  existing = command_line_file.read_text(encoding="utf-8").splitlines()[0].split() if command_line_file.is_file() else []
  arguments = list(existing)
  keys = {argument.split("=", 1)[0] for argument in existing if "=" in argument}
  flags = {argument for argument in existing if "=" not in argument}
  for argument in embedded:
    if "=" in argument:
      key = argument.split("=", 1)[0]
      if key in keys:
        continue
      keys.add(key)
    else:
      if argument in flags:
        continue
      flags.add(argument)
    arguments.append(argument)

  if not any(re.match(r"^root=", argument) for argument in arguments):
    print(messages["missing_root"].format(uki=uki, cmdline=command_line_file), file=sys.stderr)
    return None
  return (" ".join(arguments) + "\n").encode()


def main() -> int:
  ap, settings = _settings()
  paths = settings["paths"]
  helper = _configured_path(settings, "hardware_helper", ap)
  if subprocess.run([str(helper)], check=False).returncode:
    return 0

  esp = _configured_path(settings, "systemd_boot_esp", ap)
  if not (esp / paths["systemd_boot_entry"]).is_file():
    return 0

  uki = _configured_path(settings, "kernel_uki", ap, esp)
  messages = _messages(settings)
  if not uki.is_file() or not uki.stat().st_size:
    print(messages["missing_uki"].format(path=uki), file=sys.stderr)
    return 1

  command_line_file = _configured_path(settings, "kernel_cmdline", ap)
  command_line = _merged_command_line(settings, messages, uki, command_line_file)
  if command_line is None:
    return 1

  mkinitcpio_dir = _configured_path(settings, "mkinitcpio_config_dir", ap)
  preset_path = mkinitcpio_dir / settings["files"]["kernel_preset"]
  template_path = _configured_path(settings, "preset_template", ap)
  if not _write_preset_if_safe(settings, ap, messages, preset_path, template_path):
    return 1

  _atomic_write(command_line_file, command_line, int(settings["files"]["installed_mode"], 8))
  print(messages["configured"])
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
