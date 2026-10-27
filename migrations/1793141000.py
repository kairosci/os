from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("Invalid migration configuration")
  return value


def remove_exact_file(path: Path, expected: str) -> None:
  if path.is_symlink() or not path.is_file():
    return
  try:
    if path.read_text(encoding="utf-8") == expected:
      path.unlink()
  except (OSError, UnicodeError):
    return


def remove_mime_association(path: Path, config: dict[str, Any]) -> None:
  if path.is_symlink() or not path.is_file():
    return
  try:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
  except (OSError, UnicodeError):
    return

  key = config["key"]
  obsolete = config["obsolete_handler"]
  updated: list[str] = []
  changed = False
  for line in lines:
    content = line.rstrip("\r\n")
    ending = line[len(content):]
    if "=" not in content or content.partition("=")[0] != key:
      updated.append(line)
      continue
    handlers = content.partition("=")[2].split(";")
    remaining = [handler for handler in handlers if handler != obsolete]
    if len(remaining) == len(handlers):
      updated.append(line)
      continue
    changed = True
    remaining = [handler for handler in remaining if handler]
    if remaining:
      updated.append(f"{key}={';'.join(remaining)};{ending}")
  if changed:
    path.write_text("".join(updated), encoding="utf-8")


def main() -> int:
  config = load_config()
  home = Path.home()
  applications = home / config["paths"]["applications"]
  for launcher in config["launchers"]:
    remove_exact_file(applications / launcher["name"], launcher["content"])

  config_home = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config")))
  mime_files = [home / relative for relative in config["paths"]["mime_files"]]
  mime_files.append(config_home / ".".join(config["paths"]["xdg_config_mime_file"]))
  for mime_file in set(mime_files):
    remove_mime_association(mime_file, config["mime"])

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
