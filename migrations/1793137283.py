from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


def load_config(root: Path) -> dict:
  config_path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError()
  return config


def package_version(config: dict) -> tuple[str, str] | None:
  result = subprocess.run(
    config["commands"]["sync_package"],
    check=False,
    capture_output=True,
    text=True,
  )
  if result.returncode != int(config["statuses"]["success"]):
    return None

  package_name = config["packages"]["name"]
  expected_repository = config["repositories"]["official"]
  for line in result.stdout.splitlines():
    fields = line.split(maxsplit=3)
    if len(fields) == 4 and fields[0] == expected_repository and fields[1] == package_name:
      return fields[2], fields[3]
  return None


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  subprocess.run([*config["commands"]["i18n"], config["messages"]["reason"]], check=False)

  present = subprocess.run(
    [*config["commands"]["present"], config["packages"]["name"]],
    check=False,
  )
  if present.returncode != int(config["statuses"]["present"]):
    return int(config["statuses"]["success"])

  query = subprocess.run(
    [*config["commands"]["query_installed"], config["packages"]["name"]],
    check=False,
    capture_output=True,
    text=True,
  )
  if query.returncode != int(config["statuses"]["success"]):
    return query.returncode
  installed_fields = query.stdout.split()
  if len(installed_fields) < int(config["limits"]["installed_fields"]):
    return int(config["statuses"]["failed"])

  sync_package = package_version(config)
  if sync_package is None:
    return int(config["statuses"]["failed"])
  repository_version, archive = sync_package

  comparison = subprocess.run(
    [*config["commands"]["compare_versions"], installed_fields[1], repository_version],
    check=False,
    capture_output=True,
    text=True,
  )
  if comparison.returncode != int(config["statuses"]["success"]):
    return comparison.returncode
  try:
    local_is_newer = int(comparison.stdout.strip()) > int(config["limits"]["same_version"])
  except ValueError:
    return int(config["statuses"]["failed"])
  if not local_is_newer:
    return int(config["statuses"]["success"])

  install = subprocess.run(
    [*config["commands"]["install_official_archive"], archive],
    check=False,
  )
  return install.returncode


if __name__ == "__main__":
  raise SystemExit(main())
