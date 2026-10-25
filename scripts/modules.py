#!/usr/bin/env python3

"""Validate and assemble the first-party module catalog."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"
PACKAGES = ROOT / "packages"


@dataclass(frozen=True)
class Module:
    id: str
    domain: str
    package: str
    sources: tuple[str, ...]
    requires: tuple[str, ...]
    outputs: tuple[tuple[str, str], ...]
    manifest: Path


def load_modules() -> tuple[dict[str, Module], list[str], list[str]]:
    modules: dict[str, Module] = {}
    source_owners: dict[tuple[str, str], str] = {}
    output_owners: dict[str, tuple[str, str]] = {}
    package_names: dict[str, str | None] = {}
    checked_symlinks: set[Path] = set()
    errors: list[str] = []

    for manifest in sorted(MODULES.glob("**/module.toml")):
        if manifest.is_symlink():
            errors.append(f"{manifest.relative_to(ROOT)}: module manifests cannot be symlinks")
            continue
        try:
            data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            errors.append(f"{manifest.relative_to(ROOT)}: {error}")
            continue

        module_id = data.get("id")
        domain = data.get("domain")
        package = data.get("package")
        sources = data.get("sources")
        requires = data.get("requires", [])
        raw_outputs = data.get("output", [])
        if not all(isinstance(value, str) and value for value in (module_id, domain, package)):
            errors.append(f"{manifest.relative_to(ROOT)}: id, domain, and package must be non-empty strings")
            continue
        module_path = manifest.parent.relative_to(MODULES).parts
        expected_id = ".".join(module_path)
        expected_domain = module_path[0] if module_path else ""
        if domain != expected_domain:
            errors.append(f"{manifest.relative_to(ROOT)}: domain must match its module directory: {expected_domain}")
        if module_id != expected_id:
            errors.append(f"{manifest.relative_to(ROOT)}: module id must match its directory: {expected_id}")
        pkgbuild = PACKAGES / package / "PKGBUILD"
        if package not in package_names:
            pkgname = None
            if not pkgbuild.is_file():
                errors.append(f"{manifest.relative_to(ROOT)}: package has no PKGBUILD: {package}")
            else:
                for line in pkgbuild.read_text(encoding="utf-8").splitlines():
                    if not line.startswith("pkgname="):
                        continue
                    match = re.fullmatch(r"pkgname=(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z0-9@._+-]+))", line)
                    if match:
                        pkgname = next(value for value in match.groups() if value is not None)
                    break
                if pkgname != package:
                    errors.append(f"{manifest.relative_to(ROOT)}: package directory does not match pkgname: {package}")
            package_names[package] = pkgname
        if module_id in modules:
            errors.append(f"{manifest.relative_to(ROOT)}: duplicate module id {module_id}")
            continue
        if not isinstance(sources, list) or not sources or not all(isinstance(value, str) and value for value in sources):
            errors.append(f"{manifest.relative_to(ROOT)}: sources must be a non-empty list of paths")
            continue
        if not isinstance(requires, list) or not all(isinstance(value, str) and value for value in requires):
            errors.append(f"{manifest.relative_to(ROOT)}: requires must be a list of module ids")
            continue
        if not isinstance(raw_outputs, list) or not all(isinstance(value, dict) for value in raw_outputs):
            errors.append(f"{manifest.relative_to(ROOT)}: output must be an array of source/target tables")
            continue
        if not raw_outputs:
            errors.append(f"{manifest.relative_to(ROOT)}: module must declare at least one output")

        normalized_outputs: list[tuple[str, str]] = []
        for output in raw_outputs:
            source = output.get("source")
            target = output.get("target")
            if not all(isinstance(value, str) and value for value in (source, target)):
                errors.append(f"{manifest.relative_to(ROOT)}: every output needs non-empty source and target paths")
                continue
            source_path = Path(source)
            target_path = Path(target)
            resolved = (ROOT / source_path).resolve()
            if source_path.is_absolute() or ".." in source_path.parts or not resolved.is_relative_to(ROOT) or not (ROOT / source_path).exists():
                errors.append(f"{manifest.relative_to(ROOT)}: output source does not resolve inside the repository: {source}")
                continue
            if not any(source_path == Path(root) or Path(root) in source_path.parents for root in sources):
                errors.append(f"{manifest.relative_to(ROOT)}: output source is not declared in sources: {source}")
                continue
            if target_path.is_absolute() or ".." in target_path.parts or not target_path.parts:
                errors.append(f"{manifest.relative_to(ROOT)}: output target must be relative and stay inside the package: {target}")
                continue
            normalized_outputs.append((source_path.as_posix(), target_path.as_posix()))

        for source in sources:
            path = Path(source)
            resolved = (ROOT / path).resolve()
            if path.is_absolute() or ".." in path.parts or not resolved.is_relative_to(ROOT) or not (ROOT / path).exists():
                errors.append(f"{manifest.relative_to(ROOT)}: source does not resolve inside the repository: {source}")
                continue
            source_path = ROOT / path
            tree = (source_path, *source_path.rglob("*")) if source_path.is_dir() and not source_path.is_symlink() else (source_path,)
            for entry in tree:
                if not entry.is_symlink() or entry in checked_symlinks:
                    continue
                checked_symlinks.add(entry)
                try:
                    symlink_target = entry.resolve(strict=True)
                except (OSError, RuntimeError):
                    errors.append(f"{manifest.relative_to(ROOT)}: source contains a broken or cyclic symlink: {entry.relative_to(ROOT)}")
                    continue
                if not symlink_target.is_relative_to(ROOT):
                    errors.append(f"{manifest.relative_to(ROOT)}: source symlink leaves the repository: {entry.relative_to(ROOT)}")
            owner_key = (package, path.as_posix())
            previous = source_owners.get(owner_key)
            if previous:
                errors.append(f"{manifest.relative_to(ROOT)}: {source} is already owned by {previous} in package {package}")
            source_owners[owner_key] = module_id

        module = Module(
            id=module_id,
            domain=domain,
            package=package,
            sources=tuple(sources),
            requires=tuple(requires),
            outputs=tuple(normalized_outputs),
            manifest=manifest,
        )
        modules[module_id] = module

        for source, target in normalized_outputs:
            source_path = ROOT / source
            target_path = Path(target)
            if source_path.is_file() or source_path.is_symlink():
                output_paths = [target_path]
            else:
                output_paths = [
                    target_path / path.relative_to(source_path)
                    for path in source_path.rglob("*")
                    if path.is_file() or path.is_symlink()
                ]
            for output_path in output_paths:
                owner_key = output_path.as_posix()
                previous = output_owners.get(owner_key)
                if previous:
                    errors.append(
                        f"{manifest.relative_to(ROOT)}: package output {output_path} is already owned "
                        f"by {previous[1]} in package {previous[0]}"
                    )
                for parent in Path(owner_key).parents:
                    parent_owner = output_owners.get(parent.as_posix())
                    if parent_owner:
                        errors.append(
                            f"{manifest.relative_to(ROOT)}: package output {output_path} is nested under file "
                            f"{parent} owned by {parent_owner[1]} in package {parent_owner[0]}"
                        )
                if any(existing.startswith(f"{owner_key}/") for existing in output_owners):
                    errors.append(f"{manifest.relative_to(ROOT)}: package output {output_path} conflicts with a declared output directory")
                output_owners[owner_key] = (package, module_id)

    order = topological_order(modules, errors)
    return modules, order, errors


def topological_order(modules: dict[str, Module], errors: list[str]) -> list[str]:
    for module in modules.values():
        for dependency in module.requires:
            if dependency not in modules:
                errors.append(f"{module.manifest.relative_to(ROOT)}: unknown dependency {dependency}")

    state: dict[str, int] = {}
    order: list[str] = []

    def visit(module_id: str, trail: tuple[str, ...] = ()) -> None:
        if state.get(module_id) == 2:
            return
        if state.get(module_id) == 1:
            cycle = " -> ".join((*trail, module_id))
            errors.append(f"dependency cycle: {cycle}")
            return
        state[module_id] = 1
        for dependency in modules[module_id].requires:
            if dependency in modules:
                visit(dependency, (*trail, module_id))
        state[module_id] = 2
        order.append(module_id)

    for module_id in sorted(modules):
        visit(module_id)
    return order


def assemble(
    modules: dict[str, Module],
    order: list[str],
    package: str,
    destination: Path,
    patterns: tuple[str, ...],
) -> int:
    selected_ids = {
        module_id
        for module_id in order
        if modules[module_id].package == package
        and (not patterns or any(fnmatch.fnmatchcase(module_id, pattern) for pattern in patterns))
    }
    unknown = [
        pattern for pattern in patterns
        if not any(fnmatch.fnmatchcase(module_id, pattern) for module_id in modules)
    ]
    if unknown:
        print(f"module pattern matched no modules: {', '.join(unknown)}", file=sys.stderr)
        return 1

    for module_id in tuple(selected_ids):
        pending = list(modules[module_id].requires)
        while pending:
            dependency = pending.pop()
            if dependency not in modules or modules[dependency].package != package or dependency in selected_ids:
                continue
            selected_ids.add(dependency)
            pending.extend(modules[dependency].requires)

    selected = [modules[module_id] for module_id in order if module_id in selected_ids]
    if not selected:
        print(f"no modules are assigned to package {package}", file=sys.stderr)
        return 1

    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        print(f"package destination must be empty: {destination}", file=sys.stderr)
        return 1

    for module in selected:
        for source, target in module.outputs:
            source_path = ROOT / source
            target_path = destination / target
            for parent in target_path.parents:
                if parent == destination.parent:
                    break
                if parent.is_symlink():
                    print(f"package output traverses a symlink: {parent}", file=sys.stderr)
                    return 1
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path.is_dir():
                shutil.copytree(source_path, target_path, dirs_exist_ok=True, symlinks=True)
            else:
                shutil.copy2(source_path, target_path, follow_symlinks=False)
    print(f"Assembled {len(selected)} module(s) for {package} into {destination}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "graph", "assemble"))
    parser.add_argument("--package", help="select modules assigned to this package")
    parser.add_argument("--module", action="append", default=[], help="module ID or glob pattern to assemble; repeatable")
    parser.add_argument("--destination", help="package root for module assembly")
    args = parser.parse_args()

    modules, order, errors = load_modules()
    if errors:
        print("Module catalog validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    if args.command == "graph":
        print(json.dumps([
            {"id": module.id, "domain": module.domain, "package": module.package,
             "sources": module.sources, "requires": module.requires,
             "outputs": module.outputs}
            for module in (modules[module_id] for module_id in order)
        ], indent=2))
        return 0

    if args.command == "assemble":
        if not args.package or not args.destination:
            parser.error("assemble requires --package and --destination")
        if not modules:
            return 1
        return assemble(modules, order, args.package, Path(args.destination).resolve(), tuple(args.module))

    if args.package:
        selected = [module for module in modules.values() if module.package == args.package]
        if not selected:
            print(f"no modules are assigned to package {args.package}", file=sys.stderr)
            return 1
    else:
        selected = list(modules.values())
    print(f"Validated {len(selected)} module(s){f' for {args.package}' if args.package else ''}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
