from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import yaml


def _run_ignored(command: list[str], *, quiet: bool) -> None:
  try:
    subprocess.run(
      command,
      check=False,
      stdout=subprocess.DEVNULL if quiet else None,
      stderr=subprocess.DEVNULL,
    )
  except OSError:
    pass


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["asus_mic_setup"]
  if subprocess.run(settings["predicate"], check=False).returncode:
    return 0

  codec_root = Path(settings["codec_root"])
  codec_pattern = re.compile(settings["codec_pattern"])
  card_pattern = re.compile(settings["card_pattern"])
  for codec in sorted(codec_root.glob(settings["codec_glob"])):
    try:
      content = codec.read_text(encoding="utf-8", errors="replace")
    except OSError:
      continue
    if codec_pattern.search(content) is None:
      continue
    card = card_pattern.search(str(codec))
    if card is not None:
      card_number = card.group(1)
      for command in settings["mixer_commands"]:
        _run_ignored([argument.format(card=card_number) for argument in command], quiet=True)
      _run_ignored(
        [argument.format(card=card_number) for argument in settings["privilege_command"]],
        quiet=False,
      )
    break
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
