#!/usr/bin/python3

"""Generate and run command entrypoints declared for Python CLI modules."""

from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path
from typing import cast

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
  required_fields = {"binary", "module", "function", "group", "name", "summary"}
  optional_fields = {"args", "examples", "generate_launcher", "hidden", "pass_args"}
  for entry in document["entrypoints"]:
    if (
      not isinstance(entry, dict)
      or not required_fields <= set(entry)
      or not set(entry) <= required_fields | optional_fields
    ):
      raise ValueError("each entrypoint must define supported Python CLI metadata")
    if not all(isinstance(entry[key], str) for key in set(entry)):
      raise ValueError("entrypoint fields must be strings")
    if (
      not NAME.fullmatch(entry["binary"])
      or not MODULE.fullmatch(entry["module"])
      or not FUNCTION.fullmatch(entry["function"])
      or not NAME.fullmatch(entry["group"])
      or not entry["summary"].strip()
      or any(key in entry and not entry[key].strip() for key in optional_fields)
      or any(
        any(character in entry[key] for character in ("\n", "\t", "\x1f"))
        for key in set(entry) - {"binary", "module", "function", "group"}
      )
      or entry.get("hidden", "false") not in {"true", "false"}
      or entry.get("generate_launcher", "true") not in {"true", "false"}
      or entry.get("pass_args", "false") not in {"true", "false"}
    ):
      raise ValueError(f"invalid entrypoint metadata: {entry}")
    if entry["binary"] in names:
      raise ValueError(f"duplicate entrypoint: {entry['binary']}")
    names.add(entry["binary"])
    entries.append(entry)
  return entries


def load_groups() -> dict[str, str]:
  path = ROOT / "data/cli/groups.yml"
  document = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(document, dict) or not isinstance(document.get("groups"), dict):
    raise ValueError(f"invalid command group configuration: {path}")
  raw_groups = cast(dict[object, object], document["groups"])
  groups: dict[str, str] = {}
  for name, description in raw_groups.items():
    if (
      not isinstance(name, str)
      or not NAME.fullmatch(name)
      or not isinstance(description, str)
      or not description.strip()
      or any(character in description for character in ("\n", "\t", "\x1f"))
    ):
      raise ValueError(f"invalid command group metadata: {path}")
    groups[name] = description
  return groups


def validate_module(entry: dict[str, str]) -> None:
  module_path = ROOT / "src/arch/cli" / entry["module"]
  module_path = module_path.with_suffix(".py")
  if not module_path.is_file():
    raise ValueError(f"entrypoint module does not exist: {module_path.relative_to(ROOT)}")
  source = module_path.read_text(encoding="utf-8")
  if not re.search(rf"^def {re.escape(entry['function'])}\s*\(", source, re.MULTILINE):
    raise ValueError(f"entrypoint function is missing: {entry['module']}.{entry['function']}")


def generate(destination: Path) -> None:
  group_output = destination / "usr/share/arch/data/cli/group-descriptions.sh"
  group_output.parent.mkdir(parents=True, exist_ok=True)
  group_lines = [
    f"GROUP_DESCRIPTIONS[{name}]={bash_quote(description)}\n"
    for name, description in load_groups().items()
  ]
  group_output.write_text("".join(group_lines), encoding="utf-8")
  group_output.chmod(0o644)

  for entry in load_entrypoints():
    validate_module(entry)
    output = destination / "usr/share/arch/src/arch/commands" / entry["binary"]
    if entry.get("generate_launcher", "true") == "false":
      output.unlink(missing_ok=True)
      continue
    output.parent.mkdir(parents=True, exist_ok=True)
    header = [
      "#!/usr/bin/python3 -I\n",
      f"# arch:group={entry['group']}\n",
      f"# arch:name={entry['name']}\n",
      f"# arch:summary={entry['summary']}\n",
    ]
    if "args" in entry:
      header.append(f"# arch:args={entry['args']}\n")
    if "examples" in entry:
      header.append(f"# arch:examples={entry['examples']}\n")
    if entry.get("hidden") == "true":
      header.append("# arch:hidden=true\n")
    call = f"{entry['function']}(sys.argv[1:])" if entry.get("pass_args") == "true" else f"{entry['function']}()"
    source = (
      "import os\n"
      "import sys\n"
      "from pathlib import Path\n"
      "\n"
      "sys.path.insert(0, str(Path(os.environ[\"AP\"]) / \"src\"))\n"
      f"from arch.cli.{entry['module'].replace('/', '.')} import {entry['function']}\n"
      "\n"
      f"raise SystemExit({call})\n"
    )
    output.write_text("".join(header) + source, encoding="utf-8")
    output.chmod(0o755)


def bash_quote(value: str) -> str:
  return "'" + value.replace("'", "'\"'\"'") + "'"


def emit_metadata() -> None:
  for name, description in load_groups().items():
    print("\x1f".join(("group", name, description)))
  for entry in load_entrypoints():
    print("\x1f".join(("command", *(entry.get(key, "") for key in (
      "binary", "module", "function", "group", "name", "summary", "args", "examples", "hidden"
    )))))


def run_entrypoint(binary: str, arguments: list[str]) -> int:
  entries = {entry["binary"]: entry for entry in load_entrypoints()}
  try:
    entry = entries[binary]
  except KeyError as error:
    raise ValueError(f"unknown Python CLI entrypoint: {binary}") from error
  validate_module(entry)
  sys.path.insert(0, str(ROOT / "src"))
  module = importlib.import_module(f"arch.cli.{entry['module'].replace('/', '.')}")
  function = getattr(module, entry["function"])
  sys.argv = [binary, *arguments]
  result = function(arguments) if entry.get("pass_args") == "true" else function()
  return int(result) if result is not None else 0


def main() -> int:
  parser = argparse.ArgumentParser()
  operations = parser.add_subparsers(dest="operation", required=True)
  generate_parser = operations.add_parser("generate")
  generate_parser.add_argument("--destination", type=Path, required=True)
  operations.add_parser("metadata")
  run_parser = operations.add_parser("run")
  run_parser.add_argument("binary")
  run_parser.add_argument("arguments", nargs=argparse.REMAINDER)
  arguments = parser.parse_args()
  if arguments.operation == "generate":
    generate(arguments.destination)
  elif arguments.operation == "metadata":
    emit_metadata()
  else:
    return run_entrypoint(arguments.binary, arguments.arguments)
  return 0


if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    raise SystemExit(1)
