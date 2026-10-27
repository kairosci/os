"""Keep Qualcomm device trees listed in the UKI configuration."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import yaml


def translate(messages: dict, key: str) -> str:
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  return messages.get(language, messages["en"])[key]


def device_trees(directory: Path, config: dict) -> list[Path]:
  trees = {
    path
    for pattern in config["dtb_patterns"]
    for path in directory.glob(pattern)
    if path.is_file() and not path.name.endswith(config["excluded_suffix"])
  }
  return sorted(trees)


def managed_content(existing: str, trees: list[Path], config: dict) -> str:
  begin = config["managed_begin"]
  end = config["managed_end"]
  remaining = []
  managed = False
  for line in existing.splitlines():
    if line == begin:
      managed = True
      continue
    if managed and line == end:
      managed = False
      continue
    if not managed:
      remaining.append(line)

  block = [
    begin,
    *config["generated_comments"],
    "[UKI]",
    f"{config['uki_key']}={' '.join(map(str, trees))}",
    end,
  ]
  return "\n".join([*remaining, *block, ""])


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/qualcomm/dtb-uki.yml").read_text(encoding="utf-8"),
  )
  statuses = config["statuses"]
  if subprocess.run(config["hardware_check"], check=False).returncode != int(statuses["complete"]):
    return int(statuses["complete"])
  subprocess.run(config["install_packages"], check=True)

  dtb_root = Path(os.environ.get(config["dtb_root_environment"]) or config["dtb_root_default"])
  dtb_directory = dtb_root / config["dtb_subdirectory"]
  for candidate in sorted(dtb_root.glob(config["kernel_dtb_glob"])):
    if candidate.is_dir():
      dtb_directory = candidate
      break
  dtb_directory = Path(os.environ.get(config["dtb_directory_environment"]) or dtb_directory)
  uki_config = Path(os.environ.get(config["uki_config_environment"]) or config["uki_config_default"])
  trees = device_trees(dtb_directory, config)

  messages = config["messages"]
  if not trees:
    print(translate(messages, "no_trees").format(directory=dtb_directory))
    return int(statuses["complete"])

  uki_config.parent.mkdir(parents=True, exist_ok=True)
  existing = uki_config.read_text(encoding="utf-8") if uki_config.is_file() else ""
  content = managed_content(existing, trees, config)
  descriptor, temporary_name = tempfile.mkstemp(prefix=f"{uki_config.name}.", dir=uki_config.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
      stream.write(content)
    if uki_config.is_file():
      shutil.copystat(uki_config, temporary)
    else:
      temporary.chmod(int(config["new_file_mode"], 8))

    if uki_config.is_file() and temporary.read_bytes() == uki_config.read_bytes():
      temporary.unlink()
    else:
      os.replace(temporary, uki_config)
      rebuild_request = os.environ.get(config["rebuild_environment"])
      if rebuild_request:
        Path(rebuild_request).write_text("", encoding="utf-8")
  finally:
    temporary.unlink(missing_ok=True)

  print(translate(messages, "listed_trees").format(count=len(trees), path=uki_config))
  return int(statuses["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
