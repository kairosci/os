# Terminal

[Foot](https://codeberg.org/dnkl/foot) is the default terminal for Arch. It's fast, lightweight, and compatible with even old computers. It does not, however, support native tabs or splits.

If you use Tmux, you may not mind, but if not, we fully support _Alacritty_, _Ghostty_, and _Kitty_ as options as well. Pick your preference under _Install > Terminal_ in the Arch menu.

You start a new terminal using `Super + Return`. (This binding will automatically point to whichever Terminal you've installed via _Install > Terminal_, and you can switch between installed terminals under _Setup > Defaults > Terminal_.)

## Tmux

Tmux provides a consistent, programmable interface for panes, windows (aka tabs), and resumable sessions regardless of your terminal. It even works on remote hosts, so when you're SSH'ing into a server, you can use the same approach.

You start a new Tmux session in a fresh terminal using `Super + Alt + Return`, and because Tmux is a persistent process, you can resume your session even if you close that terminal. Just hit `Ctrl + Space` (called the prefix key) then `s` to see all your active sessions.

Arch ships with an ergonomically-optimized Tmux configuration, which has a lot of keybindings to learn, so keep [the cheatsheet handy](07-hotkeys.md#tmux).
