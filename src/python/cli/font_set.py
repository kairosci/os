from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/fonts.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid font command configuration")
  return settings["set"]


def _language(settings: dict[str, Any]) -> str:
  return os.environ.get("LANG", settings["messages"]["default_language"]).split(".", 1)[0].split("_", 1)[0]


def _message(settings: dict[str, Any], key: str, value: str = "") -> str:
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


def _write_atomic(path: Path, content: str, settings: dict[str, Any]) -> None:
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


def _update(settings: dict[str, Any], target: Path, config: dict[str, Any], font: str) -> None:
  if not target.is_file():
    return
  content = target.read_text(encoding="utf-8")
  replacement = config["replacement"].format(font=font, size=config.get("size", ""))
  updated, count = re.subn(config["pattern"], lambda _: replacement, content)
  if count:
    _write_atomic(target, updated, settings)


def main(arguments: list[str] | None = None) -> int:
  arguments = sys.argv[1:] if arguments is None else arguments
  settings = _settings()
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

  root = Path(os.environ["ARCH_PATH"])
  home = Path.home()
  config_home = os.environ.get(settings["config_home_environment"]) or str(home / settings["config_home_default"])
  config_root = Path(config_home)
  configs = settings["configs"]
  try:
    targets = {
      name: _safe_target(config_root, home, config["path"])
      for name, config in configs.items()
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
