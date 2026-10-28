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
from typing import Protocol, TypedDict
from urllib.parse import urlsplit

import yaml


class InvalidLauncherName(ValueError):
  pass


class EmptyLauncherValues(ValueError):
  pass


class IconDownloadFailed(RuntimeError):
  pass


class Commands(TypedDict):
  i18n: str
  gum: str
  terminal_launcher: str
  curl: str
  icon_cache: str


class Gum(TypedDict):
  input_arguments: list[str]
  placeholder_argument: str


class Theme(TypedDict):
  environment_file: str
  environment_pattern: str


class Names(TypedDict):
  invalid_pattern: str
  separator: str
  maximum_length: int


class Paths(TypedDict):
  default_data_directory: str
  applications_directory: str
  icons_directory: str
  icon_theme_directory: str
  desktop_extension: str


class Files(TypedDict):
  mode: str


class Icons(TypedDict):
  download_extension: str
  name_pattern: str
  allowed_extensions: list[str]
  schemes: list[str]
  mode: str
  cache_arguments: list[str]
  download_arguments: list[str]
  maximum_bytes: int
  timeout_seconds: int


class Desktop(TypedDict):
  app_id: str
  app_id_argument: str
  execute_arguments: list[str]
  version: str
  type: str
  terminal: bool
  startup_notify: bool
  template: str


class Examples(TypedDict):
  icon_url: str
  command_placeholder_arguments: list[str]


class ExitCodes(TypedDict):
  cancelled: int


class TuiInstallConfig(TypedDict):
  arguments: dict[str, int]
  commands: Commands
  gum: Gum
  theme: Theme
  names: Names
  paths: Paths
  files: Files
  icons: Icons
  desktop: Desktop
  examples: Examples
  exit_codes: ExitCodes


class Translator(Protocol):
  def __call__(self, key: str, *arguments: str) -> str: ...


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid TUI installer settings: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid TUI installer settings: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid TUI installer settings: {label} must be an integer")
  return value


def _boolean(value: object, label: str) -> bool:
  if not isinstance(value, bool):
    raise TypeError(f"invalid TUI installer settings: {label} must be a boolean")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise TypeError(f"invalid TUI installer settings: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _text_mapping(value: object, label: str) -> dict[str, str]:
  mapping = _mapping(value, label)
  return {
    _text(key, f"{label} key"): _text(item, f"{label} value")
    for key, item in mapping.items()
  }


def _settings() -> TuiInstallConfig:
  ap = Path(os.environ["ARCH_PATH"])
  with (ap / "data/cli/tui-install.yml").open(encoding="utf-8") as stream:
    raw: object = yaml.safe_load(stream)
  config = _mapping(raw, "root")
  arguments = _mapping(config.get("arguments"), "arguments")
  commands = _mapping(config.get("commands"), "commands")
  gum = _mapping(config.get("gum"), "gum")
  theme = _mapping(config.get("theme"), "theme")
  names = _mapping(config.get("names"), "names")
  paths = _mapping(config.get("paths"), "paths")
  files = _mapping(config.get("files"), "files")
  icons = _mapping(config.get("icons"), "icons")
  desktop = _mapping(config.get("desktop"), "desktop")
  examples = _mapping(config.get("examples"), "examples")
  exit_codes = _mapping(config.get("exit_codes"), "exit_codes")
  return {
    "arguments": {"count": _integer(arguments.get("count"), "arguments.count")},
    "commands": {
      "i18n": _text(commands.get("i18n"), "commands.i18n"),
      "gum": _text(commands.get("gum"), "commands.gum"),
      "terminal_launcher": _text(commands.get("terminal_launcher"), "commands.terminal_launcher"),
      "curl": _text(commands.get("curl"), "commands.curl"),
      "icon_cache": _text(commands.get("icon_cache"), "commands.icon_cache"),
    },
    "gum": {
      "input_arguments": _text_list(gum.get("input_arguments"), "gum.input_arguments"),
      "placeholder_argument": _text(gum.get("placeholder_argument"), "gum.placeholder_argument"),
    },
    "theme": {
      "environment_file": _text(theme.get("environment_file"), "theme.environment_file"),
      "environment_pattern": _text(theme.get("environment_pattern"), "theme.environment_pattern"),
    },
    "names": {
      "invalid_pattern": _text(names.get("invalid_pattern"), "names.invalid_pattern"),
      "separator": _text(names.get("separator"), "names.separator"),
      "maximum_length": _integer(names.get("maximum_length"), "names.maximum_length"),
    },
    "paths": {
      "default_data_directory": _text(paths.get("default_data_directory"), "paths.default_data_directory"),
      "applications_directory": _text(paths.get("applications_directory"), "paths.applications_directory"),
      "icons_directory": _text(paths.get("icons_directory"), "paths.icons_directory"),
      "icon_theme_directory": _text(paths.get("icon_theme_directory"), "paths.icon_theme_directory"),
      "desktop_extension": _text(paths.get("desktop_extension"), "paths.desktop_extension"),
    },
    "files": {"mode": _text(files.get("mode"), "files.mode")},
    "icons": {
      "download_extension": _text(icons.get("download_extension"), "icons.download_extension"),
      "name_pattern": _text(icons.get("name_pattern"), "icons.name_pattern"),
      "allowed_extensions": _text_list(icons.get("allowed_extensions"), "icons.allowed_extensions"),
      "schemes": _text_list(icons.get("schemes"), "icons.schemes"),
      "mode": _text(icons.get("mode"), "icons.mode"),
      "cache_arguments": _text_list(icons.get("cache_arguments"), "icons.cache_arguments"),
      "download_arguments": _text_list(icons.get("download_arguments"), "icons.download_arguments"),
      "maximum_bytes": _integer(icons.get("maximum_bytes"), "icons.maximum_bytes"),
      "timeout_seconds": _integer(icons.get("timeout_seconds"), "icons.timeout_seconds"),
    },
    "desktop": {
      "app_id": _text(desktop.get("app_id"), "desktop.app_id"),
      "app_id_argument": _text(desktop.get("app_id_argument"), "desktop.app_id_argument"),
      "execute_arguments": _text_list(desktop.get("execute_arguments"), "desktop.execute_arguments"),
      "version": _text(desktop.get("version"), "desktop.version"),
      "type": _text(desktop.get("type"), "desktop.type"),
      "terminal": _boolean(desktop.get("terminal"), "desktop.terminal"),
      "startup_notify": _boolean(desktop.get("startup_notify"), "desktop.startup_notify"),
      "template": _text(desktop.get("template"), "desktop.template"),
    },
    "examples": {
      "icon_url": _text(examples.get("icon_url"), "examples.icon_url"),
      "command_placeholder_arguments": _text_list(
        examples.get("command_placeholder_arguments"), "examples.command_placeholder_arguments"
      ),
    },
    "exit_codes": {"cancelled": _integer(exit_codes.get("cancelled"), "exit_codes.cancelled")},
  }


def _translator(settings: TuiInstallConfig) -> Translator:
  def translate(key: str, *arguments: str) -> str:
    ap = Path(os.environ["ARCH_PATH"])
    command = [str(ap / settings["commands"]["i18n"]), key, *arguments]
    try:
      result = subprocess.run(command, check=False, capture_output=True, text=True)
    except OSError:
      return key
    return result.stdout if result.returncode == 0 else key

  return translate


def _gum_environment(settings: TuiInstallConfig) -> dict[str, str]:
  env = os.environ.copy()
  theme_file = Path.home() / settings["theme"]["environment_file"]
  try:
    source = theme_file.read_text(encoding="utf-8")
  except FileNotFoundError:
    return env
  for key, value in re.findall(settings["theme"]["environment_pattern"], source):
    env[key] = value
  return env


def _gum(settings: TuiInstallConfig, arguments: list[str]) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [settings["commands"]["gum"], *arguments],
    check=False,
    capture_output=True,
    text=True,
    env=_gum_environment(settings),
  )


def _input(settings: TuiInstallConfig, prompt: str, placeholder: str) -> str:
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


def _slug(value: str, settings: TuiInstallConfig) -> str:
  policy = settings["names"]
  result = re.sub(policy["invalid_pattern"], policy["separator"], value.lower()).strip(policy["separator"])
  result = result[: policy["maximum_length"]].rstrip(policy["separator"])
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


def _exec_value(command: str, settings: TuiInstallConfig) -> str:
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


def _icon_cache(settings: TuiInstallConfig, directory: Path) -> None:
  subprocess.run(
    [settings["commands"]["icon_cache"], *settings["icons"]["cache_arguments"], str(directory)],
    check=False,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )


def _install_icon(reference: str, slug: str, settings: TuiInstallConfig, data_root: Path) -> str:
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
      if temporary.stat().st_size > settings["icons"]["maximum_bytes"]:
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


def _desktop_entry(name: str, command: str, icon: str, settings: TuiInstallConfig) -> str:
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


def _create(name: str, command: str, icon_reference: str, settings: TuiInstallConfig) -> None:
  if not name.strip() or not command.strip() or not icon_reference.strip():
    raise EmptyLauncherValues
  slug = _slug(name, settings)
  data_home_value = os.environ.get("XDG_DATA_HOME")
  data_home = (
    Path(data_home_value)
    if data_home_value is not None and data_home_value != ""
    else Path.home() / settings["paths"]["default_data_directory"]
  )
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


def _run(settings: TuiInstallConfig, arguments: list[str]) -> int:
  _message = _translator(settings)
  if arguments:
    if len(arguments) != settings["arguments"]["count"]:
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


def main(arguments: list[str] | None = None) -> int:
  try:
    settings = _settings()
  except (OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load TUI installer settings: {error}", file=sys.stderr)
    return os.EX_CONFIG
  supplied = sys.argv[1:] if arguments is None else arguments
  try:
    return _run(settings, supplied)
  except (OSError, re.error, subprocess.SubprocessError, TypeError, ValueError) as error:
    print(f"Could not create TUI launcher: {error}", file=sys.stderr)
    return 1
