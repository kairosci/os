"""Check the default and inherited editor values in the Bash environment."""

from __future__ import annotations

import subprocess

from base_test import ROOT, fail_check, pass_check, test_environment


environment_file = ROOT / "default/bash/envs"
command = 'source "$1"; printf "%s" "$EDITOR"'
default_environment = test_environment()
default_environment.pop("EDITOR", None)
default_environment.pop("SUDO_EDITOR", None)
result = subprocess.run(
  ["bash", "-c", command, "bash", str(environment_file)],
  capture_output=True,
  text=True,
  env=default_environment,
  check=False,
)
if result.returncode != 0 or result.stdout != "nvim":
  fail_check(f"Bash env provides Neovim as the default editor: {result.stdout}{result.stderr}")
pass_check("bash env provides a default editor")

inherited_environment = test_environment(EDITOR="helix")
result = subprocess.run(
  ["bash", "-c", command, "bash", str(environment_file)],
  capture_output=True,
  text=True,
  env=inherited_environment,
  check=False,
)
if result.returncode != 0 or result.stdout != "helix":
  fail_check(f"Bash env preserves the inherited editor: {result.stdout}{result.stderr}")
pass_check("bash env preserves the inherited editor")

sudo_command = 'source "$1"; printf "%s" "$SUDO_EDITOR"'
result = subprocess.run(
  ["bash", "-c", sudo_command, "bash", str(environment_file)],
  capture_output=True,
  text=True,
  env=default_environment,
  check=False,
)
if result.returncode != 0 or result.stdout != "nvim":
  fail_check(f"sudo uses the default editor: {result.stdout}{result.stderr}")
pass_check("sudo uses the default editor")
