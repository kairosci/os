import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(os.environ["ARCH_PATH"]) / "src/python"))
from cli.migration_commands import main


if __name__ == "__main__":
  raise SystemExit(main(Path(__file__)))
