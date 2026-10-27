#!/usr/bin/python3

import os
import pathlib
import sys
import tempfile


def usage():
    raise SystemExit("Usage: update-kernel-cmdline.py FILE set KEY=VALUE... | remove KEY...")


if len(sys.argv) < 4 or sys.argv[2] not in {"set", "remove"}:
    usage()

path = pathlib.Path(sys.argv[1])
action = sys.argv[2]
arguments = sys.argv[3:]
if not arguments:
    usage()

keys = []
values = {}
for argument in arguments:
    if any(character.isspace() for character in argument):
        raise SystemExit(f"Invalid kernel command line argument: {argument!r}")
    if action == "set":
        if "=" not in argument:
            raise SystemExit(f"Expected KEY=VALUE: {argument!r}")
        key, value = argument.split("=", 1)
        if not key or not value:
            raise SystemExit(f"Expected non-empty KEY=VALUE: {argument!r}")
        keys.append(key)
        values[key] = argument
    else:
        if "=" in argument or not argument:
            raise SystemExit(f"Expected a key name: {argument!r}")
        keys.append(argument)

if not path.exists() and action == "remove":
    raise SystemExit(0)

try:
    original = path.read_text(encoding="utf-8")
except FileNotFoundError:
    original = ""
tokens = original.split()
tokens = [token for token in tokens if token.partition("=")[0] not in keys]
if action == "set":
    tokens.extend(values[key] for key in keys if key in values)

path.parent.mkdir(parents=True, exist_ok=True)
fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as command_line:
        command_line.write(" ".join(tokens) + "\n")
    os.replace(temporary, path)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
