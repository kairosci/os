from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import tempfile
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  value = yaml.safe_load((root / "data/migrations/1792847855.yml").read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("invalid branding migration configuration")
  return value


def localized(config: dict[str, Any]) -> str:
  result = subprocess.run(
    [*config["commands"]["i18n"], config["message"]],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def apply_system_branding(config: dict[str, Any], root: Path) -> int:
  identity_path = Path(config["paths"]["os_release"])
  try:
    current_lines = identity_path.read_text(encoding="utf-8").splitlines()
  except OSError:
    current_lines = []
  if all(line in current_lines for line in config["identity_lines"]):
    return int(config["statuses"]["success"])

  command = [
    *config["commands"]["elevate"],
    f"ARCH_PATH={root}",
    *config["commands"]["python"],
    str(root / config["paths"]["branding_setup"]),
  ]
  return subprocess.run(command, check=False).returncode


def replace_atomically(path: Path, content: str) -> None:
  original_mode = stat.S_IMODE(path.stat().st_mode)
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(content)
      output.flush()
      os.fsync(output.fileno())
    os.chmod(temporary, original_mode)
    os.replace(temporary, path)
    directory_descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory_descriptor)
    finally:
      os.close(directory_descriptor)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def update_terminal(config: dict[str, Any]) -> None:
  path = Path.home() / config["paths"]["terminal_desktop"]
  if not path.is_file():
    return
  current = path.read_text(encoding="utf-8")
  lines = current.splitlines(keepends=True)
  for replacement in config["terminal_replacements"]:
    updated_lines: list[str] = []
    for line in lines:
      ending = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
      content = line[:-len(ending)] if ending else line
      updated_lines.append((replacement["new"] if content == replacement["old"] else content) + ending)
    lines = updated_lines
  updated = "".join(lines)
  if updated != current:
    replace_atomically(path, updated)


def main() -> int:
  config = load_config()
  root = Path(os.environ["ARCH_PATH"])
  print(localized(config))
  result = apply_system_branding(config, root)
  if result != 0:
    return result
  update_terminal(config)
  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
