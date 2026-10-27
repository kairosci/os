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


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  subprocess.run([*config["commands"]["i18n"], config["messages"]["reason"]], check=False)

  shell_config = Path.home() / config["paths"]["shell_config"]
  if not shell_config.is_file():
    return int(config["statuses"]["success"])

  try:
    document = json.loads(shell_config.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError):
    return int(config["statuses"]["success"])

  if not isinstance(document, dict):
    return int(config["statuses"]["success"])
  bar = document.get(config["keys"]["bar"])
  if not isinstance(bar, dict):
    return int(config["statuses"]["success"])
  layout = bar.get(config["keys"]["layout"])
  if not isinstance(layout, dict):
    return int(config["statuses"]["success"])

  changed = False
  widget_id = config["values"]["widget_id_separator"].join(config["values"]["widget_id_parts"])
  old_format = config["values"]["old_format"]
  new_format = config["values"]["new_format"]
  for section in layout.values():
    if not isinstance(section, list):
      continue
    for widget in section:
      if not isinstance(widget, dict) or widget.get(config["keys"]["widget_id"]) != widget_id:
        continue
      if widget.get(config["keys"]["format"]) == old_format:
        widget[config["keys"]["format"]] = new_format
        changed = True

  if not changed:
    return int(config["statuses"]["success"])

  temporary_path = None
  try:
    with tempfile.NamedTemporaryFile(
      mode="w",
      encoding="utf-8",
      dir=shell_config.parent,
      delete=False,
    ) as temporary:
      temporary_path = Path(temporary.name)
      json.dump(document, temporary, ensure_ascii=False, indent=2)
      temporary.write("\n")
      temporary.flush()
      os.fsync(temporary.fileno())
    temporary_path.replace(shell_config)
  finally:
    if temporary_path is not None:
      temporary_path.unlink(missing_ok=True)

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
