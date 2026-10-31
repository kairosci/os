from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys


def _run(tool: str, arguments: list[str]) -> int:
  root = str(Path(os.environ["AP"]))
  if root not in sys.path:
    sys.path.insert(0, root)
  module = importlib.import_module(f"scripts.iso.{tool}")
  return int(module.main(arguments))


def download_main(arguments: list[str]) -> int:
  return _run("download", arguments)


def parts_main(arguments: list[str]) -> int:
  return _run("parts", arguments)


def upload_main(arguments: list[str]) -> int:
  return _run("upload", arguments)
