from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal, NotRequired, TypedDict

import yaml


class PathSetting(TypedDict):
  environment_override: str
  default: NotRequired[str]
  relative_default: NotRequired[str]


class Paths(TypedDict):
  hardware_helper: PathSetting
  systemd_boot_esp: PathSetting
  systemd_boot_entry: str
  kernel_cmdline: PathSetting
  kernel_uki: PathSetting
  mkinitcpio_config_dir: PathSetting
  preset_template: PathSetting
  default_preset: PathSetting


class Commands(TypedDict):
  objcopy: list[str]


class Files(TypedDict):
  kernel_preset: str
  preset_package_base: str
  preset_package_name: str
  installed_mode: str
  legacy_preset: str


class Messages(TypedDict):
  missing_uki: str
  objcopy_failed: str
  missing_root: str
  custom_preset: str
  configured: str


class Settings(TypedDict):
  paths: Paths
  commands: Commands
  files: Files
  messages: dict[str, Messages]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid systemd-boot kernel setup settings: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid systemd-boot kernel setup settings: {label} must be a string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value:
    raise TypeError(f"invalid systemd-boot kernel setup settings: {label} must be a non-empty list")
  return [_text(item, f"{label} item") for item in value]


def _path_setting(value: object, label: str) -> PathSetting:
  raw = _mapping(value, label)
  parsed: PathSetting = {"environment_override": _text(raw.get("environment_override"), f"{label}.environment_override")}
  if "default" in raw:
    parsed["default"] = _text(raw.get("default"), f"{label}.default")
  if "relative_default" in raw:
    parsed["relative_default"] = _text(raw.get("relative_default"), f"{label}.relative_default")
  if "default" not in parsed and "relative_default" not in parsed:
    raise ValueError(f"invalid systemd-boot kernel setup settings: {label} needs a default path")
  return parsed


def _messages_by_language(value: object) -> dict[str, Messages]:
  raw = _mapping(value, "messages")
  messages: dict[str, Messages] = {}
  for language, raw_messages in raw.items():
    key = _text(language, "messages language")
    entry = _mapping(raw_messages, f"messages.{key}")
    messages[key] = {
      "missing_uki": _text(entry.get("missing_uki"), f"messages.{key}.missing_uki"),
      "objcopy_failed": _text(entry.get("objcopy_failed"), f"messages.{key}.objcopy_failed"),
      "missing_root": _text(entry.get("missing_root"), f"messages.{key}.missing_root"),
      "custom_preset": _text(entry.get("custom_preset"), f"messages.{key}.custom_preset"),
      "configured": _text(entry.get("configured"), f"messages.{key}.configured"),
    }
  if "en" not in messages:
    raise ValueError("invalid systemd-boot kernel setup settings: English messages are required")
  return messages


def _settings() -> tuple[Path, Settings]:
  ap = Path(os.environ["AP"])
  with (ap / "data/installer/systemd-boot-kernel.yml").open(encoding="utf-8") as stream:
    raw: object = yaml.safe_load(stream)
  document = _mapping(raw, "root")
  settings = _mapping(document.get("systemd_boot_kernel"), "systemd_boot_kernel")
  paths = _mapping(settings.get("paths"), "paths")
  commands = _mapping(settings.get("commands"), "commands")
  files = _mapping(settings.get("files"), "files")
  return ap, {
    "paths": {
      "hardware_helper": _path_setting(paths.get("hardware_helper"), "paths.hardware_helper"),
      "systemd_boot_esp": _path_setting(paths.get("systemd_boot_esp"), "paths.systemd_boot_esp"),
      "systemd_boot_entry": _text(paths.get("systemd_boot_entry"), "paths.systemd_boot_entry"),
      "kernel_cmdline": _path_setting(paths.get("kernel_cmdline"), "paths.kernel_cmdline"),
      "kernel_uki": _path_setting(paths.get("kernel_uki"), "paths.kernel_uki"),
      "mkinitcpio_config_dir": _path_setting(paths.get("mkinitcpio_config_dir"), "paths.mkinitcpio_config_dir"),
      "preset_template": _path_setting(paths.get("preset_template"), "paths.preset_template"),
      "default_preset": _path_setting(paths.get("default_preset"), "paths.default_preset"),
    },
    "commands": {"objcopy": _text_list(commands.get("objcopy"), "commands.objcopy")},
    "files": {
      "kernel_preset": _text(files.get("kernel_preset"), "files.kernel_preset"),
      "preset_package_base": _text(files.get("preset_package_base"), "files.preset_package_base"),
      "preset_package_name": _text(files.get("preset_package_name"), "files.preset_package_name"),
      "installed_mode": _text(files.get("installed_mode"), "files.installed_mode"),
      "legacy_preset": _text(files.get("legacy_preset"), "files.legacy_preset"),
    },
    "messages": _messages_by_language(settings.get("messages")),
  }


def _messages(settings: Settings) -> Messages:
  language = os.environ.get("LC_MESSAGES", os.environ.get("LANG", "en")).split("_", 1)[0].lower()
  return settings["messages"].get(language, settings["messages"]["en"])


def _configured_path(
  settings: Settings, key: Literal[
    "hardware_helper", "systemd_boot_esp", "kernel_cmdline", "kernel_uki",
    "mkinitcpio_config_dir", "preset_template", "default_preset",
  ], ap: Path, relative_base: Path | None = None,
) -> Path:
  config = settings["paths"][key]
  override = os.environ.get(config["environment_override"])
  if override is not None and override != "":
    return Path(override)
  default = config.get("default")
  if default is not None:
    return Path(default)
  base = relative_base if relative_base is not None else ap
  relative_default = config.get("relative_default")
  if relative_default is None:
    raise ValueError(f"missing relative default for configured path {key}")
  return base / relative_default


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
  settings: Settings, ap: Path, messages: Messages, preset_path: Path, template_path: Path,
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
  settings: Settings, messages: Messages, uki: Path, command_line_file: Path,
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
  try:
    ap, settings = _settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load systemd-boot kernel settings: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
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
  except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as error:
    print(f"Could not configure systemd-boot kernel: {error}", file=sys.stderr)
    return os.EX_SOFTWARE
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
