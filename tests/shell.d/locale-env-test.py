"""Check locale defaults and Unicode handling in the Bash environment."""

from __future__ import annotations

import subprocess

from base_test import ROOT, fail_check, pass_check, test_environment


environment_file = ROOT / "default/bash/envs"
command = 'source "$1"; printf "%s" "$LANG"'

without_locale = test_environment()
without_locale.pop("LANG", None)
result = subprocess.run(
  ["bash", "-c", command, "bash", str(environment_file)],
  capture_output=True,
  text=True,
  env=without_locale,
  check=False,
)
if result.returncode != 0 or not result.stdout:
  fail_check("bash env sets a locale when none is inherited")
pass_check("bash env sets a locale when none is inherited")

if "utf-8" not in result.stdout.casefold() and "utf8" not in result.stdout.casefold():
  fail_check(f"bash env picks a UTF-8 locale: actual {result.stdout}")
pass_check("bash env picks a UTF-8 locale")

inherited = test_environment(LANG="en_DK.UTF-8")
result = subprocess.run(
  ["bash", "-c", command, "bash", str(environment_file)],
  capture_output=True,
  text=True,
  env=inherited,
  check=False,
)
if result.returncode != 0 or result.stdout != "en_DK.UTF-8":
  fail_check(f"bash env preserves the inherited locale: actual {result.stdout}")
pass_check("bash env preserves the inherited locale")

glyph_environment = test_environment()
glyph_environment.pop("LANG", None)
glyph = subprocess.run(
  ["bash", "-c", 'source "$1"; printf "\\U000F17A9"', "bash", str(environment_file)],
  capture_output=True,
  text=True,
  env=glyph_environment,
  check=False,
)
if glyph.returncode != 0 or "\\U" in glyph.stdout:
  fail_check(f"bash env locale renders Unicode escapes: actual {glyph.stdout}")
pass_check("bash env locale renders unicode escapes")
