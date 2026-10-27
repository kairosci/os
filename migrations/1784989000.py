from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def load_config(root: Path) -> dict:
  config_path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError()
  return config


def entry_id(value: object, object_id_key: str) -> object:
  if isinstance(value, str):
    return value
  if isinstance(value, dict):
    return value.get(object_id_key) or ""
  return ""


def move_before(entries: object, item_id: str, before_id: str, object_id_key: str) -> bool:
  if not isinstance(entries, list):
    return False

  item_index = next((index for index, entry in enumerate(entries) if entry_id(entry, object_id_key) == item_id), None)
  before_index = next((index for index, entry in enumerate(entries) if entry_id(entry, object_id_key) == before_id), None)
  if item_index is None or before_index is None or item_index < before_index:
    return False

  item = entries.pop(item_index)
  new_before_index = next(index for index, entry in enumerate(entries) if entry_id(entry, object_id_key) == before_id)
  entries.insert(new_before_index, item)
  return True


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  subprocess.run([*config["commands"]["i18n"], config["messages"]["reason"]], check=False)

  config_file = Path.home() / config["paths"]["shell_config"]
  if not config_file.is_file() or config_file.stat().st_size == 0:
    return int(config["statuses"]["success"])

  try:
    document = json.loads(config_file.read_text(encoding="utf-8"))
  except (OSError, UnicodeDecodeError, json.JSONDecodeError):
    return int(config["statuses"]["success"])

  settings = config["values"]
  bar = document.get(settings["bar_key"]) if isinstance(document, dict) else None
  layout = bar.get(settings["layout_key"]) if isinstance(bar, dict) else None
  entries = layout.get(settings["section_key"]) if isinstance(layout, dict) else None
  item_id = settings["values_join_separator"].join(settings["item_id"])
  before_id = settings["values_join_separator"].join(settings["before_id"])
  changed = move_before(entries, item_id, before_id, settings["object_id_key"])
  if not changed:
    return int(config["statuses"]["success"])

  config_file.parent.mkdir(parents=True, exist_ok=True)
  temporary_file = None
  try:
    with tempfile.NamedTemporaryFile(
      mode="w",
      encoding="utf-8",
      dir=config_file.parent,
      prefix=f".{config_file.name}.",
      delete=False,
    ) as output:
      temporary_file = Path(output.name)
      json.dump(document, output, ensure_ascii=False, indent=2)
      output.write("\n")
    os.replace(temporary_file, config_file)
  finally:
    if temporary_file is not None:
      temporary_file.unlink(missing_ok=True)

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
