"""Check that stock Neovim themes use the compatible Catppuccin flavour."""

from __future__ import annotations

from base_test import ROOT, fail_check, pass_check


themes = ROOT / "assets/themes"
matches = [
  str(path)
  for path in themes.rglob("*")
  if path.is_file() and "catppuccin-nvim" in path.read_text(encoding="utf-8", errors="replace")
]
if matches:
  fail_check("stock themes avoid the newer-only catppuccin colorscheme name: " + "\n".join(matches))
pass_check("stock themes avoid the newer-only catppuccin colorscheme name")

neovim_theme = themes / "cosmic/neovim.lua"
if 'colorscheme = "catppuccin-mocha"' not in neovim_theme.read_text(encoding="utf-8"):
  fail_check("os theme uses its flavour colorscheme")
pass_check("os theme uses its flavour colorscheme")
