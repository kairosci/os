from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

import yaml


def settings() -> tuple[Path, dict[str, Any]]:
  arch_path = Path(os.environ["ARCH_PATH"])
  config_path = arch_path / "data/installer/hardware/n1x.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError
  return arch_path, config


def message(config: dict[str, Any], key: str, **values: str) -> str:
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  localized = config["messages"].get(language, config["messages"]["en"])
  return localized[key].format(**values)


def system_root(config: dict[str, Any]) -> Path:
  if os.geteuid() == 0:
    return Path("/")
  value = os.environ.get(config["paths"]["system_root_environment"])
  if value:
    return Path(value)
  raise PermissionError(message(config, "not_root"))


def run(
  command: list[str], *, check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess[str]:
  return subprocess.run(command, check=check, text=True, capture_output=capture)


def has_prefix(command: list[str], prefix: list[str]) -> bool:
  return command[:len(prefix)] == prefix


def write_file(root: Path, entry: dict[str, str], content: str, mode: int) -> None:
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


def installed_kernel(root: Path, config: dict[str, Any]) -> str:
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
  return matches[0].parent.name


def configure(root: Path, config: dict[str, Any]) -> None:
  commands = config["commands"]
  files = config["files"]
  packages = config["packages"]
  mode = int(config["file_mode"], 8)

  run([*commands["package_drop"], *packages["default_kernels"]])
  for name in ("input", "sleep", "cppc_rule"):
    write_file(root, files[name], files[name]["content"], mode)

  proart = run(
    [*commands["match"], config["hardware"]["proart_match"]], check=False, capture=True
  ).returncode == int(config["statuses"]["matched"])
  write_file(
    root,
    files["usb4_proart"] if proart else files["usb4"],
    files["usb4_proart"]["content"] if proart else files["usb4"]["content"],
    mode,
  )
  if proart:
    entry = files["usb4_proart_root_ports"]
    content = entry["content"]
    for key in ("proart_pci_vendor", "proart_pci_device"):
      content = content.replace(f"@{key.upper()}@", config["hardware"][key])
    write_file(root, entry, content, mode)

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
