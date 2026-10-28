#!/usr/bin/python3

"""Generate installed command launchers for Python CLI modules."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
MODULE = re.compile(r"[a-z_][a-z0-9_]*(?:/[a-z_][a-z0-9_]*)*\Z")
FUNCTION = re.compile(r"[a-z_][a-z0-9_]*\Z")


def load_entrypoints() -> list[dict[str, str]]:
  path = ROOT / "data/cli/python-entrypoints.yml"
  document = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(document, dict) or not isinstance(document.get("entrypoints"), list):
    raise ValueError(f"invalid entrypoint configuration: {path}")

  entries: list[dict[str, str]] = []
  names: set[str] = set()
  for entry in document["entrypoints"]:
    if not isinstance(entry, dict) or set(entry) != {"binary", "module", "function"}:
      raise ValueError("each entrypoint must define binary, module, and function")
    if not all(isinstance(entry[key], str) for key in ("binary", "module", "function")):
      raise ValueError("entrypoint fields must be strings")
    if not NAME.fullmatch(entry["binary"]) or not MODULE.fullmatch(entry["module"]):
      raise ValueError(f"invalid entrypoint name or module: {entry}")
    if not FUNCTION.fullmatch(entry["function"]):
      raise ValueError(f"invalid entrypoint function: {entry}")
    if entry["binary"] in names:
      raise ValueError(f"duplicate entrypoint: {entry['binary']}")
    names.add(entry["binary"])
    entries.append(entry)
  return entries


def generate(destination: Path) -> None:
  for entry in load_entrypoints():
    module_path = ROOT / "src/arch/cli" / entry["module"]
    module_path = module_path.with_suffix(".py")
    if not module_path.is_file():
      raise ValueError(f"entrypoint module does not exist: {module_path.relative_to(ROOT)}")
    source = module_path.read_text(encoding="utf-8")
    if not re.search(rf"^def {re.escape(entry['function'])}\s*\(", source, re.MULTILINE):
      raise ValueError(f"entrypoint function is missing: {entry['module']}.{entry['function']}")

    output = destination / "usr/share/arch/src/arch/commands" / entry["binary"]
    if not output.is_file():
      raise ValueError(f"entrypoint command is not declared by a module: {entry['binary']}")
    output.write_text(
      "#!/usr/bin/python3 -I\n"
      "import os\n"
      "import sys\n"
      "from pathlib import Path\n"
      "\n"
      "sys.path.insert(0, str(Path(os.environ[\"AP\"]) / \"src\"))\n"
      f"from arch.cli.{entry['module'].replace('/', '.')} import {entry['function']}\n"
      "\n"
      f"raise SystemExit({entry['function']}())\n",
      encoding="utf-8",
    )
    output.chmod(0o755)


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("generate", choices=("generate",))
  parser.add_argument("--destination", type=Path, required=True)
  arguments = parser.parse_args()
  generate(arguments.destination)
  return 0


if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except (OSError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    raise SystemExit(1)
