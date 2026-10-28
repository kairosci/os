"""Install SPI keyboard support on MacBook models that require it."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/apple/macbook-spi-keyboard.yml").read_text(encoding="utf-8"),
  )
  model = next(
    (
      item for item in config["models"]
      if subprocess.run([*config["match_command"], item["pattern"]], check=False).returncode == 0
    ),
    None,
  )
  if model is None:
    return int(config["statuses"]["complete"])

  subprocess.run(config["install_packages"], check=True)
  content = config["content_template"].format(modules=" ".join(model["modules"]))
  with tempfile.TemporaryDirectory() as temporary_directory:
    source = Path(temporary_directory) / Path(config["target"]).name
    source.write_text(content, encoding="utf-8")
    subprocess.run([*config["install_file"], str(source), config["target"]], check=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
