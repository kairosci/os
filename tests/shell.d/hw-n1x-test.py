from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

import yaml

from base_test import ROOT, fail_check, pass_check, test_environment

os.environ.update(test_environment())
sys.path.insert(0, str(ROOT / "src/python"))

from installer.hardware import n1x


config = yaml.safe_load((ROOT / "data/installer/hardware/n1x.yml").read_text(encoding="utf-8"))
setup_steps = yaml.safe_load(
  (ROOT / "data/installer/hardware-setup.yml").read_text(encoding="utf-8")
)["steps"]


def prepare_root(root: Path, bios: str) -> None:
  (root / config["paths"]["kernel_cmdline"]).parent.mkdir(parents=True)
  (root / config["paths"]["kernel_cmdline"]).write_text("root=UUID=test rw\n", encoding="utf-8")
  kernel = root / config["paths"]["modules"] / "7.2.5-9-n1x"
  kernel.mkdir(parents=True)
  (kernel / config["paths"]["module_package_base"]).write_text(
    config["packages"]["base_package"] + "\n", encoding="utf-8"
  )
  version = root / config["paths"]["bios_version"]
  version.parent.mkdir(parents=True)
  version.write_text(bios, encoding="utf-8")


def configure(root: Path, *, proart: bool, module_info: bool = True) -> list[list[str]]:
  calls: list[list[str]] = []

  def run(command: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    calls.append(command)
    status = 0
    if n1x.has_prefix(command, config["commands"]["match"]):
      status = 0 if proart else 1
    elif n1x.has_prefix(command, config["commands"]["module_info"]):
      status = 0 if module_info else 1
    if check and status:
      raise subprocess.CalledProcessError(status, command)
    return subprocess.CompletedProcess(command, status)

  with patch.object(n1x, "run", side_effect=run):
    n1x.configure(root, config)
  return calls


def check(condition: bool, description: str) -> None:
  if condition:
    pass_check(description)
  else:
    fail_check(description)


n1x_step = "src/python/installer/hardware/n1x.py"
nvidia_step = "src/python/installer/hardware/nvidia.py"
check(n1x_step in setup_steps and setup_steps.index(n1x_step) < setup_steps.index(nvidia_step),
      "N1x setup stays before the generic NVIDIA module")

with patch.object(n1x, "run", return_value=subprocess.CompletedProcess([], 1)):
  check(n1x.main() == int(config["statuses"]["complete"]),
        "non-N1x hardware skips all N1x setup")

with tempfile.TemporaryDirectory(prefix="arch-n1x-setup-") as scratch:
  root = Path(scratch)
  prepare_root(root, "1.0.4")
  calls = configure(root, proart=True)
  files = config["files"]

  input_config = root / files["input"]["path"]
  boot_order = root / files["rescue_boot"]["path"]
  proart_rule = root / files["usb4_proart_root_ports"]["path"]
  gpu_config = root / files["nvidia_driver_options"]["path"]
  brightness_hook = root / files["brightness_runtime_hook"]["path"]
  disabled = root / files["nvidia_disable"]["path"]

  check(input_config.is_file() and "i2c_mt65xx i2c_hid_acpi" in input_config.read_text(),
        "the initramfs includes the N1x internal keyboard transport")
  check("root=UUID=test" in boot_order.read_text() and "systemd.unit=multi-user.target" in boot_order.read_text(),
        "the rescue entry preserves root and uses the verbose systemd target")
  check(proart_rule.is_file() and config["hardware"]["proart_pci_device"] in proart_rule.read_text(),
        "the validated ProArt USB4 ports remain awake")
  check(gpu_config.is_file() and "modeset=1 fbdev=1" in gpu_config.read_text(),
        "release firmware enables early NVIDIA display support")
  check(brightness_hook.is_file() and not disabled.exists(),
        "release firmware installs the initramfs brightness hook and enables NVIDIA")
  check(subprocess.run(["bash", "-n", str(root / files["brightness_install_hook"]["path"])], check=False).returncode == 0,
        "the generated initramfs install hook parses")
  check(subprocess.run(["sh", "-n", str(brightness_hook)], check=False).returncode == 0,
        "the generated initramfs runtime hook parses")
  check((gpu_config.stat().st_mode & 0o777) == int(config["file_mode"], 8),
        "generated system configuration has the configured mode")
  check(any(command == [*config["commands"]["package_drop"], *config["packages"]["default_kernels"]]
            for command in calls), "other kernels are removed through the package helper")
  check(any(command == [*config["commands"]["package_add"], *config["packages"]["nvidia"]]
            for command in calls), "release firmware installs the NVIDIA package set")
  check(any(command == [*config["commands"]["package_add"], config["packages"]["auxiliary"]]
            for command in calls), "the on-demand N1x probe receives its PCI utility")

with tempfile.TemporaryDirectory(prefix="arch-n1x-prerelease-") as scratch:
  root = Path(scratch)
  prepare_root(root, "0.60.1")
  calls = configure(root, proart=False)
  files = config["files"]
  generic_usb4 = root / files["usb4"]["path"]
  generic_rule = root / files["usb4_proart_root_ports"]["path"]
  disabled = root / files["nvidia_disable"]["path"]

  proart_check = [*config["commands"]["match"], config["hardware"]["proart_match"]]
  check(proart_check in calls, "setup uses the dedicated ProArt hardware predicate")
  check("pci=hpbussize=0x20" in generic_usb4.read_text() and not generic_rule.exists(),
        "other N1x models receive only their validated USB4 settings")
  check(disabled.is_file() and not (root / files["nvidia_driver_options"]["path"]).exists(),
        "pre-release firmware keeps the NVIDIA stack disabled")
  check(not any(n1x.has_prefix(command, config["commands"]["module_info"]) for command in calls),
        "pre-release firmware skips an unusable NVIDIA module probe")

with tempfile.TemporaryDirectory(prefix="arch-n1x-no-dkms-") as scratch:
  root = Path(scratch)
  prepare_root(root, "1.0.4")
  configure(root, proart=False, module_info=False)
  files = config["files"]
  disabled = root / files["nvidia_disable"]["path"]
  check(disabled.is_file() and not (root / files["nvidia_cmdline"]["path"]).exists(),
        "a failed DKMS build falls back to the firmware framebuffer")

with tempfile.TemporaryDirectory(prefix="arch-n1x-root-policy-") as scratch:
  fixture_root = Path(scratch)
  with patch.object(n1x.os, "geteuid", return_value=0), patch.dict(
    os.environ, {config["paths"]["system_root_environment"]: str(fixture_root)}
  ):
    check(n1x.system_root(config) == Path("/"), "root ignores environment overrides for system paths")
  with patch.object(n1x.os, "geteuid", return_value=1000), patch.dict(
    os.environ, {config["paths"]["system_root_environment"]: str(fixture_root)}
  ):
    check(n1x.system_root(config) == fixture_root, "non-root tests can use an isolated system root")

with tempfile.TemporaryDirectory(prefix="arch-n1x-invalid-root-") as scratch:
  root = Path(scratch)
  prepare_root(root, "1.0.4")
  (root / config["paths"]["kernel_cmdline"]).write_text("quiet rw\n", encoding="utf-8")
  try:
    configure(root, proart=False)
  except RuntimeError as error:
    check(str(error) == n1x.message(config, "missing_root"),
          "an invalid kernel command line stops N1x boot setup")
  else:
    fail_check("an invalid kernel command line stops N1x boot setup")
