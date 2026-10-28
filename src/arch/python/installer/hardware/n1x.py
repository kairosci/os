from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import TypedDict, cast

import yaml


class Commands(TypedDict):
  platform_check: list[str]
  match: list[str]
  package_drop: list[str]
  package_add: list[str]
  module_info: list[str]


class Paths(TypedDict):
  system_root_environment: str
  kernel_cmdline: str
  bios_version: str
  modules: str
  module_package_base: str


class FileEntry(TypedDict, total=False):
  path: str
  content: str
  template: str
  cmdline_suffix: str


class Packages(TypedDict):
  default_kernels: list[str]
  nvidia: list[str]
  auxiliary: str
  modules: list[str]
  base_package: str


class Hardware(TypedDict):
  proart_match: str
  proart_pci_vendor: str
  proart_pci_device: str
  prerelease_bios_pattern: str
  root_cmdline_pattern: str


class Statuses(TypedDict):
  matched: int
  complete: int
  failure: int


class Config(TypedDict):
  commands: Commands
  paths: Paths
  files: dict[str, FileEntry]
  paths_to_remove: list[str]
  gpu_enabled_files: list[str]
  gpu_disabled_files: list[str]
  packages: Packages
  hardware: Hardware
  statuses: Statuses
  messages: dict[str, dict[str, str]]
  file_mode: str


def settings() -> tuple[Path, Config]:
  ap = Path(os.environ["ARCH_PATH"])
  config_path = ap / "data/installer/hardware/n1x.yml"
  raw_config: object = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(raw_config, dict):
    raise ValueError
  return ap, cast(Config, raw_config)


def message(config: Config, key: str, **values: str) -> str:
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  localized = config["messages"].get(language, config["messages"]["en"])
  return localized[key].format(**values)


def system_root(config: Config) -> Path:
  if os.geteuid() == 0:
    return Path("/")
  value = os.environ.get(config["paths"]["system_root_environment"])
  if value is not None and value != "":
    return Path(value)
  raise PermissionError(message(config, "not_root"))


def run(
  command: list[str], *, check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess[str]:
  return subprocess.run(command, check=check, text=True, capture_output=capture)


def has_prefix(command: list[str], prefix: list[str]) -> bool:
  return command[:len(prefix)] == prefix


def write_file(root: Path, entry: FileEntry, content: str, mode: int) -> None:
  target = root / entry["path"]
  target.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
      stream.write(content)
      stream.write("\n")
      os.fchmod(stream.fileno(), mode)
      stream.flush()
      os.fsync(stream.fileno())
    os.replace(temporary, target)
    directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def remove_files(root: Path, relative_paths: list[str]) -> None:
  for relative in relative_paths:
    (root / relative).unlink(missing_ok=True)


def installed_kernel(root: Path, config: Config) -> str:
  paths = config["paths"]
  expected = config["packages"]["base_package"]
  package_base = config["paths"]["module_package_base"]
  matches = []
  for file in sorted((root / paths["modules"]).glob(f"*/{package_base}")):
    try:
      if expected in file.read_text(encoding="utf-8").splitlines():
        matches.append(file)
    except OSError:
      continue
  if len(matches) != 1:
    raise RuntimeError(message(config, "kernel_count", count=str(len(matches))))
  assert matches
  return matches[0].parent.name


def configure(root: Path, config: Config) -> None:
  commands = config["commands"]
  files = config["files"]
  packages = config["packages"]
  mode = int(config["file_mode"], 8)

  run([*commands["package_drop"], *packages["default_kernels"]])
  for name in ("input", "sleep", "cppc_rule"):
    write_file(root, files[name], files[name]["content"], mode)

  write_file(root, files["usb4"], files["usb4"]["content"], mode)

  cmdline_path = root / config["paths"]["kernel_cmdline"]
  try:
    root_cmdline = cmdline_path.read_text(encoding="utf-8").strip()
  except OSError:
    root_cmdline = ""
  if re.search(config["hardware"]["root_cmdline_pattern"], root_cmdline) is None:
    raise RuntimeError(message(config, "missing_root"))
  rescue = files["rescue_boot"]
  boot_content = rescue["template"].format(
    root_cmdline=root_cmdline,
    cmdline_suffix=rescue["cmdline_suffix"],
  )
  write_file(root, rescue, boot_content, mode)

  kernel = installed_kernel(root, config)
  try:
    bios_version = (root / config["paths"]["bios_version"]).read_text(encoding="utf-8").strip()
  except OSError:
    bios_version = ""

  remove_files(root, config["paths_to_remove"])
  write_file(root, files["nvidiafb"], files["nvidiafb"]["content"], mode)
  prerelease = re.search(config["hardware"]["prerelease_bios_pattern"], bios_version) is not None
  driver_active = False
  if not prerelease:
    run([*commands["package_add"], *packages["nvidia"]])
    result = run([*commands["module_info"], kernel, *packages["modules"]], check=False, capture=True)
    driver_active = result.returncode == int(config["statuses"]["complete"])
    if not driver_active:
      print(message(config, "dkms_missing", kernel=kernel), file=sys.stderr)
  else:
    print(message(config, "prerelease", bios=bios_version))

  if driver_active:
    remove_files(root, config["gpu_disabled_files"])
    for name in ("nvidia_driver_options", "nvidia_initramfs", "nvidia_cmdline", "brightness_install_hook", "brightness_runtime_hook", "brightness_mkinitcpio"):
      write_file(root, files[name], files[name]["content"], mode)
    print(message(config, "release", bios=bios_version))
  else:
    remove_files(root, config["gpu_enabled_files"])
    write_file(root, files["nvidia_disable"], files["nvidia_disable"]["content"], mode)

  run([*commands["package_add"], packages["auxiliary"]])


def main() -> int:
  _, config = settings()
  if run(config["commands"]["platform_check"], check=False, capture=True).returncode:
    return int(config["statuses"]["complete"])
  try:
    root = system_root(config)
  except PermissionError as error:
    print(error, file=sys.stderr)
    return int(config["statuses"]["failure"])
  print(message(config, "detected"))
  try:
    configure(root, config)
  except RuntimeError as error:
    print(error, file=sys.stderr)
    return int(config["statuses"]["failure"])
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
