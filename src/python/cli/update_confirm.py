from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/update-confirm.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid update confirmation configuration")
  return config


def localized(config: dict[str, Any], key: str, *arguments: str) -> str:
  result = subprocess.run(
    [*config["commands"]["i18n"], key, *arguments],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def main() -> int:
  try:
    config = load_config()
    lines: list[str] = []
    for item in config["style"]["lines"]:
      if "message" in item:
        key = config["strings"][item["message"]]
        message = localized(config, key, *item.get("arguments", []))
        lines.append(f"{item.get('prefix', '')}{message}")
      else:
        lines.append(item["text"])
    subprocess.run([*config["commands"]["style"], *lines], check=False)
    print()

    affirmative = localized(config, config["messages"]["yes"])
    negative = localized(config, config["messages"]["no"])
    question = localized(config, config["messages"]["continue"])
    result = subprocess.run(
      [
        *config["commands"]["confirm"],
        config["flags"]["affirmative"], affirmative,
        config["flags"]["negative"], negative,
        question,
      ],
      check=False,
    )
    if result.returncode != int(config["statuses"]["confirmed"]):
      print(localized(config, config["messages"]["cancelled"]))
      return int(config["statuses"]["cancelled"])
    return int(config["statuses"]["confirmed"])
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    return int(config["statuses"]["failed"]) if isinstance(locals().get("config"), dict) else 1


if __name__ == "__main__":
  raise SystemExit(main())
