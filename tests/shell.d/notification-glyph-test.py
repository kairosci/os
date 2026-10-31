"""Check that notification commands do not lose their glyph argument."""

from __future__ import annotations

import re

import yaml
from base_test import ROOT, fail_check, pass_check

invalid_glyph = re.compile(r"arch-notification-send[^#]*[ \t]-g([ \t]+(-|\"\$\(arch-i18n|\"[A-Za-z])|[ \t]*$)")
matches = []
for path in (ROOT / "src/arch/commands").iterdir():
  if not path.is_file():
    continue
  for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
    if invalid_glyph.search(line):
      matches.append(f"{path}:{number}:{line}")

if matches:
  fail_check("every notification -g carries a glyph:\n" + "\n".join(matches))
notification = yaml.safe_load((ROOT / "data/cli/notification-time.yml").read_text(encoding="utf-8"))[
    "commands"
]["notification"]
glyph_index = notification.index("-g") if "-g" in notification else None
if glyph_index is None or glyph_index + 1 == len(notification) or not notification[glyph_index + 1].strip():
  fail_check("the time notification keeps its configured glyph")
pass_check("every notification -g carries a glyph")
