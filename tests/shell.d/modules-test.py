"""Validate module declarations and assembled package trees."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


MODULES_TOOL = ROOT / "scripts/modules.py"
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def command(*arguments: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, *map(str, arguments)],
    cwd=ROOT,
    env=test_environment(),
    check=False,
    capture_output=True,
    text=True,
  )


def check(condition: bool, detail: object) -> None:
  if not condition:
    raise AssertionError(detail)


def compare_trees(source: Path, destination: Path, excluded: set[str] | None = None) -> None:
  excluded = excluded or set()

  def entries(root: Path) -> dict[str, tuple[str, object, int | None]]:
    result = {}
    for path in root.rglob("*"):
      relative = path.relative_to(root)
      if any(part in excluded for part in relative.parts):
        continue
      if "__pycache__" in relative.parts or path.suffix in IGNORED_SUFFIXES:
        continue
      if path.is_dir() and not path.is_symlink():
        continue
      if path.is_symlink():
        result[relative.as_posix()] = ("link", os.readlink(path), None)
      else:
        result[relative.as_posix()] = ("file", path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
    return result

  check(entries(source) == entries(destination), (source, destination))


def check_module_graph(graph_path: Path) -> None:
  modules = {module["id"]: module for module in json.loads(graph_path.read_text(encoding="utf-8"))}
  cli_directory = ROOT / "src/cli"
  stages = {
    "system.installation.boot",
    "system.installation.config",
    "system.installation.hardware",
    "system.installation.login",
    "system.installation.packages",
    "system.installation.post-install",
    "system.installation.provisioning",
    "system.installation.user",
  }
  settings = {
    "system.settings.defaults",
    "system.settings.preinstall-tools",
    "system.settings.system-files",
    "desktop.applications",
    "desktop.branding.preinstall",
  }
  runtime_data = {"system.runtime-data.libalpm-hooks"}
  default_modules = {key: value for key, value in modules.items() if key.startswith("system.settings.defaults.")}
  system_file_modules = {key: value for key, value in modules.items() if key.startswith("system.settings.system-files.")}
  command_modules = {key: value for key, value in modules.items() if key.startswith("desktop.commands.")}
  command_sources = {
    source for key, module in modules.items() if key.startswith("desktop.commands") for source in module["sources"]
  }
  cli_files = {f"src/cli/{path.name}" for path in cli_directory.iterdir() if path.is_file()}
  cli_files -= {"src/cli/arch-debug", "src/cli/arch-debug-idle", "src/cli/arch-upload-log"}
  expected_groups = {
    f"desktop.commands.{source.removeprefix('src/cli/arch-').split('-', 1)[0]}"
    for source in cli_files if source != "src/cli/archctl"
  }
  default_roots = ROOT / "default"
  etc_roots = ROOT / "etc"
  config_roots = ROOT / "config"
  expected_default_sources = {f"default/{path.name}" for path in default_roots.iterdir()}
  declared_default_sources = {
    source for key, module in modules.items()
    if key == "system.settings.defaults" or key in default_modules for source in module["sources"]
  }
  expected_etc_sources = {f"etc/{path.name}" for path in etc_roots.iterdir()}
  declared_etc_sources = {
    source for key, module in modules.items()
    if key == "system.settings.system-files" or key in system_file_modules for source in module["sources"]
  }
  config_modules = {key: value for key, value in modules.items() if key.startswith("system.settings.user-configs.")}
  expected_config_sources = {f"config/{path.name}" for path in config_roots.iterdir() if path.is_dir()}
  declared_config_sources = {source for module in config_modules.values() for source in module["sources"]}
  root_config_files = {f"config/{path.name}" for path in config_roots.iterdir() if path.is_file()}
  declared_root_config_files = set(modules["system.settings"]["sources"])

  check(stages <= modules.keys(), stages - modules.keys())
  check(settings <= modules.keys(), settings - modules.keys())
  check(runtime_data <= modules.keys(), runtime_data - modules.keys())
  check(set(command_modules) == expected_groups, set(command_modules) ^ expected_groups)
  check(command_sources == cli_files, (cli_files - command_sources, command_sources - cli_files))
  check(declared_default_sources == expected_default_sources, (expected_default_sources - declared_default_sources, declared_default_sources - expected_default_sources))
  check(declared_etc_sources == expected_etc_sources, (expected_etc_sources - declared_etc_sources, declared_etc_sources - expected_etc_sources))
  check(declared_config_sources == expected_config_sources, (expected_config_sources - declared_config_sources, declared_config_sources - expected_config_sources))
  check(declared_root_config_files == root_config_files, (root_config_files - declared_root_config_files, declared_root_config_files - root_config_files))

  for module_id, module in default_modules.items():
    check(module["package"] == "arch-settings", module_id)
    check(module["requires"] == ["system.settings.defaults"], (module_id, module["requires"]))
    check(len(module["sources"]) == 1 and len(module["sources"][0].split("/")) == 2, module_id)
    expected_id = f"system.settings.defaults.{Path(module['sources'][0]).name.replace('.', '-')}"
    check(module_id == expected_id, (module_id, expected_id))
  for module_id, module in system_file_modules.items():
    check(module["package"] == "arch-settings", module_id)
    check(module["requires"] == ["system.settings.system-files"], (module_id, module["requires"]))
    check(len(module["sources"]) == 1 and len(module["sources"][0].split("/")) == 2, module_id)
    slug = re.sub(r"[^a-z0-9]+", "-", Path(module["sources"][0]).name.lower()).strip("-")
    expected_id = f"system.settings.system-files.{slug}"
    check(module_id == expected_id, (module_id, module["sources"][0]))
  for module_id, module in config_modules.items():
    check(module["package"] == "arch-settings", module_id)
    check(module["requires"] == ["system.settings"], (module_id, module["requires"]))
    check(len(module["sources"]) == len(module["outputs"]) == 1, module_id)
    source = module["sources"][0]
    slug = Path(source).name.lower().replace("_", "-")
    check(module_id == f"system.settings.user-configs.{slug}", (module_id, source))
    check(module["outputs"][0] == [source, f"usr/share/arch/{source}"], (module_id, module["outputs"]))
  for module_id in stages:
    module = modules[module_id]
    check(module["package"] == "arch", module_id)
    check(module["requires"] == ["system.installation"], (module_id, module["requires"]))
  for module_id in settings:
    module = modules[module_id]
    check(module["package"] == "arch-settings", module_id)
    check(module["requires"] == ["system.settings"], (module_id, module["requires"]))
  check(modules["system.runtime-data"]["package"] == "arch", modules["system.runtime-data"])
  check(["data", "usr/share/arch/data"] in modules["system.runtime-data"]["outputs"], modules["system.runtime-data"]["outputs"])
  for module_id in runtime_data:
    module = modules[module_id]
    check(module["package"] == "arch", module_id)
    check(module["requires"] == ["system.runtime-data"], (module_id, module["requires"]))
  for module_id, module in command_modules.items():
    check(module["package"] == "arch", module_id)
    check(module["requires"] == ["desktop.commands"], (module_id, module["requires"]))
    check(len(module["sources"]) == len(module["outputs"]), module_id)
    for source, output in zip(module["sources"], module["outputs"]):
      check(output == [source, f"usr/share/arch/src/cli/{Path(source).name}"], (module_id, source, output))
  check(modules["desktop.commands"]["sources"] == ["src/cli/archctl"], modules["desktop.commands"])


def check_validator_rejections() -> None:
  with tempfile.TemporaryDirectory(prefix="modules-test-") as temporary:
    sandbox = Path(temporary)
    root = sandbox / "repo"
    (root / "modules/system/example").mkdir(parents=True)
    (root / "payload").mkdir()
    (root / "packages/example").mkdir(parents=True)
    (root / "packages/example/PKGBUILD").write_text("pkgname=example\n", encoding="utf-8")
    manifest = root / "modules/system/example/module.toml"
    manifest.write_text(
      'id = "system.example"\ndomain = "system"\npackage = "example"\n'
      'sources = ["payload"]\nrequires = []\n\n'
      '[[output]]\nsource = "payload"\ntarget = "usr/share/example/payload"\n',
      encoding="utf-8",
    )
    spec = importlib.util.spec_from_file_location("modules_tool", MODULES_TOOL)
    check(spec is not None and spec.loader is not None, "could not load module validator")
    modules_tool = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modules_tool
    spec.loader.exec_module(modules_tool)
    modules_tool.ROOT = root
    modules_tool.MODULES = root / "modules"
    modules_tool.PACKAGES = root / "packages"
    (root / "payload/first").write_text("first", encoding="utf-8")

    (root / "packages/example/PKGBUILD").write_text("pkgname=other\n", encoding="utf-8")
    _, _, errors = modules_tool.load_modules()
    check(any("package directory does not match pkgname" in error for error in errors), errors)
    (root / "packages/example/PKGBUILD").write_text("pkgname=example\n", encoding="utf-8")

    manifest.write_text(manifest.read_text(encoding="utf-8").replace('id = "system.example"', 'id = "system.wrong"'), encoding="utf-8")
    _, _, errors = modules_tool.load_modules()
    check(any("module id must match its directory" in error for error in errors), errors)
    manifest.write_text(manifest.read_text(encoding="utf-8").replace('id = "system.wrong"', 'id = "system.example"'), encoding="utf-8")

    (root / "packages/second").mkdir(parents=True)
    (root / "packages/second/PKGBUILD").write_text("pkgname=second\n", encoding="utf-8")
    (root / "payload/second").write_text("second", encoding="utf-8")
    (root / "modules/system/second").mkdir()
    (root / "modules/system/second/module.toml").write_text(
      'id = "system.second"\ndomain = "system"\npackage = "second"\n'
      'sources = ["payload/second"]\nrequires = []\n\n'
      '[[output]]\nsource = "payload/second"\ntarget = "usr/share/example/payload"\n',
      encoding="utf-8",
    )
    _, _, errors = modules_tool.load_modules()
    check(any("package output usr/share/example/payload conflicts with a declared output directory" in error for error in errors), errors)

    outside = sandbox / "outside"
    outside.write_text("outside", encoding="utf-8")
    (root / "payload/external").symlink_to(outside)
    _, _, errors = modules_tool.load_modules()
    check(any("source symlink leaves the repository" in error for error in errors), errors)

    (root / "payload/external").unlink()
    (root / "payload/dangling").symlink_to(root / "missing")
    _, _, errors = modules_tool.load_modules()
    check(any("broken or cyclic symlink" in error for error in errors), errors)


def verify_assembled_outputs(graph_path: Path, stage: Path) -> None:
  package_roots = {"arch": stage / "arch", "arch-settings": stage / "settings"}
  expected: dict[str, set[str]] = {name: set() for name in package_roots}
  for module in json.loads(graph_path.read_text(encoding="utf-8")):
    package = module["package"]
    for source, target in module["outputs"]:
      source_path = ROOT / source
      target_root = package_roots[package]
      if source_path.is_dir() and not source_path.is_symlink():
        sources = (entry for entry in source_path.rglob("*") if "__pycache__" not in entry.parts and entry.suffix not in IGNORED_SUFFIXES)
        for original in sources:
          if original.is_dir() and not original.is_symlink():
            continue
          relative = original.relative_to(source_path)
          destination = target_root / target / relative
          expected[package].add(destination.relative_to(target_root).as_posix())
          check(destination.is_symlink() if original.is_symlink() else destination.is_file(), destination)
          if original.is_symlink():
            check(destination.readlink() == original.readlink(), destination)
          else:
            check(destination.read_bytes() == original.read_bytes(), destination)
            check(stat.S_IMODE(destination.stat().st_mode) == stat.S_IMODE(original.stat().st_mode), destination)
      else:
        destination = target_root / target
        expected[package].add(destination.relative_to(target_root).as_posix())
        check(destination.is_symlink() if source_path.is_symlink() else destination.is_file(), destination)
        if source_path.is_symlink():
          check(destination.readlink() == source_path.readlink(), destination)
        else:
          check(destination.read_bytes() == source_path.read_bytes(), destination)
          check(stat.S_IMODE(destination.stat().st_mode) == stat.S_IMODE(source_path.stat().st_mode), destination)

  for package, package_root in package_roots.items():
    actual = {
      entry.relative_to(package_root).as_posix()
      for entry in package_root.rglob("*")
      if "__pycache__" not in entry.parts and entry.suffix not in IGNORED_SUFFIXES
      if entry.is_file() or entry.is_symlink()
    }
    check(actual == expected[package], (package, expected[package] - actual, actual - expected[package]))


def main() -> int:
  try:
    with tempfile.TemporaryDirectory(prefix="modules-test-") as temporary:
      stage = Path(temporary)
      validation = command(MODULES_TOOL, "validate")
      check(validation.returncode == 0, validation.stdout + validation.stderr)
      graph_result = command(MODULES_TOOL, "graph")
      check(graph_result.returncode == 0, graph_result.stdout + graph_result.stderr)
      graph_path = stage / "graph.json"
      graph_path.write_text(graph_result.stdout, encoding="utf-8")
      check_module_graph(graph_path)
      pass_check("module ownership and command grouping are explicit")

      check_validator_rejections()
      pass_check("module validation rejects invalid package names, ids, collisions, and escaping symlinks")

      arch = stage / "arch"
      result = command(MODULES_TOOL, "assemble", "--package", "arch", "--destination", arch)
      check(result.returncode == 0, result.stdout + result.stderr)
      for path in ("installer", "migrations"):
        compare_trees(ROOT / path, arch / "usr/share/arch" / path)
      source_cli = ROOT / "src/cli"
      assembled_cli = arch / "usr/share/arch/src/cli"
      excluded = {"arch-debug", "arch-debug-idle", "arch-upload-log"}
      expected_cli = {path.name for path in source_cli.iterdir() if path.is_file()} - excluded
      actual_cli = {path.name for path in assembled_cli.iterdir() if path.is_file() or path.is_symlink()}
      check(actual_cli == expected_cli, (expected_cli - actual_cli, actual_cli - expected_cli))
      for name in expected_cli:
        original, packaged = source_cli / name, assembled_cli / name
        check(original.read_bytes() == packaged.read_bytes(), name)
        check(stat.S_IMODE(original.stat().st_mode) == stat.S_IMODE(packaged.stat().st_mode), name)
      pass_check("the runtime package assembles installer, migration, and CLI sources unchanged")

      settings = stage / "settings"
      result = command(MODULES_TOOL, "assemble", "--package", "arch-settings", "--destination", settings)
      check(result.returncode == 0, result.stdout + result.stderr)
      for path in ("config", "default"):
        compare_trees(ROOT / path, settings / "usr/share/arch" / path)
      compare_trees(ROOT / "etc", settings / "etc", {"skel"})
      for path in (
        "etc/skel/.config/arch/branding/screensaver.txt",
        "etc/skel/.config/arch/branding/about.txt",
        "usr/share/icons/hicolor/256x256/apps/arch.png",
      ):
        check((settings / path).is_file(), f"settings package assembles {path}")
      verify_assembled_outputs(graph_path, stage)
      pass_check("settings outputs match source contents and permissions")
  except (AssertionError, OSError, subprocess.SubprocessError, ValueError) as error:
    fail_check(str(error))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
