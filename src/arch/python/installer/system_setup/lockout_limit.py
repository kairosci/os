from __future__ import annotations

import os
import re
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  ap = Path(os.environ["ARCH_PATH"])
  with (ap / "data/installer/config-setup.yml").open(encoding="utf-8") as stream:
    settings = yaml.safe_load(stream)
  if not isinstance(settings, dict):
    raise ValueError("invalid system setup settings")
  return settings["lockout_limit"]


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


def _update_system_auth(path: Path, rules: list[dict[str, str]]) -> str:
  lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
  for rule in rules:
    lines, _ = _replace_lines(lines, rule["pattern"], rule["replacement"], rule["name"])
  return "".join(lines)


def _update_sddm(path: Path, settings: dict[str, Any]) -> str:
  original = path.read_text(encoding="utf-8").splitlines(keepends=True)
  remove_patterns = [re.compile(pattern) for pattern in settings["sddm_autologin"]["remove_patterns"]]
  insert_pattern = re.compile(settings["sddm_autologin"]["insert_after_pattern"])
  insert_line = settings["sddm_autologin"]["insert_line"]
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
    raise ValueError(f"expected PAM insertion point not found: {settings['sddm_autologin']['insert_after_pattern']}")
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


def main() -> None:
  settings = _settings()
  system_auth = Path(settings["system_auth"]["path"])
  sddm_autologin = Path(settings["sddm_autologin"]["path"])
  system_auth_content = _update_system_auth(system_auth, settings["system_auth"]["rules"])
  sddm_content = _update_sddm(sddm_autologin, settings)
  _replace_file(system_auth, system_auth_content)
  _replace_file(sddm_autologin, sddm_content)


if __name__ == "__main__":
  main()
