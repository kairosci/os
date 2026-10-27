from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile

import yaml


def load_config(root: Path) -> dict:
  config_path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError()
  return config


def localized(config: dict, key: str) -> str:
  result = subprocess.run(
    [*config["commands"]["i18n"], key],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def prepend_line(path: Path, line: str) -> None:
  temporary_path = None
  try:
    with tempfile.NamedTemporaryFile(
      mode="w",
      encoding="utf-8",
      dir=path.parent,
      delete=False,
    ) as temporary:
      temporary_path = Path(temporary.name)
      temporary.write(line)
      temporary.write("\n")
      temporary.write(path.read_text(encoding="utf-8"))
      temporary.flush()
      os.fsync(temporary.fileno())
    temporary_path.replace(path)
  finally:
    if temporary_path is not None:
      temporary_path.unlink(missing_ok=True)


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  print(localized(config, config["messages"]["reason"]))

  home = Path.home()
  nvim_config = home / config["paths"]["nvim_config_dir"]
  if nvim_config.is_dir():
    provider = home / config["paths"]["nvim_provider"]
    provider.parent.mkdir(parents=True, exist_ok=True)
    installed = subprocess.run(
      [
        *config["commands"]["install"],
        *config["arguments"]["install_mode"],
        str(root / config["paths"]["provider_source"]),
        str(provider),
      ],
      check=False,
    )
    if installed.returncode != int(config["statuses"]["success"]):
      return installed.returncode

    options = home / config["paths"]["nvim_options"]
    if options.is_file():
      config_module = config["values"]["module_separator"].join(config["values"]["module_parts"])
      setup_line = "".join(config["values"]["setup_line_parts"]).replace(
        config["values"]["module_placeholder"], config_module
      )
      options_text = options.read_text(encoding="utf-8")
      if config_module not in options_text:
        prepend_line(options, setup_line)

  tmux_config = home / config["paths"]["tmux_config"]
  if tmux_config.is_file():
    content = tmux_config.read_text(encoding="utf-8")
    if re.search(config["patterns"]["clipboard_feature"], content) is None:
      with tmux_config.open("a", encoding="utf-8") as stream:
        stream.write(config["values"]["line_break"])
        stream.write(localized(config, config["messages"]["tmux_comment"]))
        stream.write(config["values"]["line_break"])
        stream.write(config["values"]["tmux_setting"])
        stream.write(config["values"]["line_break"])

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
