from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path

import yaml


def _append_atomically(path: Path, addition: str, marker: str) -> bool:
  if not path.is_file():
    return False
  target = path.resolve(strict=True)
  metadata = target.stat()
  if not stat.S_ISREG(metadata.st_mode):
    return False
  content = target.read_text(encoding="utf-8")
  if marker in content:
    return False

  descriptor, temporary = tempfile.mkstemp(dir=target.parent)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(content)
      output.write(addition)
      output.write("\n")
    os.chmod(temporary, stat.S_IMODE(metadata.st_mode))
    os.replace(temporary, target)
  finally:
    Path(temporary).unlink(missing_ok=True)
  return True


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["nouveau_cursor_setup"]
  nvidia_config = Path(
    os.environ.get(settings["nvidia_config_environment"], settings["nvidia_config_default"])
  )
  if nvidia_config.is_file():
    return 0
  if subprocess.run(settings["command_check"], check=False, stdout=subprocess.DEVNULL).returncode:
    return 0
  environment = {**os.environ, **settings["driver_environment"]}
  result = subprocess.run(settings["driver_command"], check=False, capture_output=True, text=True, env=environment)
  if result.returncode or re.search(settings["driver_pattern"], result.stdout, flags=re.IGNORECASE) is None:
    return 0

  home = Path.home()
  target = home / settings["config_file"]
  if _append_atomically(target, settings["setting"], settings["existing_setting"]):
    language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
    message = settings["messages"].get(language, settings["messages"]["en"])["enabled"]
    print(message)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
