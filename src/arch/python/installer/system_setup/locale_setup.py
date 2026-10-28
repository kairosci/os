from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import TypedDict, TypeGuard

import yaml


class LocaleSetup(TypedDict):
  locale_conf_environment: str
  locale_conf_default: str
  locale_gen_environment: str
  locale_gen_default: str
  language_file_environment: str
  language_file_default: str
  default_language: str
  target_locale: str
  target_locale_pattern: str
  target_locale_gen_line: str
  commented_locale_pattern: str
  locale_command: list[str]
  locale_gen_command: list[str]
  stock_values: list[str]
  mode: str
  messages: dict[str, dict[str, str]]


def _is_string_mapping(value: object) -> TypeGuard[dict[str, str]]:
  return isinstance(value, dict) and all(
    isinstance(key, str) and isinstance(item, str) for key, item in value.items()
  )


def _is_locale_setup(value: object) -> TypeGuard[LocaleSetup]:
  if not isinstance(value, dict):
    return False
  text_fields = (
    "locale_conf_environment", "locale_conf_default", "locale_gen_environment", "locale_gen_default",
    "language_file_environment", "language_file_default", "default_language", "target_locale",
    "target_locale_pattern", "target_locale_gen_line", "commented_locale_pattern", "mode",
  )
  messages = value.get("messages")
  return (
    all(isinstance(value.get(field), str) for field in text_fields)
    and all(
      isinstance(value.get(field), list) and all(isinstance(item, str) for item in value[field])
      for field in ("locale_command", "locale_gen_command", "stock_values")
    )
    and isinstance(messages, dict)
    and all(isinstance(language, str) and _is_string_mapping(catalog) for language, catalog in messages.items())
    and isinstance(messages.get("en"), dict)
  )


def _write_atomically(path: Path, content: str, default_mode: int) -> None:
  if path.is_symlink():
    path = path.resolve(strict=True)
  if path.is_file() and path.read_text(encoding="utf-8") == content:
    return
  mode = stat.S_IMODE(path.stat().st_mode) if path.is_file() else default_mode
  path.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary = tempfile.mkstemp(dir=path.parent)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(content)
      output.flush()
      os.fsync(output.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  finally:
    Path(temporary).unlink(missing_ok=True)


def _read(path: Path) -> str:
  try:
    return path.read_text(encoding="utf-8")
  except FileNotFoundError:
    return ""


def _messages(settings: LocaleSetup) -> dict[str, str]:
  language_path = Path(os.environ.get(settings["language_file_environment"]) or settings["language_file_default"])
  language = settings["default_language"]
  try:
    language_code = language_path.read_text(encoding="utf-8").splitlines()[0].split("-", 1)[0].lower()
  except (OSError, IndexError):
    language_code = language
  return settings["messages"].get(language_code, settings["messages"][language])


def _append_line(content: str, line: str) -> str:
  separator = "" if not content or content.endswith("\n") else "\n"
  return f"{content}{separator}{line}\n"


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config: object = yaml.safe_load((root / "data/installer/system-setup.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid system setup configuration")
  settings = config["locale_setup"]
  if not _is_locale_setup(settings):
    raise ValueError("invalid locale setup configuration")
  messages = _messages(settings)
  locale_conf = Path(settings["locale_conf_default"])
  locale_gen = Path(settings["locale_gen_default"])
  if os.geteuid() != 0:
    locale_conf = Path(os.environ.get(settings["locale_conf_environment"]) or locale_conf)
    locale_gen = Path(os.environ.get(settings["locale_gen_environment"]) or locale_gen)

  locale_conf_content = _read(locale_conf)
  current_values = re.findall(r"^LANG=(.*)$", locale_conf_content, flags=re.MULTILINE)
  current = current_values[-1].replace('"', "") if current_values else settings["stock_values"][0]
  if current not in settings["stock_values"]:
    print(messages["leaving"].format(locale=current))
    return 0

  target_locale = settings["target_locale"]
  print(messages["setting"].format(locale=target_locale))
  try:
    available = subprocess.run(
      settings["locale_command"], check=False, stdout=subprocess.PIPE, text=True, stderr=subprocess.DEVNULL
    )
  except OSError:
    available = subprocess.CompletedProcess(settings["locale_command"], 127, "", "")
  if available.returncode or re.search(
    settings["target_locale_pattern"], available.stdout, flags=re.IGNORECASE | re.MULTILINE
  ) is None:
    locale_gen_content = _read(locale_gen)
    commented = re.search(settings["commented_locale_pattern"], locale_gen_content, flags=re.MULTILINE)
    if commented:
      locale_gen_content = re.sub(
        settings["commented_locale_pattern"],
        target_locale,
        locale_gen_content,
        flags=re.MULTILINE,
      )
    elif re.search(settings["target_locale_pattern"], locale_gen_content, flags=re.MULTILINE) is None:
      locale_gen_content = _append_line(locale_gen_content, settings["target_locale_gen_line"])
    _write_atomically(locale_gen, locale_gen_content, int(settings["mode"], 8))
    try:
      generated = subprocess.run(settings["locale_gen_command"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
      return 127
    if generated.returncode:
      return generated.returncode

  updated_lines = []
  found_lang = False
  for line in locale_conf_content.splitlines(keepends=True):
    if line.startswith("LANG="):
      updated_lines.append(f"LANG={target_locale}\n")
      found_lang = True
    else:
      updated_lines.append(line)
  if not found_lang:
    locale_conf_content = _append_line(locale_conf_content, f"LANG={target_locale}")
  else:
    locale_conf_content = "".join(updated_lines)
  _write_atomically(locale_conf, locale_conf_content, int(settings["mode"], 8))
  print(messages["set"].format(locale=target_locale))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
