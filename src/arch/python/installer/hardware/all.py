from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.environ["ARCH_PATH"]) / "src/arch/python"))
from installer.step_runner import main as run


def main() -> int:
  arguments = sys.argv[1:]
  if not arguments or arguments in (["--list"], ["--validate"]):
    arguments.append("data/installer/hardware-setup.yml")
  return run(arguments)


if __name__ == "__main__":
  raise SystemExit(main())
