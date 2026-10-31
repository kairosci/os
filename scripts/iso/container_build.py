"""Build the ArchISO profile inside the repository's pinned Arch container."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast

import yaml

sys.path.insert(0, str(Path(os.environ["AP"])))
from scripts.iso.build import native_architecture, platform_architecture
from scripts.iso.config import CiBuildSettings, require_ci_build


class ArchitectureSource(TypedDict):
    revision: str


class ArchitectureSetup(TypedDict):
    source: ArchitectureSource
    source_path: str
    commands: list[list[str]]
    verify_command: list[str]
    patches: list[str]


class SeccompSettings(TypedDict):
    default_profile: str
    temporary_prefix: str
    temporary_filename: str
    allow_syscalls: list[str]
    allow_action: str
    allow_comment: str


class ContainerSettings(TypedDict):
    engine_command: list[str]
    images: dict[str, str]
    architecture_packages: dict[str, list[str]]
    architecture_setup: dict[str, ArchitectureSetup]
    mount_path: str
    build_user: str
    build_path: str
    build_user_environment: str
    root_home: str
    build_script: str
    bootstrap_commands: dict[str, str]
    bootstrap_argument_zero: str
    build_script_environment: str
    build_operation_environment: str
    mount_path_environment: str
    run_arguments: list[str]
    apparmor_profile_name: str
    apparmor_profile: str
    apparmor_profile_command: list[str]
    apparmor_profile_arguments: list[str]
    environment_arguments: list[str]
    ci_environment_arguments: list[str]
    ci_environment_passthrough: list[str]
    additional_mounts: list[dict[str, str]]
    additional_mount_arguments: list[str]
    entrypoint: list[str]
    packages: list[str]
    operation: str
    host_uid_environment: str
    host_gid_environment: str
    directory_environment: list[str]
    seccomp: SeccompSettings
    root_build_uid: int
    root_build_gid: int
    commands: dict[str, list[str]]
    build_command: list[str]
    mounts: dict[str, str]
    build_script_description: str
    messages: dict[str, str]


class BuilderSettings(TypedDict):
    container: ContainerSettings
    ci: CiBuildSettings
    architecture_environment: str
    makepkg_run_as: list[str]
    profile: str
    work_directory: str
    output_directory: str
    parts_directory: str


class Settings(TypedDict):
    builder: BuilderSettings


def repository() -> Path:
    return Path(os.environ["AP"])


def load_settings() -> Settings:
    path = repository() / "data/iso/release.yml"
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("builder"), dict):
        builder_value = value.get("builder") if isinstance(value, dict) else None
        container_value = (
            builder_value.get("container") if isinstance(builder_value, dict) else None
        )
        messages = (
            container_value.get("messages")
            if isinstance(container_value, dict)
            else None
        )
        messages = messages if isinstance(messages, dict) else {}
        message = messages["invalid_settings"]
        raise TypeError(message.format(path=path))
    return cast(Settings, value)


def repository_path(
    value: str, mount_path: str, description: str, messages: dict[str, str]
) -> str:
    path = Path(value)
    root = repository()
    candidate = Path(os.path.abspath(path if path.is_absolute() else root / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(
            messages["path_inside_repository"].format(description=description)
        ) from error
    if not relative.parts:
        raise ValueError(
            messages["path_is_repository_root"].format(description=description)
        )
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(
                messages["path_traverses_symlink"].format(
                    description=description, path=current
                )
            )
    return str(Path(mount_path) / relative)


def repository_file(relative: str, message: str) -> Path:
    path = Path(relative)
    root = repository().resolve(strict=True)
    if path.is_absolute() or not path.parts or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise ValueError(message)
    candidate = root
    for part in path.parts:
        candidate /= part
        if candidate.is_symlink():
            raise ValueError(message)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise ValueError(message) from error
    if not resolved.is_file():
        raise ValueError(message)
    return resolved


def container_command(settings: Settings, seccomp_profile: Path) -> list[str]:
    builder = settings["builder"]
    container = builder["container"]
    engine_command = container["engine_command"]
    messages = container["messages"]
    architecture = platform_architecture()
    if architecture not in container["images"]:
        raise RuntimeError(
            messages["unsupported_architecture"].format(architecture=architecture)
        )
    missing_engine_commands = [
        name for name in engine_command if shutil.which(name) is None
    ]
    if missing_engine_commands:
        raise RuntimeError(
            messages["engine_required"].format(
                engine=" ".join(missing_engine_commands)
            )
        )

    mount_path = container["mount_path"]
    inner_environment = {
        name: repository_path(
            os.environ.get(name, cast(dict[str, str], builder)[destination]),
            mount_path,
            name,
            messages,
        )
        for name, destination in container["mounts"].items()
    }
    additional_mount_arguments: list[str] = []
    for mount in container["additional_mounts"]:
        container_source = Path(
            repository_path(
                cast(dict[str, str], builder)[mount["setting"]],
                mount_path,
                mount["environment"],
                messages,
            )
        )
        source = repository() / container_source.relative_to(mount_path)
        source.mkdir(parents=True, exist_ok=True)
        inner_environment[mount["environment"]] = mount["destination"]
        additional_mount_arguments.extend(
            argument.format(source=source, destination=mount["destination"])
            for argument in container["additional_mount_arguments"]
        )
    format_values = {
        "repository": str(repository()),
        "mount_path": mount_path,
        "seccomp_profile": str(seccomp_profile),
        "host_uid": os.getuid(),
        "host_gid": os.getgid(),
        "build_user": container["build_user"],
        "build_script_environment": container["build_script_environment"],
        "build_script": repository_path(
            container["build_script"],
            mount_path,
            container["build_script_description"],
            messages,
        ),
        "build_operation_environment": container["build_operation_environment"],
        "operation": container["operation"],
    }
    command = [
        *engine_command,
        *(argument.format(**format_values) for argument in container["run_arguments"]),
        *additional_mount_arguments,
    ]
    command.extend(
        argument.format(profile=container["apparmor_profile_name"])
        for argument in container["apparmor_profile_arguments"]
    )
    for name in container["ci_environment_passthrough"]:
        value = os.environ.get(name)
        if value is None:
            continue
        command.extend(
            argument.format(name=name, value=value)
            for argument in container["ci_environment_arguments"]
        )
    for name, value in inner_environment.items():
        command.extend(
            argument.format(name=name, value=value)
            for argument in container["environment_arguments"]
        )
    command.extend(
        argument.format(name=builder["architecture_environment"], value=architecture)
        for argument in container["environment_arguments"]
    )
    command.extend(
        (
            container["images"][architecture],
            *container["entrypoint"],
            container["bootstrap_commands"][architecture].format(
                mount_path=container["mount_path"]
            ),
            container["bootstrap_argument_zero"],
            *container["packages"],
            *container["architecture_packages"].get(architecture, []),
        )
    )
    return command


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def run_in_container(settings: Settings) -> int:
    container = settings["builder"]["container"]
    architecture = native_architecture()
    architecture_setup = container["architecture_setup"].get(architecture)
    if architecture_setup is None and architecture not in container["images"]:
        raise RuntimeError(
            container["messages"]["unsupported_architecture"].format(
                architecture=architecture
            )
        )
    if architecture_setup is not None:
        source = architecture_setup["source"]
        setup = architecture_setup["commands"]
        for command in setup:
            subprocess.run(command, check=True)
        revision = subprocess.run(
            architecture_setup["verify_command"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if revision != source["revision"]:
            raise RuntimeError(
                container["messages"]["source_revision_mismatch"].format(
                    expected=source["revision"], actual=revision
                )
            )
        for patch_name in architecture_setup["patches"]:
            patch_path = repository_file(
                patch_name, container["messages"]["architecture_patch_invalid"]
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    architecture_setup["source_path"],
                    "apply",
                    "--check",
                    str(patch_path),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    architecture_setup["source_path"],
                    "apply",
                    str(patch_path),
                ],
                check=True,
            )
    commands = container["commands"]
    uid_name = container["host_uid_environment"]
    gid_name = container["host_gid_environment"]
    host_uid = int(os.environ[uid_name])
    host_gid = int(os.environ[gid_name])
    build_uid = host_uid if host_uid != 0 else int(container["root_build_uid"])
    build_gid = host_gid if host_uid != 0 else int(container["root_build_gid"])

    group = run([*commands["lookup_group"], str(build_gid)])
    if group.returncode != 0:
        subprocess.run(
            [
                *commands["create_group"],
                str(build_gid),
                container["build_user"],
            ],
            check=True,
        )

    user = run([*commands["lookup_user"], str(build_uid)])
    if user.returncode != 0:
        subprocess.run(
            [
                argument.format(
                    uid=build_uid,
                    gid=build_gid,
                    name=container["build_user"],
                )
                for argument in commands["create_user"]
            ],
            check=True,
        )
        user = run([*commands["lookup_user"], str(build_uid)])
        if user.returncode != 0:
            raise RuntimeError(container["messages"]["build_user_missing"])
    fields = user.stdout.strip().split(":")
    if (
        len(fields) < 6
        or not fields[2].isdigit()
        or not fields[3].isdigit()
        or int(fields[2]) != build_uid
        or int(fields[3]) != build_gid
    ):
        raise RuntimeError(container["messages"]["build_user_invalid"])
    build_user = fields[0]

    directories = [os.environ[name] for name in container["directory_environment"]]
    prepared_directories: list[str] = []
    try:
        for directory in directories:
            subprocess.run([*commands["make_directory"], directory], check=True)
            subprocess.run(
                [*commands["change_owner"], f"{build_uid}:{build_gid}", directory],
                check=True,
            )
            prepared_directories.append(directory)

        values = {
            "user": build_user,
            "root_home": container["root_home"],
            "path": container["build_path"],
            "mount_path": os.environ[container["mount_path_environment"]],
            "build_user_environment": container["build_user_environment"],
            **{name: os.environ[name] for name in container["mounts"]},
            **{name: os.environ[name] for name in container["directory_environment"]},
        }
        command = [argument.format(**values) for argument in container["build_command"]]
        result = subprocess.run(command, check=False)
        return result.returncode
    finally:
        for directory in prepared_directories:
            subprocess.run(
                [*commands["change_owner"], f"{host_uid}:{host_gid}", directory],
                check=True,
            )


def main() -> int:
    try:
        settings = load_settings()
        require_ci_build(settings["builder"]["ci"])
        container = settings["builder"]["container"]
        if sys.argv[1:] == [container["operation"]]:
            return run_in_container(settings)
        if sys.argv[1:]:
            raise ValueError(container["messages"]["unknown_operation"])
        subprocess.run(
            container["apparmor_profile_command"],
            input=container["apparmor_profile"],
            check=True,
            text=True,
        )
        seccomp = container["seccomp"]
        with tempfile.TemporaryDirectory(
            prefix=seccomp["temporary_prefix"]
        ) as temporary_directory:
            profile = Path(temporary_directory) / seccomp["temporary_filename"]
            source = Path(seccomp["default_profile"])
            if source.is_symlink() or not source.is_file():
                raise RuntimeError(container["messages"]["seccomp_profile_missing"])
            profile_data = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(profile_data, dict) or not isinstance(
                profile_data.get("syscalls"), list
            ):
                raise RuntimeError(container["messages"]["seccomp_profile_invalid"])
            syscall_names = seccomp["allow_syscalls"]
            existing_rules = [
                rule
                for rule in profile_data["syscalls"]
                if isinstance(rule, dict)
                and set(rule.get("names", [])) & set(syscall_names)
            ]
            if any(
                rule.get("action") != seccomp["allow_action"]
                or rule.get("args")
                or rule.get("includes")
                or rule.get("excludes")
                for rule in existing_rules
            ):
                raise RuntimeError(container["messages"]["seccomp_syscall_configured"])
            if not existing_rules:
                profile_data["syscalls"].append(
                    {
                        "names": syscall_names,
                        "action": seccomp["allow_action"],
                        "args": [],
                        "comment": seccomp["allow_comment"],
                        "includes": {},
                        "excludes": {},
                    }
                )
            profile.write_text(
                json.dumps(profile_data, separators=(",", ":")), encoding="utf-8"
            )
            command = container_command(settings, profile)
            result = subprocess.run(command, check=False)
        return result.returncode
    except (
        KeyError,
        OSError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
        yaml.YAMLError,
    ) as error:
        try:
            settings = load_settings()
            message = settings["builder"]["container"]["messages"]["build_failure"]
        except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
            print(error, file=sys.stderr)
            return 1
        print(message.format(error=error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
