from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from typing import Any

import yaml


def load_config(root: Path) -> dict[str, Any]:
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("invalid mise migration configuration")
  return value


def replace_atomically(path: Path, content: str) -> None:
  mode = stat.S_IMODE(path.stat().st_mode)
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(content)
      output.flush()
      os.fsync(output.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, path)
    directory_descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory_descriptor)
    finally:
      os.close(directory_descriptor)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  message = subprocess.run(
    [*config["commands"]["i18n"], config["message"]],
    check=False,
    capture_output=True,
    text=True,
  )
  print(message.stdout.rstrip("\n"))

  path = Path(os.environ["HOME"]) / config["paths"]["mise_config"]
  if path.is_file():
    content = path.read_text(encoding="utf-8")
    updated = re.sub(config["rewrite"]["pattern"], config["rewrite"]["replacement"], content)
    if updated != content:
      replace_atomically(path, updated)

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
