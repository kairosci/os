from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from string import Template
from typing import Any
from urllib.parse import urlsplit

import yaml


class InvalidLauncherName(ValueError):
  pass


class EmptyLauncherValues(ValueError):
  pass


class IconDownloadFailed(RuntimeError):
  pass


def _settings() -> dict[str, Any]:
  arch_path = Path(os.environ["ARCH_PATH"])
  with (arch_path / "data/cli/tui-install.yml").open(encoding="utf-8") as stream:
    value = yaml.safe_load(stream)
  if not isinstance(value, dict):
    raise ValueError("invalid TUI installer settings")
  return value


def _translator(settings: dict[str, Any]):
  def translate(key: str, *arguments: str) -> str:
    arch_path = Path(os.environ["ARCH_PATH"])
    command = [str(arch_path / settings["commands"]["i18n"]), key, *arguments]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else key

  return translate


def _gum_environment(settings: dict[str, Any]) -> dict[str, str]:
  env = os.environ.copy()
  theme_file = Path.home() / settings["theme"]["environment_file"]
  try:
    source = theme_file.read_text(encoding="utf-8")
  except FileNotFoundError:
    return env
  for key, value in re.findall(settings["theme"]["environment_pattern"], source):
    env[key] = value
  return env


def _gum(settings: dict[str, Any], arguments: list[str]) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [settings["commands"]["gum"], *arguments],
    check=False,
    capture_output=True,
    text=True,
    env=_gum_environment(settings),
  )


def _input(settings: dict[str, Any], prompt: str, placeholder: str) -> str:
  result = _gum(
    settings,
    [
      *settings["gum"]["input_arguments"],
      prompt,
      settings["gum"]["placeholder_argument"],
      placeholder,
    ],
  )
  if result.returncode:
    raise KeyboardInterrupt
  return result.stdout.rstrip("\n")


def _slug(value: str, settings: dict[str, Any]) -> str:
  policy = settings["names"]
  result = re.sub(policy["invalid_pattern"], policy["separator"], value.lower()).strip(policy["separator"])
  result = result[: int(policy["maximum_length"])].rstrip(policy["separator"])
  if not result:
    raise InvalidLauncherName
  return result


def _under(root: Path, relative: str) -> Path:
  candidate = root.joinpath(*Path(relative).parts)
  candidate.mkdir(parents=True, exist_ok=True)
  resolved = candidate.resolve(strict=True)
  if resolved != root and root not in resolved.parents:
    raise ValueError("launcher data directory leaves its configured root")
  return resolved


def _escape_string(value: str) -> str:
  return value.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")


def _escape_exec_argument(value: str) -> str:
  if any(ord(character) < 32 or ord(character) == 127 for character in value):
    raise ValueError("control characters are not valid in desktop commands")
  value = value.replace("%", "%%")
  exec_escaped = "".join("\\" + character if character in '\\"$`' else character for character in value)
  return _escape_string(f'"{exec_escaped}"')


def _exec_value(command: str, settings: dict[str, Any]) -> str:
  arguments = shlex.split(command)
  if not arguments:
    raise ValueError("empty launcher command")
  app_id_argument = settings["desktop"]["app_id_argument"].format(app_id=settings["desktop"]["app_id"])
  fixed = [
    settings["commands"]["terminal_launcher"],
    app_id_argument,
    *settings["desktop"]["execute_arguments"],
  ]
  return " ".join(_escape_exec_argument(argument) for argument in [*fixed, *arguments])


def _atomic_write(path: Path, content: str, mode: int) -> None:
  descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
      stream.write(content)
      stream.flush()
      os.fsync(stream.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, path)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def _icon_cache(settings: dict[str, Any], directory: Path) -> None:
  subprocess.run(
    [settings["commands"]["icon_cache"], *settings["icons"]["cache_arguments"], str(directory)],
    check=False,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )


def _install_icon(reference: str, slug: str, settings: dict[str, Any], data_root: Path) -> str:
  icon_directory = _under(data_root, settings["paths"]["icons_directory"])
  if reference.startswith(tuple(settings["icons"]["schemes"])):
    parsed = urlsplit(reference)
    if parsed.scheme not in settings["icons"]["schemes"] or not parsed.netloc:
      raise ValueError("invalid icon URL")
    suffix = settings["icons"]["download_extension"]
    icon_name = f"{slug}.{suffix}"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{slug}-", dir=icon_directory)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
      result = subprocess.run(
        [
          settings["commands"]["curl"],
          *[
            argument.format(
              maximum_bytes=settings["icons"]["maximum_bytes"],
              timeout_seconds=settings["icons"]["timeout_seconds"],
            )
            for argument in settings["icons"]["download_arguments"]
          ],
          str(temporary),
          reference,
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
      )
      if result.returncode:
        raise IconDownloadFailed
      if temporary.stat().st_size > int(settings["icons"]["maximum_bytes"]):
        raise IconDownloadFailed
      os.chmod(temporary, int(settings["icons"]["mode"], 8))
      os.replace(temporary, icon_directory / icon_name)
    except BaseException:
      temporary.unlink(missing_ok=True)
      raise
    _icon_cache(settings, _under(data_root, settings["paths"]["icon_theme_directory"]))
    return slug

  source = Path(reference)
  if source.is_file():
    suffix = source.suffix.lstrip(".").lower() or settings["icons"]["download_extension"]
    if suffix not in settings["icons"]["allowed_extensions"]:
      raise ValueError("unsupported icon file type")
    icon_name = f"{slug}.{suffix}"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{slug}-", dir=icon_directory)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
      shutil.copyfile(source, temporary)
      os.chmod(temporary, int(settings["icons"]["mode"], 8))
      os.replace(temporary, icon_directory / icon_name)
    except BaseException:
      temporary.unlink(missing_ok=True)
      raise
    _icon_cache(settings, _under(data_root, settings["paths"]["icon_theme_directory"]))
    return slug

  if not re.fullmatch(settings["icons"]["name_pattern"], reference):
    raise ValueError("invalid icon name")
  return reference


def _desktop_entry(name: str, command: str, icon: str, settings: dict[str, Any]) -> str:
  values = {
    "version": settings["desktop"]["version"],
    "name": _escape_string(name),
    "comment": _escape_string(name),
    "exec": _exec_value(command, settings),
    "icon": _escape_string(icon),
    "type": settings["desktop"]["type"],
    "terminal": str(settings["desktop"]["terminal"]).lower(),
    "startup_notify": str(settings["desktop"]["startup_notify"]).lower(),
  }
  template = Template(settings["desktop"]["template"])
  return template.substitute(values)


def _create(name: str, command: str, icon_reference: str, settings: dict[str, Any]) -> None:
  if not name.strip() or not command.strip() or not icon_reference.strip():
    raise EmptyLauncherValues
  slug = _slug(name, settings)
  data_home_value = os.environ.get("XDG_DATA_HOME")
  data_home = Path(data_home_value) if data_home_value else Path.home() / settings["paths"]["default_data_directory"]
  if not data_home.is_absolute():
    raise ValueError("XDG_DATA_HOME must be absolute")
  data_root = data_home.resolve()
  data_root.mkdir(parents=True, exist_ok=True)
  data_root = data_root.resolve(strict=True)
  applications = _under(data_root, settings["paths"]["applications_directory"])
  icon = _install_icon(icon_reference, slug, settings, data_root)
  desktop_path = applications / f"{slug}{settings['paths']['desktop_extension']}"
  content = _desktop_entry(name, command, icon, settings)
  _atomic_write(desktop_path, content, int(settings["files"]["mode"], 8))


def main() -> int:
  settings = _settings()
  _message = _translator(settings)
  arguments = sys.argv[1:]
  if arguments:
    if len(arguments) != int(settings["arguments"]["count"]):
      print(_message("tui.usage"), file=sys.stderr)
      return 2
    name, command, icon_reference = arguments
  else:
    print(_message("tui.intro"))
    try:
      name = _input(settings, _message("tui.namePrompt"), _message("tui.namePlaceholder"))
      command = _input(
        settings,
        _message("tui.commandPrompt"),
        _message("tui.commandPlaceholder", *settings["examples"]["command_placeholder_arguments"]),
      )
      icon_reference = _input(
        settings,
        _message("tui.iconPrompt"),
        _message("tui.iconPlaceholder", settings["examples"]["icon_url"]),
      )
    except KeyboardInterrupt:
      return settings["exit_codes"]["cancelled"]

  try:
    _create(name, command, icon_reference, settings)
  except IconDownloadFailed:
    print(_message("tui.iconDownloadFailed"), file=sys.stderr)
    return 1
  except EmptyLauncherValues:
    print(_message("tui.requiredValues"), file=sys.stderr)
    return 1
  except InvalidLauncherName:
    print(_message("tui.invalidName"), file=sys.stderr)
    return 1
  except (OSError, ValueError, RuntimeError):
    print(_message("tui.failed"), file=sys.stderr)
    return 1

  if not arguments:
    print(_message("tui.created", name))
  return 0
