"""Keep Qualcomm device trees listed in the UKI configuration."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import TypedDict, TypeGuard

import yaml


class DtbUkiConfig(TypedDict):
  hardware_check: list[str]
  install_packages: list[str]
  dtb_root_environment: str
  dtb_root_default: str
  dtb_subdirectory: str
  kernel_dtb_glob: str
  dtb_directory_environment: str
  uki_config_environment: str
  uki_config_default: str
  dtb_patterns: list[str]
  excluded_suffix: str
  managed_begin: str
  managed_end: str
  generated_comments: list[str]
  uki_key: str
  new_file_mode: str
  rebuild_environment: str
  messages: dict[str, dict[str, str]]
  statuses: dict[str, int]


def _is_string_list(value: object) -> TypeGuard[list[str]]:
  return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_string_mapping(value: object) -> TypeGuard[dict[str, str]]:
  return isinstance(value, dict) and all(
    isinstance(key, str) and isinstance(item, str) for key, item in value.items()
  )


def _is_dtb_uki_config(value: object) -> TypeGuard[DtbUkiConfig]:
  if not isinstance(value, dict):
    return False
  string_keys = (
    "dtb_root_environment", "dtb_root_default", "dtb_subdirectory", "kernel_dtb_glob",
    "dtb_directory_environment", "uki_config_environment", "uki_config_default", "excluded_suffix",
    "managed_begin", "managed_end", "uki_key", "new_file_mode", "rebuild_environment",
  )
  messages = value.get("messages")
  statuses = value.get("statuses")
  return (
    _is_string_list(value.get("hardware_check"))
    and _is_string_list(value.get("install_packages"))
    and all(isinstance(value.get(key), str) for key in string_keys)
    and _is_string_list(value.get("dtb_patterns"))
    and _is_string_list(value.get("generated_comments"))
    and isinstance(messages, dict)
    and all(isinstance(language, str) and _is_string_mapping(catalog) for language, catalog in messages.items())
    and isinstance(messages.get("en"), dict)
    and isinstance(statuses, dict)
    and type(statuses.get("complete")) is int
  )


def translate(messages: dict[str, dict[str, str]], key: str) -> str:
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  return messages.get(language, messages["en"])[key]


def device_trees(directory: Path, config: DtbUkiConfig) -> list[Path]:
  trees = {
    path
    for pattern in config["dtb_patterns"]
    for path in directory.glob(pattern)
    if path.is_file() and not path.name.endswith(config["excluded_suffix"])
  }
  return sorted(trees)


def managed_content(existing: str, trees: list[Path], config: DtbUkiConfig) -> str:
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
  root = Path(os.environ["AP"])
  config: object = yaml.safe_load(
    (root / "data/installer/hardware/qualcomm/dtb-uki.yml").read_text(encoding="utf-8"),
  )
  if not _is_dtb_uki_config(config):
    raise ValueError("invalid Qualcomm device tree configuration")
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
      if rebuild_request is not None and rebuild_request != "":
        Path(rebuild_request).write_text("", encoding="utf-8")
  finally:
    temporary.unlink(missing_ok=True)

  print(translate(messages, "listed_trees").format(count=len(trees), path=uki_config))
  return int(statuses["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
