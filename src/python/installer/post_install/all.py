from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.environ["ARCH_PATH"]) / "src/python"))
from installer.step_runner import run_steps


def main() -> int:
  arch_path = Path(os.environ["ARCH_PATH"])
  arch_install = Path(os.environ.get("ARCH_INSTALL", str(arch_path / "installer")))
  return run_steps(arch_path, arch_install, Path("data/installer/post-install.yml"))


if __name__ == "__main__":
  raise SystemExit(main())
