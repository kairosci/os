from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  return subprocess.run(config["video_decode"]["command"], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
