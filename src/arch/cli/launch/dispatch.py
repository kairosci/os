from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from itertools import islice
from pathlib import Path
from typing import TypedDict, cast

import yaml

from arch.cli.lib.bounded import run_bounded


class Launcher(TypedDict):
  command: list[str]
  working_directory: bool
  terminal_directory: bool


class TerminalDirectory(TypedDict):
  active_window_command: list[str]
  kitty_command: list[str]
  active_pid_pattern: str
  pid_pattern: str
  runtime_directory_environment: str
  home_environment: str
  proc_root: str
  shells_file: str
  task_directory: str
  children_filename: str
  cwd_filename: str
  executable_filename: str
  kitty_socket_prefix: str
  kitty_target_prefix: str
  pid_option_prefix: str
  directory_option_prefix: str
  encoding: str
  tabs_key: str
  windows_key: str
  cwd_key: str
  active_window_timeout: int
  kitty_timeout: int
  cleanup_timeout: int
  maximum_command_output: int
  read_chunk_bytes: int
  maximum_task_files: int
  maximum_children_file_bytes: int
  maximum_child_processes: int
  maximum_shells_file_bytes: int
  maximum_pid_digits: int


class TuiSettings(TypedDict):
  command: list[str]
  execute_option: str
  app_id_option_prefix: str
  default_app_id_prefix: str
  clients_command: list[str]
  match_fields: list[str]
  match_prefix: str
  match_suffix: str
  case_insensitive: bool
  address_placeholder: str
  focus_commands: list[list[str]]
  address_field: str
  address_pattern: str
  command_timeout: int
  maximum_clients_output: int
  maximum_client_count: int
  maximum_address_length: int


class Statuses(TypedDict):
  configuration_error: int
  command_error: int
  invalid_arguments: int
  success: int


class Settings(TypedDict):
  launchers: dict[str, Launcher]
  statuses: Statuses
  command_error_message: str
  unknown_launcher_message: str
  terminal_directory: TerminalDirectory
  tui: TuiSettings
  tui_usage_message: str
  tui_focus_usage_message: str
  invalid_app_id_message: str


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"{label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError(f"{label} must be a non-empty argv list")
  return cast(list[str], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"{label} must be non-empty text")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise ValueError(f"{label} must be an exit status")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/launchers.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "configuration")
  raw_launchers = _mapping(document.get("launchers"), "launchers")
  launchers: dict[str, Launcher] = {}
  for name, raw_launcher in raw_launchers.items():
    values = _mapping(raw_launcher, name)
    command = _strings(values.get("command"), f"{name}.command")
    working_directory = values.get("working_directory", False)
    terminal_directory = values.get("terminal_directory", False)
    if not isinstance(working_directory, bool) or not isinstance(terminal_directory, bool):
      raise TypeError(f"{name} directory options must be booleans")
    if working_directory and terminal_directory:
      raise ValueError(f"{name} cannot use both directory modes")
    launchers[name] = {
      "command": command,
      "working_directory": working_directory,
      "terminal_directory": terminal_directory,
    }
  raw_statuses = _mapping(document.get("statuses"), "statuses")
  messages = _mapping(document.get("messages"), "messages")
  directory = _mapping(document.get("terminal_directory"), "terminal_directory")
  tui_values = _mapping(document.get("tui"), "tui")
  directory_commands = _mapping(directory.get("commands"), "terminal_directory.commands")
  directory_values = _mapping(directory.get("values"), "terminal_directory.values")
  directory_environment = _mapping(directory.get("environment"), "terminal_directory.environment")
  directory_paths = _mapping(directory.get("paths"), "terminal_directory.paths")
  directory_limits = _mapping(directory.get("limits"), "terminal_directory.limits")

  def tui_text(key: str) -> str:
    return _text(tui_values.get(key), f"tui.{key}")

  def tui_integer(key: str) -> int:
    value = tui_values.get(key)
    if type(value) is not int or value <= 0:
      raise ValueError(f"tui.{key} must be positive")
    return value

  match_fields = _strings(tui_values.get("match_fields"), "tui.match_fields")
  if any(not field.replace("_", "").isalnum() for field in match_fields):
    raise ValueError("tui.match_fields contains an invalid JSON key")
  raw_case_insensitive = tui_values.get("case_insensitive")
  if not isinstance(raw_case_insensitive, bool):
    raise TypeError("tui.case_insensitive must be a boolean")
  raw_focus_commands = tui_values.get("focus_commands")
  if not isinstance(raw_focus_commands, list) or not raw_focus_commands:
    raise ValueError("tui.focus_commands must be a non-empty list")
  focus_commands = [
    _strings(command, "tui.focus_commands[]")
    for command in raw_focus_commands
  ]
  address_placeholder = tui_text("address_placeholder")
  if any(not any(address_placeholder in part for part in command) for command in focus_commands):
    raise ValueError("each tui focus command must include its address placeholder")
  tui: TuiSettings = {
    "command": _strings(tui_values.get("command"), "tui.command"),
    "execute_option": tui_text("execute_option"),
    "app_id_option_prefix": tui_text("app_id_option_prefix"),
    "default_app_id_prefix": tui_text("default_app_id_prefix"),
    "clients_command": _strings(tui_values.get("clients_command"), "tui.clients_command"),
    "match_fields": match_fields,
    "match_prefix": tui_text("match_prefix"),
    "match_suffix": tui_text("match_suffix"),
    "case_insensitive": raw_case_insensitive,
    "focus_commands": focus_commands,
    "address_field": tui_text("address_field"),
    "address_pattern": tui_text("address_pattern"),
    "address_placeholder": address_placeholder,
    "command_timeout": tui_integer("command_timeout_seconds"),
    "maximum_clients_output": tui_integer("maximum_clients_output_bytes"),
    "maximum_client_count": tui_integer("maximum_client_count"),
    "maximum_address_length": tui_integer("maximum_address_length"),
  }
  try:
    re.compile(tui["match_prefix"] + tui["match_suffix"])
    re.compile(tui["address_pattern"])
  except re.error as error:
    raise ValueError("tui match expression is invalid") from error

  def terminal_text(section: dict[str, object], key: str) -> str:
    return _text(section.get(key), f"terminal_directory.{key}")

  def terminal_integer(key: str) -> int:
    value = directory_limits.get(key)
    if type(value) is not int or value <= 0:
      raise ValueError(f"terminal_directory.limits.{key} must be positive")
    return value

  terminal_directory: TerminalDirectory = {
    "active_window_command": _strings(directory_commands.get("active_window"), "active_window"),
    "kitty_command": _strings(directory_commands.get("kitty"), "kitty"),
    "active_pid_pattern": terminal_text(directory_values, "active_pid_pattern"),
    "pid_pattern": terminal_text(directory_values, "pid_pattern"),
    "runtime_directory_environment": terminal_text(directory_environment, "runtime_directory"),
    "home_environment": terminal_text(directory_environment, "home"),
    "proc_root": terminal_text(directory_paths, "proc_root"),
    "shells_file": terminal_text(directory_paths, "shells_file"),
    "task_directory": terminal_text(directory_paths, "task_directory"),
    "children_filename": terminal_text(directory_paths, "children_filename"),
    "cwd_filename": terminal_text(directory_paths, "cwd_filename"),
    "executable_filename": terminal_text(directory_paths, "executable_filename"),
    "kitty_socket_prefix": terminal_text(directory_values, "kitty_socket_prefix"),
    "kitty_target_prefix": terminal_text(directory_values, "kitty_target_prefix"),
    "pid_option_prefix": terminal_text(directory_values, "pid_option_prefix"),
    "directory_option_prefix": terminal_text(directory_values, "directory_option_prefix"),
    "encoding": terminal_text(directory_values, "encoding"),
    "tabs_key": terminal_text(directory_values, "tabs_key"),
    "windows_key": terminal_text(directory_values, "windows_key"),
    "cwd_key": terminal_text(directory_values, "cwd_key"),
    "active_window_timeout": terminal_integer("active_window_timeout_seconds"),
    "kitty_timeout": terminal_integer("kitty_timeout_seconds"),
    "cleanup_timeout": terminal_integer("cleanup_timeout_seconds"),
    "maximum_command_output": terminal_integer("maximum_command_output_bytes"),
    "read_chunk_bytes": terminal_integer("read_chunk_bytes"),
    "maximum_task_files": terminal_integer("maximum_task_files"),
    "maximum_children_file_bytes": terminal_integer("maximum_children_file_bytes"),
    "maximum_child_processes": terminal_integer("maximum_child_processes"),
    "maximum_shells_file_bytes": terminal_integer("maximum_shells_file_bytes"),
    "maximum_pid_digits": terminal_integer("maximum_pid_digits"),
  }
  try:
    if re.compile(terminal_directory["active_pid_pattern"]).groups != 1:
      raise ValueError("terminal_directory active PID pattern needs one capture")
    re.compile(terminal_directory["pid_pattern"])
  except re.error as error:
    raise ValueError("terminal_directory PID pattern is invalid") from error
  return {
    "launchers": launchers,
    "statuses": {
      "configuration_error": _status(raw_statuses.get("configuration_error"), "configuration_error"),
      "command_error": _status(raw_statuses.get("command_error"), "command_error"),
      "invalid_arguments": _status(raw_statuses.get("invalid_arguments"), "invalid_arguments"),
      "success": _status(raw_statuses.get("success"), "success"),
    },
    "command_error_message": _text(messages.get("command_error"), "messages.command_error"),
    "unknown_launcher_message": _text(messages.get("unknown_launcher"), "messages.unknown_launcher"),
    "terminal_directory": terminal_directory,
    "tui": tui,
    "tui_usage_message": _text(messages.get("tui_usage"), "messages.tui_usage"),
    "tui_focus_usage_message": _text(messages.get("tui_focus_usage"), "messages.tui_focus_usage"),
    "invalid_app_id_message": _text(messages.get("invalid_app_id"), "messages.invalid_app_id"),
  }


def _bounded_command(command: list[str], settings: Settings, timeout: int) -> bytes | None:
  directory = settings["terminal_directory"]
  try:
    return run_bounded(
      command,
      timeout_seconds=timeout,
      cleanup_timeout_seconds=directory["cleanup_timeout"],
      max_output_bytes=directory["maximum_command_output"],
      read_chunk_bytes=directory["read_chunk_bytes"],
    )
  except OSError:
    return None


def _valid_pid(value: str, settings: Settings) -> bool:
  directory = settings["terminal_directory"]
  if len(value) > directory["maximum_pid_digits"] or not re.fullmatch(directory["pid_pattern"], value):
    return False
  return int(value) > 0


def _active_pid(settings: Settings) -> str | None:
  directory = settings["terminal_directory"]
  output = _bounded_command(
    directory["active_window_command"], settings, directory["active_window_timeout"]
  )
  if output is None:
    return None
  text = output.decode(directory["encoding"], errors="surrogateescape")
  for line in text.splitlines():
    match = re.search(directory["active_pid_pattern"], line)
    if match is not None:
      pid = match.group(1)
      if isinstance(pid, str) and _valid_pid(pid, settings):
        return pid
  return None


def _kitty_cwd(socket: Path, settings: Settings) -> str:
  directory = settings["terminal_directory"]
  target = f"{directory['kitty_target_prefix']}{socket}"
  command = [part.format(target=target) for part in directory["kitty_command"]]
  output = _bounded_command(command, settings, directory["kitty_timeout"])
  if output is None:
    return ""
  try:
    windows = json.loads(output.decode(directory["encoding"], errors="strict"))
  except (UnicodeError, json.JSONDecodeError):
    return ""
  if not isinstance(windows, list):
    return ""
  directories: list[str] = []
  for window in windows:
    if not isinstance(window, dict):
      continue
    tabs = window.get(directory["tabs_key"])
    if not isinstance(tabs, list):
      continue
    for tab in tabs:
      if not isinstance(tab, dict):
        continue
      entries = tab.get(directory["windows_key"])
      if not isinstance(entries, list):
        continue
      for entry in entries:
        if isinstance(entry, dict):
          cwd = entry.get(directory["cwd_key"])
          if isinstance(cwd, str) and cwd:
            directories.append(cwd)
  return "\n".join(directories)


def _read_bounded(path: Path, maximum_bytes: int) -> bytes | None:
  try:
    with path.open("rb") as stream:
      data = stream.read(maximum_bytes + 1)
  except OSError:
    return None
  return data if len(data) <= maximum_bytes else None


def _process_cwd(pid: str, settings: Settings) -> str:
  directory = settings["terminal_directory"]
  proc_root = Path(directory["proc_root"])
  task_root = proc_root / pid / directory["task_directory"]
  try:
    tasks = list(islice(task_root.iterdir(), directory["maximum_task_files"] + 1))
  except OSError:
    return ""
  if len(tasks) > directory["maximum_task_files"]:
    return ""

  children: set[int] = set()
  for task in tasks:
    data = _read_bounded(task / directory["children_filename"], directory["maximum_children_file_bytes"])
    if data is None:
      continue
    text = data.decode(directory["encoding"], errors="surrogateescape")
    for child in text.split():
      if _valid_pid(child, settings):
        children.add(int(child))
        if len(children) > directory["maximum_child_processes"]:
          return ""
  if not children:
    return ""

  child_proc = proc_root / str(max(children))
  try:
    cwd = (child_proc / directory["cwd_filename"]).resolve(strict=True)
    executable = (child_proc / directory["executable_filename"]).resolve(strict=True)
  except (OSError, RuntimeError):
    return ""
  shells_data = _read_bounded(Path(directory["shells_file"]), directory["maximum_shells_file_bytes"])
  if shells_data is None:
    return ""
  shells = shells_data.decode(directory["encoding"], errors="surrogateescape").splitlines()
  return str(cwd) if str(executable) in shells else ""


def _working_directory(settings: Settings, requested_pid: str | None = None) -> str:
  directory = settings["terminal_directory"]
  pid = requested_pid if requested_pid is not None else _active_pid(settings)
  if pid is None or not _valid_pid(pid, settings):
    return os.environ.get(directory["home_environment"], "")

  runtime_directory = os.environ.get(directory["runtime_directory_environment"], "")
  socket = Path(runtime_directory) / f"{directory['kitty_socket_prefix']}{pid}"
  if socket.is_socket():
    cwd = _kitty_cwd(socket, settings)
  else:
    cwd = _process_cwd(pid, settings)
  return cwd if cwd and Path(cwd).is_dir() else os.environ.get(directory["home_environment"], "")


def _launch(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  launcher = settings["launchers"].get(Path(sys.argv[0]).name)
  if launcher is None:
    print(settings["unknown_launcher_message"], file=sys.stderr)
    return settings["statuses"]["configuration_error"]

  command = launcher["command"]
  directory_settings = settings["terminal_directory"]
  if launcher["terminal_directory"]:
    pid: str | None = None
    remaining = list(arguments)
    pid_prefix = directory_settings["pid_option_prefix"]
    if remaining and remaining[0].startswith(pid_prefix):
      pid = remaining.pop(0)[len(pid_prefix):]
    cwd = _working_directory(settings, pid)
    command = [*command, f"{directory_settings['directory_option_prefix']}{cwd}", *remaining]
  elif launcher["working_directory"]:
    command = [*command, _working_directory(settings)]
  else:
    command = [*command, *arguments]

  try:
    os.execvpe(command[0], command, os.environ)
  except OSError:
    print(settings["command_error_message"], file=sys.stderr)
    return settings["statuses"]["command_error"]


def _load_settings() -> Settings | None:
  try:
    return _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return None


def _tui_arguments(arguments: list[str], settings: Settings, *, focus: bool) -> tuple[str, list[str]] | None:
  tui = settings["tui"]
  remaining = list(arguments)
  app_id: str | None = None
  option_prefix = tui["app_id_option_prefix"]
  if remaining and remaining[0].startswith(option_prefix):
    app_id = remaining.pop(0)[len(option_prefix):]

  if not remaining:
    usage = settings["tui_focus_usage_message"] if focus else settings["tui_usage_message"]
    print(usage, file=sys.stderr)
    return None
  if app_id is None:
    app_id = tui["default_app_id_prefix"] + Path(remaining[0]).name
  if not app_id or "\x00" in app_id:
    print(settings["invalid_app_id_message"], file=sys.stderr)
    return None
  return app_id, remaining


def _launch_tui(command: list[str], app_id: str, settings: Settings) -> int:
  tui = settings["tui"]
  argv = [
    *tui["command"],
    f"{tui['app_id_option_prefix']}{app_id}",
    tui["execute_option"],
    *command,
  ]
  try:
    os.execvpe(argv[0], argv, os.environ)
  except OSError:
    print(settings["command_error_message"], file=sys.stderr)
    return settings["statuses"]["command_error"]


def launch_tui_main(arguments: list[str]) -> int:
  settings = _load_settings()
  if settings is None:
    return os.EX_CONFIG
  parsed = _tui_arguments(arguments, settings, focus=False)
  if parsed is None:
    return settings["statuses"]["invalid_arguments"]
  app_id, command = parsed
  return _launch_tui(command, app_id, settings)


def _tui_window_address(app_id: str, settings: Settings) -> str | None:
  tui = settings["tui"]
  directory = settings["terminal_directory"]
  try:
    output = run_bounded(
      tui["clients_command"],
      timeout_seconds=tui["command_timeout"],
      cleanup_timeout_seconds=directory["cleanup_timeout"],
      max_output_bytes=tui["maximum_clients_output"],
      read_chunk_bytes=directory["read_chunk_bytes"],
    )
  except OSError:
    return None
  if output is None:
    return None
  try:
    clients = json.loads(output.decode(directory["encoding"], errors="strict"))
  except (UnicodeError, json.JSONDecodeError):
    return None
  if not isinstance(clients, list) or len(clients) > tui["maximum_client_count"]:
    return None

  flags = re.IGNORECASE if tui["case_insensitive"] else 0
  expression = re.compile(tui["match_prefix"] + re.escape(app_id) + tui["match_suffix"], flags)
  for client in clients:
    if not isinstance(client, dict):
      continue
    if not any(
      isinstance(client.get(field), str) and expression.search(client[field])
      for field in tui["match_fields"]
    ):
      continue
    address = client.get(tui["address_field"])
    if (
      isinstance(address, str)
      and len(address) <= tui["maximum_address_length"]
      and re.fullmatch(tui["address_pattern"], address)
    ):
      return address
  return None


def _focus_tui(app_id: str, settings: Settings) -> bool:
  tui = settings["tui"]
  address = _tui_window_address(app_id, settings)
  if address is None:
    return False
  for configured_command in tui["focus_commands"]:
    command = [part.replace(tui["address_placeholder"], address) for part in configured_command]
    try:
      result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=tui["command_timeout"],
      )
    except (OSError, subprocess.SubprocessError):
      continue
    if result.returncode == 0:
      return True
  return False


def focus_tui_main(arguments: list[str]) -> int:
  settings = _load_settings()
  if settings is None:
    return os.EX_CONFIG
  parsed = _tui_arguments(arguments, settings, focus=True)
  if parsed is None:
    return settings["statuses"]["invalid_arguments"]
  app_id, command = parsed
  if _focus_tui(app_id, settings):
    return settings["statuses"]["success"]
  return _launch_tui(command, app_id, settings)


def main() -> int:
  return _launch([])


def terminal_main(arguments: list[str]) -> int:
  return _launch(arguments)
