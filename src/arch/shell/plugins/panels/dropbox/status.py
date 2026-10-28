import heapq
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, TypeGuard


class DropboxFile(TypedDict):
  name: str
  path: str
  folder: str
  modifiedTs: int
  sizeBytes: int


def _is_string_mapping(value: object) -> TypeGuard[dict[str, object]]:
  return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _is_quota_mapping(value: object) -> TypeGuard[dict[str, int]]:
  return isinstance(value, dict) and all(
    isinstance(key, str) and type(quota) is int and quota >= 0 for key, quota in value.items()
  )


def load_plan_quotas() -> dict[str, int]:
  root = Path(os.environ["AP"])
  path = root / "data/python/dropbox-plan-quotas.json"
  with path.open("r", encoding="utf-8") as handle:
    quotas: object = json.load(handle)
  if not _is_quota_mapping(quotas):
    raise ValueError("Dropbox plan quota data must map plan names to non-negative byte counts")
  return quotas


PLAN_QUOTAS = load_plan_quotas()


def read_info() -> dict[str, object]:
  info_path = Path.home() / ".dropbox" / "info.json"
  if not info_path.exists():
    return {}
  try:
    with info_path.open("r", encoding="utf-8") as handle:
      info: object = json.load(handle)
      return info if _is_string_mapping(info) else {}
  except (OSError, json.JSONDecodeError):
    return {}


def dropbox_account(info: dict[str, object]) -> dict[str, object]:
  for key in ("personal", "business"):
    account = info.get(key)
    if _is_string_mapping(account):
      return account
  return {}


def command_output(command: list[str]) -> tuple[int, str]:
  try:
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=4)
  except (OSError, subprocess.TimeoutExpired):
    return 1, ""
  return completed.returncode, (completed.stdout + completed.stderr).strip()


def scan_dropbox(path: str, limit: int) -> tuple[int, list[DropboxFile]]:
  total = 0
  counter = 0
  recent: list[tuple[int, int, DropboxFile]] = []
  try:
    for root, dirs, files in os.walk(path):
      dirs[:] = [name for name in dirs if not os.path.islink(os.path.join(root, name))]
      for name in files:
        file_path = os.path.join(root, name)
        if os.path.islink(file_path):
          continue
        try:
          stat = os.stat(file_path)
        except OSError:
          continue
        total += stat.st_size
        rel = os.path.relpath(file_path, path)
        folder = os.path.dirname(rel)
        row: DropboxFile = {
          "name": name,
          "path": file_path,
          "folder": "/" if folder in ("", ".") else folder,
          "modifiedTs": int(stat.st_mtime),
          "sizeBytes": stat.st_size,
        }
        counter += 1
        entry = (row["modifiedTs"], counter, row)
        if len(recent) < limit:
          heapq.heappush(recent, entry)
        else:
          heapq.heappushpop(recent, entry)
  except OSError:
    return 0, []
  rows = [entry[2] for entry in sorted(recent, reverse=True)]
  return total, rows


def main() -> None:
  limit = 25
  if len(sys.argv) > 1:
    try:
      limit = max(1, min(100, int(sys.argv[1])))
    except ValueError:
      limit = 25

  dropbox_cli = shutil.which("dropbox-cli")
  info = read_info()
  account = dropbox_account(info)
  account_path = account.get("path")
  if not isinstance(account_path, str):
    account_path = ""
  plan = account.get("subscription_type")
  if not isinstance(plan, str):
    plan = ""
  quota = PLAN_QUOTAS.get(plan.lower(), 0)
  authenticated = account_path != "" and Path(account_path).exists()

  running = False
  status_text = "Not installed"
  if dropbox_cli is not None:
    status_exit, status_output = command_output([dropbox_cli, "status"])
    status_text = status_output if status_exit == 0 and status_output else "Stopped"
    lowered = status_text.lower()
    stopped = "not running" in lowered or "isn't running" in lowered or lowered == "stopped"
    running = status_exit == 0 and status_output != "" and not stopped

  used, files = scan_dropbox(account_path, limit) if authenticated else (0, [])
  usage_percent = (used / quota * 100) if quota > 0 else 0

  print(json.dumps({
    "ok": True,
    "installed": dropbox_cli is not None,
    "running": running,
    "authenticated": authenticated,
    "statusText": status_text,
    "accountPath": account_path,
    "plan": plan,
    "usedBytes": used,
    "quotaBytes": quota,
    "usagePercent": usage_percent,
    "quotaKnown": quota > 0,
    "files": files,
  }))


if __name__ == "__main__":
  main()
