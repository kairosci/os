from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError(f"Invalid migration configuration: {path}")
  return value


def remove_values(value: Any, values: set[str], object_key: str | None) -> Any:
  if isinstance(value, list):
    return [
      item for item in value
      if not (isinstance(item, str) and item in values) and not (
        object_key and isinstance(item, dict) and item.get(object_key) in values
      )
    ]
  if isinstance(value, dict):
    return {key: remove_values(item, values, object_key) for key, item in value.items()}
  return value


def remove_config_entries(home: Path, config: dict[str, Any]) -> None:
  xdg_variable = config["xdg_variable"]
  fallback = home / config["default_directory"]
  base = Path(os.environ.get(xdg_variable) or fallback)
  path = base / config["relative_file"]
  if not path.exists():
    return

  path = path.resolve(strict=True)
  document = json.loads(path.read_text(encoding="utf-8"))
  original = json.dumps(document, ensure_ascii=False, indent=2) + "\n"

  for entry in config["entries"]:
    current = document
    for key in entry["path"]:
      if not isinstance(current, dict):
        current = None
        break
      current = current.get(key)
    if isinstance(current, list):
      index = entry.get("object_key")
      values = set(entry["remove"])
      filtered = remove_values(current, values, index)
      parent = document
      for key in entry["path"][:-1]:
        if not isinstance(parent, dict):
          parent = None
          break
        parent = parent.get(key)
      if isinstance(parent, dict):
        parent[entry["path"][-1]] = filtered
    elif isinstance(current, dict):
      values = set(entry["remove"])
      index = entry.get("object_key")
      for key, item in current.items():
        if isinstance(item, list):
          current[key] = remove_values(item, values, index)

  updated = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
  if updated == original:
    return

  mode = path.stat().st_mode & 0o777
  temporary_name: str | None = None
  try:
    with tempfile.NamedTemporaryFile(
      mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as temporary:
      temporary_name = temporary.name
      temporary.write(updated)
      temporary.flush()
      os.fsync(temporary.fileno())
    os.chmod(temporary_name, mode)
    os.replace(temporary_name, path)
  finally:
    if temporary_name and os.path.exists(temporary_name):
      os.unlink(temporary_name)


def remove_home_paths(home: Path, paths: dict[str, list[str]]) -> None:
  home = home.resolve()
  for name in paths.get("files", []):
    target = safe_home_path(home, name)
    if target is None:
      continue
    if target.is_symlink() or target.is_file():
      target.unlink()
  for name in paths.get("directories", []):
    target = safe_home_path(home, name)
    if target is None:
      continue
    if target.is_symlink() or target.is_file():
      target.unlink()
    elif target.is_dir():
      shutil.rmtree(target)


def safe_home_path(home: Path, name: str) -> Path | None:
  relative = Path(name)
  if relative.is_absolute() or ".." in relative.parts:
    raise ValueError(f"Migration path must stay under the home directory: {name}")
  target = home / relative
  if not target.parent.resolve(strict=False).is_relative_to(home):
    return None
  return target


def run_mise_cleanup(
  config: dict[str, Any], commands: dict[str, list[str]], list_command: list[str]
) -> None:
  tool = config.get("tool")
  if not tool or not shutil.which(commands["mise"][0]):
    return

  listed = subprocess.run(
    [*commands["mise"], *list_command, tool], check=False, capture_output=True, text=True
  )
  if listed.returncode or tool not in listed.stdout:
    return

  for action in config["actions"]:
    subprocess.run([*commands["mise"], *action], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(migration_path: Path) -> int:
  root = Path(os.environ["ARCH_PATH"])
  migration = load_yaml(root / "data/migrations" / f"{migration_path.stem}.yml")
  runner = load_yaml(root / "data/cli/migration-cleanup.yml")
  translated = subprocess.run(
    [*runner["commands"]["i18n"], migration["messages"]["reason"]],
    check=True,
    capture_output=True,
    text=True,
  )
  print(translated.stdout.rstrip("\n"))

  commands = runner["commands"]
  packages = migration.get("packages", {}).get("drop", [])
  if packages:
    subprocess.run([*commands["package_drop"], *packages], check=True)

  run_mise_cleanup(migration.get("mise", {}), commands, runner["commands"]["mise_list"])
  home = Path.home()
  if "config" in migration:
    remove_config_entries(home, migration["config"])
  remove_home_paths(home, migration.get("paths", {}))
  return int(runner["statuses"]["success"])
