from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_desktop_entry(path: Path) -> dict[str, str] | None:
  fields: dict[str, str] = {}
  in_entry = False
  try:
    lines = path.read_text(encoding="utf-8").splitlines()
  except (OSError, UnicodeError):
    return None

  for line in lines:
    if line.startswith("["):
      if in_entry:
        break
      in_entry = line == "[Desktop Entry]"
      continue
    if not in_entry or "=" not in line:
      continue
    key, value = line.split("=", 1)
    key = key.strip()
    if key in fields:
      return None
    fields[key] = value.strip()
  return fields if in_entry else None


def remove_exact_desktop_entry(path: Path, generated_entries: list[dict[str, Any]]) -> bool:
  if path.is_symlink() or not path.is_file():
    return False
  if parse_desktop_entry(path) not in generated_entries:
    return False
  path.unlink()
  return True
