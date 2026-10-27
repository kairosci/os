-- Define terminal tag so themes and bindings can single terminals out. Arch
-- launches TUIs and its own terminal windows under dedicated app-ids
-- (org.arch.btop, org.arch.terminal, TUI.tile, ...), so match those too.
-- The class is matched in full, so foot's other app-id needs spelling out.
o.window(
  "(Alacritty|kitty|com.mitchellh.ghostty|foot|org\\.codeberg\\.dnkl\\.foot|wezterm|org\\.arch\\.terminal|org\\.arch\\.btop|TUI\\..*)",
  { tag = "+terminal" }
)
