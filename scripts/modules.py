#!/usr/bin/env python3

"""Validate the first-party module catalog and its source ownership."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"


@dataclass(frozen=True)
class Module:
    id: str
    domain: str
    package: str
    sources: tuple[str, ...]
    requires: tuple[str, ...]
    manifest: Path


def load_modules() -> dict[str, Module]:
    modules: dict[str, Module] = {}
    source_owners: dict[tuple[str, str], str] = {}
    errors: list[str] = []

    for manifest in sorted(MODULES.glob("**/module.toml")):
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
        if not all(isinstance(value, str) and value for value in (module_id, domain, package)):
            errors.append(f"{manifest.relative_to(ROOT)}: id, domain, and package must be non-empty strings")
            continue
        if module_id in modules:
            errors.append(f"{manifest.relative_to(ROOT)}: duplicate module id {module_id}")
            continue
        if not isinstance(sources, list) or not sources or not all(isinstance(value, str) and value for value in sources):
            errors.append(f"{manifest.relative_to(ROOT)}: sources must be a non-empty list of paths")
            continue
        if not isinstance(requires, list) or not all(isinstance(value, str) and value for value in requires):
            errors.append(f"{manifest.relative_to(ROOT)}: requires must be a list of module ids")
            continue

        for source in sources:
            path = Path(source)
            resolved = (ROOT / path).resolve()
            if path.is_absolute() or ".." in path.parts or not resolved.is_relative_to(ROOT) or not (ROOT / path).exists():
                errors.append(f"{manifest.relative_to(ROOT)}: source does not resolve inside the repository: {source}")
                continue
            owner_key = (package, path.as_posix())
            previous = source_owners.get(owner_key)
            if previous:
                errors.append(f"{manifest.relative_to(ROOT)}: {source} is already owned by {previous} in package {package}")
            source_owners[owner_key] = module_id

        modules[module_id] = Module(
            id=module_id,
            domain=domain,
            package=package,
            sources=tuple(sources),
            requires=tuple(requires),
            manifest=manifest,
        )

    for module in modules.values():
        for dependency in module.requires:
            if dependency not in modules:
                errors.append(f"{module.manifest.relative_to(ROOT)}: unknown dependency {dependency}")

    if not errors:
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
                visit(dependency, (*trail, module_id))
            state[module_id] = 2
            order.append(module_id)

        for module_id in sorted(modules):
            visit(module_id)

    if errors:
        raise ValueError("\n".join(errors))
    return modules


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "graph"))
    parser.add_argument("--package", help="validate modules that belong to this package")
    args = parser.parse_args()

    try:
        modules = load_modules()
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    if args.command == "graph":
        print(json.dumps([
            {"id": module.id, "domain": module.domain, "package": module.package,
             "sources": module.sources, "requires": module.requires}
            for module in modules.values()
        ], indent=2))
        return 0

    selected = [module for module in modules.values() if not args.package or module.package == args.package]
    if args.package and not selected:
        print(f"no modules are assigned to package {args.package}", file=sys.stderr)
        return 1
    print(f"Validated {len(selected)} module(s){f' for {args.package}' if args.package else ''}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
