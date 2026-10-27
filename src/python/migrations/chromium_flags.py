from __future__ import annotations

from pathlib import Path


def add_extension(
  config_file: Path,
  extension_marker: str,
  load_extension_option: str,
  extension_path: str,
) -> bool:
  if not config_file.is_file():
    return False

  contents = config_file.read_bytes()
  if extension_marker.encode("utf-8") in contents:
    return False

  option = load_extension_option.encode("utf-8")
  extension = extension_path.encode("utf-8")
  output = []
  has_load_extension = False
  lines = contents.split(b"\n")
  for index, body in enumerate(lines):
    ending = b"\n" if index < len(lines) - 1 else b""
    if ending and body.endswith(b"\r"):
      body = body[:-1]
      ending = b"\r\n"
    if body.startswith(option):
      body += b"," + extension
      has_load_extension = True
    output.append(body + ending)

  if has_load_extension:
    updated = b"".join(output)
  else:
    updated = contents
    if updated and not updated.endswith(b"\n"):
      updated += b"\n"
    updated += option + extension + b"\n"

  config_file.write_bytes(updated)
  return True
