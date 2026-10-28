from collections.abc import Callable


class _FileMonitor:
  def cancel(self) -> None: ...
  def connect(self, signal: str, callback: Callable[..., object]) -> int: ...


class _File:
  @staticmethod
  def new_for_path(path: str) -> _File: ...
  def monitor_file(self, flags: object, cancellable: object | None) -> _FileMonitor: ...


class _Subprocess:
  @staticmethod
  def new(argv: list[str], flags: object) -> _Subprocess: ...
  def wait_check(self, cancellable: object | None = None) -> bool: ...


class Gio:
  class DBusCallFlags:
    NONE: int
    NO_AUTO_START: int

  class FileMonitorFlags:
    WATCH_MOVES: int

  class SubprocessFlags:
    NONE: int
    STDOUT_SILENCE: int
    STDERR_SILENCE: int

  class BusNameWatcherFlags:
    NONE: int

  class BusType:
    SESSION: int

  File = _File
  Subprocess = _Subprocess
  @staticmethod
  def bus_watch_name_on_connection(connection: object, name: str, flags: object, appeared: Callable[..., object], vanished: Callable[..., object]) -> int: ...
  @staticmethod
  def bus_get_sync(bus_type: object, cancellable: object | None) -> object: ...


class GLib:
  class Error(Exception): ...
  class Variant:
    def __init__(self, signature: str, value: tuple[object, ...]) -> None: ...
  class MainLoop:
    def run(self) -> None: ...
    def quit(self) -> None: ...
  SOURCE_REMOVE: int
  SOURCE_CONTINUE: int
  IO_IN: int
  IO_HUP: int
  @staticmethod
  def timeout_add(interval: int, callback: Callable[[], bool | int]) -> int: ...
  @staticmethod
  def source_remove(source_id: int) -> bool: ...
  @staticmethod
  def io_add_watch(stream: object, condition: int, callback: Callable[..., bool | int]) -> int: ...


class GObject:
  class GObject: ...


class Nautilus:
  class MenuProvider: ...
  class MenuItem:
    def __init__(self, *, name: str, label: str, icon: str) -> None: ...
    def connect(self, signal: str, callback: Callable[..., object], *args: object) -> int: ...
