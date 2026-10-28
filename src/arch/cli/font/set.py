from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Literal, NotRequired, TypedDict

import yaml


class Messages(TypedDict):
  default_language: str
  usage: dict[str, str]
  invalid_font: dict[str, str]
  not_found: dict[str, str]
  unsafe_config: dict[str, str]


class FontListConfig(TypedDict):
  path: str
  pattern: str
  replacement: str
  size: NotRequired[int]


class KittyConfig(TypedDict):
  path: str
  presence_command: list[str]
  pattern: str
  replacement: str
  append: str
  reload_command: list[str]


class GhosttyConfig(FontListConfig):
  reload_command: list[str]


class FontConfig(TypedDict):
  path: str
  template: str


class Configs(TypedDict):
  alacritty: FontListConfig
  kitty: KittyConfig
  ghostty: GhosttyConfig
  foot: FontListConfig
  fontconfig: FontConfig


class ExitCodes(TypedDict):
  usage: int
  invalid_font: int
  not_found: int
  unsafe_config: int


class FontSetConfig(TypedDict):
  allowed_extra_characters: str
  help_arguments: list[str]
  exit_codes: ExitCodes
  messages: Messages
  config_home_environment: str
  config_home_default: str
  default_file_mode: int
  file_mode_mask: int
  temporary_file_prefix: str
  font_list_command: list[str]
  configs: Configs
  process_command: list[str]
  notification_command: list[str]
  i18n_command: list[str]
  notifications: list[dict[str, str]]
  notification_message: str
  restart_command: list[str]
  hook_command: list[str]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid font command configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid font command configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid font command configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid font command configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _text_mapping(value: object, label: str) -> dict[str, str]:
  mapping = _mapping(value, label)
  return {
    _text(key, f"{label} key"): _text(item, f"{label} value")
    for key, item in mapping.items()
  }


def _message_tables(value: object) -> Messages:
  messages = _mapping(value, "messages")
  return {
    "default_language": _text(messages.get("default_language"), "messages.default_language"),
    "usage": _text_mapping(messages.get("usage"), "messages.usage"),
    "invalid_font": _text_mapping(messages.get("invalid_font"), "messages.invalid_font"),
    "not_found": _text_mapping(messages.get("not_found"), "messages.not_found"),
    "unsafe_config": _text_mapping(messages.get("unsafe_config"), "messages.unsafe_config"),
  }


def _font_list_config(value: object, label: str) -> FontListConfig:
  config = _mapping(value, label)
  result: FontListConfig = {
    "path": _text(config.get("path"), f"{label}.path"),
    "pattern": _text(config.get("pattern"), f"{label}.pattern"),
    "replacement": _text(config.get("replacement"), f"{label}.replacement"),
  }
  if "size" in config:
    result["size"] = _integer(config.get("size"), f"{label}.size")
  return result


def _configs(value: object) -> Configs:
  configs = _mapping(value, "configs")
  kitty = _mapping(configs.get("kitty"), "configs.kitty")
  ghostty = _mapping(configs.get("ghostty"), "configs.ghostty")
  fontconfig = _mapping(configs.get("fontconfig"), "configs.fontconfig")
  return {
    "alacritty": _font_list_config(configs.get("alacritty"), "configs.alacritty"),
    "kitty": {
      "path": _text(kitty.get("path"), "configs.kitty.path"),
      "presence_command": _text_list(kitty.get("presence_command"), "configs.kitty.presence_command"),
      "pattern": _text(kitty.get("pattern"), "configs.kitty.pattern"),
      "replacement": _text(kitty.get("replacement"), "configs.kitty.replacement"),
      "append": _text(kitty.get("append"), "configs.kitty.append"),
      "reload_command": _text_list(kitty.get("reload_command"), "configs.kitty.reload_command"),
    },
    "ghostty": {
      **_font_list_config(ghostty, "configs.ghostty"),
      "reload_command": _text_list(ghostty.get("reload_command"), "configs.ghostty.reload_command"),
    },
    "foot": _font_list_config(configs.get("foot"), "configs.foot"),
    "fontconfig": {
      "path": _text(fontconfig.get("path"), "configs.fontconfig.path"),
      "template": _text(fontconfig.get("template"), "configs.fontconfig.template"),
    },
  }


def _settings() -> FontSetConfig:
  root = Path(os.environ["ARCH_PATH"])
  raw: object = yaml.safe_load((root / "data/cli/fonts.yml").read_text(encoding="utf-8"))
  settings = _mapping(raw, "root")
  config = _mapping(settings.get("set"), "set")
  exits = _mapping(config.get("exit_codes"), "set.exit_codes")
  notifications = config.get("notifications")
  if not isinstance(notifications, list):
    raise ValueError("invalid font command configuration: set.notifications must be a list")
  parsed_notifications: list[dict[str, str]] = []
  for index, item in enumerate(notifications):
    notification = _mapping(item, f"set.notifications[{index}]")
    parsed_notifications.append({
      "process": _text(notification.get("process"), f"set.notifications[{index}].process"),
      "application": _text(notification.get("application"), f"set.notifications[{index}].application"),
    })
  return {
    "allowed_extra_characters": _text(config.get("allowed_extra_characters"), "set.allowed_extra_characters"),
    "help_arguments": _text_list(config.get("help_arguments"), "set.help_arguments"),
    "exit_codes": {
      "usage": _integer(exits.get("usage"), "set.exit_codes.usage"),
      "invalid_font": _integer(exits.get("invalid_font"), "set.exit_codes.invalid_font"),
      "not_found": _integer(exits.get("not_found"), "set.exit_codes.not_found"),
      "unsafe_config": _integer(exits.get("unsafe_config"), "set.exit_codes.unsafe_config"),
    },
    "messages": _message_tables(config.get("messages")),
    "config_home_environment": _text(config.get("config_home_environment"), "set.config_home_environment"),
    "config_home_default": _text(config.get("config_home_default"), "set.config_home_default"),
    "default_file_mode": _integer(config.get("default_file_mode"), "set.default_file_mode"),
    "file_mode_mask": _integer(config.get("file_mode_mask"), "set.file_mode_mask"),
    "temporary_file_prefix": _text(config.get("temporary_file_prefix"), "set.temporary_file_prefix"),
    "font_list_command": _text_list(config.get("font_list_command"), "set.font_list_command"),
    "configs": _configs(config.get("configs")),
    "process_command": _text_list(config.get("process_command"), "set.process_command"),
    "notification_command": _text_list(config.get("notification_command"), "set.notification_command"),
    "i18n_command": _text_list(config.get("i18n_command"), "set.i18n_command"),
    "notifications": parsed_notifications,
    "notification_message": _text(config.get("notification_message"), "set.notification_message"),
    "restart_command": _text_list(config.get("restart_command"), "set.restart_command"),
    "hook_command": _text_list(config.get("hook_command"), "set.hook_command"),
  }


def _language(settings: FontSetConfig) -> str:
  return os.environ.get("LANG", settings["messages"]["default_language"]).split(".", 1)[0].split("_", 1)[0]


def _message(settings: FontSetConfig, key: Literal["usage", "invalid_font", "not_found", "unsafe_config"], value: str = "") -> str:
  messages = settings["messages"]
  translations = messages[key]
  language = _language(settings)
  message = translations.get(language, translations[messages["default_language"]])
  return message.replace("%1", value)


def _safe_target(config_root: Path, home: Path, relative_path: str) -> Path:
  base = config_root.resolve()
  target = (config_root / relative_path).resolve(strict=False)
  roots = (base, home.resolve())
  if not any(target == root or root in target.parents for root in roots):
    raise ValueError("unsafe configuration path")
  return target


def _write_atomic(path: Path, content: str, settings: FontSetConfig) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  permission_mask = int(settings["file_mode_mask"])
  existing_mode = path.stat().st_mode & permission_mask if path.exists() else None
  if existing_mode is None:
    mask = os.umask(0)
    os.umask(mask)
    mode = int(settings["default_file_mode"]) & ~mask
  else:
    mode = existing_mode

  descriptor, temporary = tempfile.mkstemp(prefix=settings["temporary_file_prefix"], dir=path.parent)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
      stream.write(content)
      stream.flush()
      os.fsync(stream.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, path)
  except BaseException:
    try:
      os.unlink(temporary)
    except FileNotFoundError:
      pass
    raise


def _update(settings: FontSetConfig, target: Path, config: FontListConfig, font: str) -> None:
  if not target.is_file():
    return
  content = target.read_text(encoding="utf-8")
  replacement = config["replacement"].format(font=font, size=config.get("size", ""))
  updated, count = re.subn(config["pattern"], lambda _: replacement, content)
  if count:
    _write_atomic(target, updated, settings)


def _set_font(arguments: list[str], settings: FontSetConfig) -> int:
  font = arguments[0] if arguments else ""
  usage_code = int(settings["exit_codes"]["usage"])

  if font in settings["help_arguments"]:
    print(_message(settings, "usage"))
    return 0
  if not font:
    print(_message(settings, "usage"), file=sys.stderr)
    return usage_code
  if not all(character.isalnum() or character in settings["allowed_extra_characters"] for character in font):
    print(_message(settings, "invalid_font"), file=sys.stderr)
    return int(settings["exit_codes"]["invalid_font"])

  available = subprocess.run(settings["font_list_command"], check=False, stdout=subprocess.PIPE, text=True)
  if font.casefold() not in available.stdout.casefold():
    print(_message(settings, "not_found", font))
    return int(settings["exit_codes"]["not_found"])

  home = Path.home()
  config_home = os.environ.get(settings["config_home_environment"]) or str(home / settings["config_home_default"])
  config_root = Path(config_home)
  configs = settings["configs"]
  try:
    targets = {
      "alacritty": _safe_target(config_root, home, configs["alacritty"]["path"]),
      "kitty": _safe_target(config_root, home, configs["kitty"]["path"]),
      "ghostty": _safe_target(config_root, home, configs["ghostty"]["path"]),
      "foot": _safe_target(config_root, home, configs["foot"]["path"]),
      "fontconfig": _safe_target(config_root, home, configs["fontconfig"]["path"]),
    }
  except ValueError:
    print(_message(settings, "unsafe_config"), file=sys.stderr)
    return int(settings["exit_codes"]["unsafe_config"])

  _update(settings, targets["alacritty"], configs["alacritty"], font)

  kitty = configs["kitty"]
  kitty_target = targets["kitty"]
  present = kitty_target.is_file() or subprocess.run(
    kitty["presence_command"], check=False,
  ).returncode == 0
  if present:
    content = kitty_target.read_text(encoding="utf-8") if kitty_target.is_file() else ""
    replacement = kitty["replacement"].format(font=font)
    updated, count = re.subn(kitty["pattern"], lambda _: replacement, content)
    if not count:
      updated = content + kitty["append"].replace("\\n", "\n").format(font=font)
    _write_atomic(kitty_target, updated, settings)
    subprocess.run(kitty["reload_command"], check=False)

  ghostty = configs["ghostty"]
  _update(settings, targets["ghostty"], ghostty, font)
  if targets["ghostty"].is_file():
    subprocess.run(ghostty["reload_command"], check=False)

  _update(settings, targets["foot"], configs["foot"], font)

  fontconfig = configs["fontconfig"]
  template = fontconfig["template"].format(font=font)
  _write_atomic(targets["fontconfig"], template, settings)
  subprocess.run(settings["restart_command"], check=False)

  for notification in settings["notifications"]:
    running = subprocess.run([*settings["process_command"], notification["process"]], check=False)
    if running.returncode == 0:
      message = subprocess.run(
        [*settings["i18n_command"], settings["notification_message"], notification["application"]],
        check=False,
        capture_output=True,
        text=True,
      )
      subprocess.run([*settings["notification_command"], message.stdout.rstrip("\n")], check=False)

  result = subprocess.run([*settings["hook_command"], font], check=False)
  return result.returncode


def main(arguments: list[str] | None = None) -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load font command configuration: {error}", file=sys.stderr)
    return 1
  supplied = sys.argv[1:] if arguments is None else arguments
  try:
    return _set_font(supplied, settings)
  except (KeyError, OSError, re.error, subprocess.SubprocessError, TypeError, ValueError) as error:
    print(f"Could not set the font: {error}", file=sys.stderr)
    return 1
