from __future__ import annotations

import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

import yaml


class Rule(TypedDict):
  name: str
  pattern: str
  replacement: str


class SystemAuth(TypedDict):
  path: str
  rules: list[Rule]


class SddmAutologin(TypedDict):
  path: str
  remove_patterns: list[str]
  insert_after_pattern: str
  insert_line: str


class Settings(TypedDict):
  system_auth: SystemAuth
  sddm_autologin: SddmAutologin


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid lockout limit configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid lockout limit configuration: {label} must be a string")
  return value


def _pattern(value: object, label: str) -> str:
  pattern = _text(value, label)
  try:
    re.compile(pattern)
  except re.error as error:
    raise ValueError(f"invalid lockout limit configuration: {label} is not a valid pattern") from error
  return pattern


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list):
    raise TypeError(f"invalid lockout limit configuration: {label} must be a list")
  return [_text(item, f"{label} item") for item in value]


def _rules(value: object) -> list[Rule]:
  if not isinstance(value, list):
    raise TypeError("invalid lockout limit configuration: system_auth.rules must be a list")
  result: list[Rule] = []
  for index, raw_rule in enumerate(value):
    rule = _mapping(raw_rule, f"system_auth.rules[{index}]")
    result.append({
      "name": _text(rule.get("name"), f"system_auth.rules[{index}].name"),
      "pattern": _pattern(rule.get("pattern"), f"system_auth.rules[{index}].pattern"),
      "replacement": _text(rule.get("replacement"), f"system_auth.rules[{index}].replacement"),
    })
  return result


def _settings() -> Settings:
  ap = Path(os.environ["AP"])
  with (ap / "data/installer/config-setup.yml").open(encoding="utf-8") as stream:
    raw: object = yaml.safe_load(stream)
  root = _mapping(raw, "root")
  system_auth = _mapping(root.get("lockout_limit"), "lockout_limit")
  auth = _mapping(system_auth.get("system_auth"), "system_auth")
  sddm = _mapping(system_auth.get("sddm_autologin"), "sddm_autologin")
  remove_patterns = _text_list(sddm.get("remove_patterns"), "sddm_autologin.remove_patterns")
  for index, pattern in enumerate(remove_patterns):
    _pattern(pattern, f"sddm_autologin.remove_patterns[{index}]")
  return {
    "system_auth": {
      "path": _text(auth.get("path"), "system_auth.path"),
      "rules": _rules(auth.get("rules")),
    },
    "sddm_autologin": {
      "path": _text(sddm.get("path"), "sddm_autologin.path"),
      "remove_patterns": remove_patterns,
      "insert_after_pattern": _pattern(sddm.get("insert_after_pattern"), "sddm_autologin.insert_after_pattern"),
      "insert_line": _text(sddm.get("insert_line"), "sddm_autologin.insert_line"),
    },
  }


def _replace_lines(lines: list[str], pattern: str, replacement: str, description: str) -> tuple[list[str], int]:
  updated: list[str] = []
  count = 0
  for line in lines:
    body = line.rstrip("\r\n")
    ending = line[len(body):]
    if re.match(pattern, body):
      updated.append(re.sub(pattern, replacement, body) + ending)
      count += 1
    else:
      updated.append(line)
  if count == 0:
    raise ValueError(f"expected PAM rule not found: {description}")
  return updated, count


def _update_system_auth(path: Path, rules: list[Rule]) -> str:
  lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
  for rule in rules:
    lines, _ = _replace_lines(lines, rule["pattern"], rule["replacement"], rule["name"])
  return "".join(lines)


def _update_sddm(path: Path, settings: Settings) -> str:
  options = settings["sddm_autologin"]
  original = path.read_text(encoding="utf-8").splitlines(keepends=True)
  remove_patterns = [re.compile(pattern) for pattern in options["remove_patterns"]]
  insert_pattern = re.compile(options["insert_after_pattern"])
  insert_line = options["insert_line"]
  lines: list[str] = []
  insertions = 0
  for line in original:
    body = line.rstrip("\r\n")
    if any(pattern.search(body) for pattern in remove_patterns):
      continue
    lines.append(line)
    if insert_pattern.search(body):
      ending = "\r\n" if line.endswith("\r\n") else "\n"
      if not line.endswith(("\n", "\r")):
        lines[-1] = line + ending
      lines.append(insert_line + ending)
      insertions += 1
  if insertions == 0:
    raise ValueError(f"expected PAM insertion point not found: {options['insert_after_pattern']}")
  return "".join(lines)


def _replace_file(path: Path, content: str) -> None:
  source_stat = path.lstat()
  if not stat.S_ISREG(source_stat.st_mode):
    raise ValueError(f"PAM configuration is not a regular file: {path}")
  if path.is_symlink():
    raise ValueError(f"PAM configuration is a symlink: {path}")
  if path.read_text(encoding="utf-8") == content:
    return

  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
      stream.write(content)
      stream.flush()
      os.fsync(stream.fileno())
    os.chown(temporary, source_stat.st_uid, source_stat.st_gid)
    shutil.copystat(path, temporary, follow_symlinks=False)
    os.chmod(temporary, stat.S_IMODE(source_stat.st_mode))
    with temporary.open("rb") as stream:
      os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def main() -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load lockout limit configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    system_auth = Path(settings["system_auth"]["path"])
    sddm_autologin = Path(settings["sddm_autologin"]["path"])
    system_auth_content = _update_system_auth(system_auth, settings["system_auth"]["rules"])
    sddm_content = _update_sddm(sddm_autologin, settings)
    _replace_file(system_auth, system_auth_content)
    _replace_file(sddm_autologin, sddm_content)
  except (OSError, ValueError) as error:
    print(f"Could not apply lockout limit configuration: {error}", file=sys.stderr)
    return os.EX_SOFTWARE
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
