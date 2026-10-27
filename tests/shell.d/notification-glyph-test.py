"""Check that notification commands do not lose their glyph argument."""

from __future__ import annotations

import re

from base_test import ROOT, fail_check, pass_check


invalid_glyph = re.compile(r"arch-notification-send[^#]*[ \t]-g([ \t]+(-|\"\$\(arch-i18n|\"[A-Za-z])|[ \t]*$)")
matches = []
for path in (ROOT / "src/cli").iterdir():
  if not path.is_file():
    continue
  for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
    if invalid_glyph.search(line):
      matches.append(f"{path}:{number}:{line}")

if matches:
  fail_check("every notification -g carries a glyph:\n" + "\n".join(matches))
pass_check("every notification -g carries a glyph")
