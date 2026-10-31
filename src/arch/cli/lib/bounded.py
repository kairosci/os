from __future__ import annotations

import os
import selectors
import subprocess
import time


def _stop(process: subprocess.Popen[bytes], timeout: int) -> None:
  process.kill()
  try:
    process.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
    pass


def run_bounded(
  command: list[str],
  *,
  timeout_seconds: int,
  cleanup_timeout_seconds: int,
  max_output_bytes: int,
  read_chunk_bytes: int,
) -> bytes | None:
  process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  if process.stdout is None:
    _stop(process, cleanup_timeout_seconds)
    return None

  output = bytearray()
  deadline = time.monotonic() + timeout_seconds
  try:
    with selectors.DefaultSelector() as selector:
      selector.register(process.stdout, selectors.EVENT_READ)
      while selector.get_map():
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not selector.select(remaining):
          _stop(process, cleanup_timeout_seconds)
          return None
        chunk = os.read(process.stdout.fileno(), min(read_chunk_bytes, max_output_bytes + 1 - len(output)))
        if not chunk:
          selector.unregister(process.stdout)
          continue
        output.extend(chunk)
        if len(output) > max_output_bytes:
          _stop(process, cleanup_timeout_seconds)
          return None
    remaining = deadline - time.monotonic()
    if remaining <= 0:
      _stop(process, cleanup_timeout_seconds)
      return None
    try:
      status = process.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
      _stop(process, cleanup_timeout_seconds)
      return None
  except OSError:
    _stop(process, cleanup_timeout_seconds)
    return None
  finally:
    process.stdout.close()
  return bytes(output) if status == 0 else None
