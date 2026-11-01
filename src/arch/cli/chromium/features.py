from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  flags_file: str
  feature_argument: str
  usage: str
  invalid_feature: str
  operation_error: str
  success: int
  invalid_arguments: int
  invalid_feature_status: int
  operation_failed: int


class InvalidFeature(ValueError):
  pass


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"Chromium feature {label} must be a mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"Chromium feature {label} must be non-empty text")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise TypeError(f"Chromium feature {label} must be an exit status")
  return value


def _relative(value: object, label: str) -> str:
  text = _text(value, label)
  path = Path(text)
  if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
    raise ValueError(f"Chromium feature {label} must be a relative path without traversal")
  return text


def load_settings(root: Path) -> Settings:
  document = _mapping(yaml.safe_load((root / "data/cli/chromium-add-feature.yml").read_text(encoding="utf-8")), "configuration")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  return {
    "flags_file": _relative(document.get("flags_file"), "flags file"),
    "feature_argument": _text(document.get("feature_argument"), "feature argument"),
    "usage": _text(messages.get("usage"), "usage message"),
    "invalid_feature": _text(messages.get("invalid_feature"), "invalid feature message"),
    "operation_error": _text(messages.get("operation_error"), "operation error message"),
    "success": _status(statuses.get("success"), "success status"),
    "invalid_arguments": _status(statuses.get("invalid_arguments"), "argument status"),
    "invalid_feature_status": _status(statuses.get("invalid_feature"), "invalid feature status"),
    "operation_failed": _status(statuses.get("operation_failed"), "operation status"),
  }


def _target(home: Path, settings: Settings) -> Path | None:
  path = home / settings["flags_file"]
  if not path.is_file():
    return None
  target = path.resolve(strict=True)
  if not target.is_relative_to(home):
    raise ValueError("Chromium flags file resolves outside the home directory")
  return target


def _line_parts(line: str) -> tuple[str, str]:
  if line.endswith("\r\n"):
    return line[:-2], "\r\n"
  if line.endswith(("\n", "\r")):
    return line[:-1], line[-1:]
  return line, ""


def _arguments(line: str) -> list[str]:
  return line.partition("#")[0].split()


def _has_switch(lines: list[str], switch: str) -> bool:
  return any(argument.startswith(f"{switch}=") for line in lines for argument in _arguments(line))


def _has_feature(lines: list[str], settings: Settings, feature: str) -> bool:
  prefix = f"{settings['feature_argument']}="
  for line in lines:
    for argument in _arguments(line):
      if not argument.startswith(prefix):
        continue
      for item in argument[len(prefix) :].split(","):
        if item.startswith(feature) and (item == feature or item[len(feature) :].startswith(("<", ":"))):
          return True
  return False


def _atomic_write(target: Path, contents: str) -> None:
  if not os.access(target, os.W_OK):
    raise PermissionError("Chromium flags file is not writable")
  descriptor, temporary = tempfile.mkstemp(dir=target.parent)
  temporary_path = Path(temporary)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as output:
      os.fchmod(output.fileno(), stat.S_IMODE(target.stat().st_mode))
      output.write(contents)
      output.flush()
      os.fsync(output.fileno())
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)


def ensure_chromium_flags(
  home: Path,
  settings: Settings,
  feature: str,
  additional_arguments: list[str] | None = None,
) -> None:
  if not feature.isascii() or not feature.isalnum():
    raise InvalidFeature(settings["invalid_feature"])
  target = _target(home, settings)
  if target is None:
    return
  with target.open("r", encoding="utf-8", newline="") as source:
    original = source.read()
  lines = original.splitlines(keepends=True)
  additions: list[str] = []
  modified = False
  for argument in additional_arguments or []:
    switch, separator, _ = argument.partition("=")
    if not separator or not switch.startswith("--"):
      raise ValueError("Chromium additional arguments must be named switches with values")
    if not _has_switch(lines, switch):
      additions.append(argument)

  if not _has_feature(lines, settings, feature):
    prefix = f"{settings['feature_argument']}="
    updated = False
    for index, line in enumerate(lines):
      body, ending = _line_parts(line)
      arguments = _arguments(body)
      argument = next((item for item in arguments if item.startswith(prefix)), None)
      if argument is None:
        continue
      value = argument[len(prefix) :]
      separator = "," if value else ""
      replacement = f"{argument}{separator}{feature}"
      comment_index = body.find("#")
      before_comment = body if comment_index == -1 else body[:comment_index]
      after_comment = "" if comment_index == -1 else body[comment_index:]
      lines[index] = before_comment.replace(argument, replacement, 1) + after_comment + ending
      updated = True
      modified = True
      break
    if not updated:
      additions.append(f"{settings['feature_argument']}={feature}")

  if not additions and not modified:
    return
  newline = "\r\n" if "\r\n" in original else "\n"
  contents = "".join(lines)
  if contents and not contents.endswith(("\n", "\r")):
    contents += newline
  contents += newline.join(additions) + newline
  _atomic_write(target, contents)


def main(arguments: list[str]) -> int:
  try:
    root = Path(os.environ["AP"])
    settings = load_settings(root)
  except (KeyError, OSError, RuntimeError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return 1
  if len(arguments) != 1:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]
  try:
    home = Path(os.environ["HOME"]).resolve(strict=True)
    ensure_chromium_flags(home, settings, arguments[0])
  except InvalidFeature as error:
    print(error, file=sys.stderr)
    return settings["invalid_feature_status"]
  except (KeyError, OSError, RuntimeError, UnicodeError, ValueError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
