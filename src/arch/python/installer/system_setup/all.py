from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.environ["ARCH_PATH"]) / "src/arch/python"))
from installer.step_runner import run_steps


def main() -> int:
  ap = Path(os.environ["ARCH_PATH"])
  arch_install = Path(os.environ.get("ARCH_INSTALL", str(ap / "installer")))
  return run_steps(ap, arch_install, Path("data/installer/system-setup.yml"))


if __name__ == "__main__":
  raise SystemExit(main())
