"""Load ISO build and release settings from the repository data file."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class ReleaseSettings(TypedDict):
    github_asset_limit_bytes: int
    max_part_bytes: int
    read_size_bytes: int
    manifest_max_bytes: int
    maximum_part_count: int
    manifest_format: int
    manifest_suffix: str
    part_name_format: str
    sha256_pattern: str
    checksum_algorithm: str
    iso_name_pattern: str
    repository_pattern: str
    tag_pattern: str
    default_repository: str
    download_directory_prefix: str
    upload_directory_prefix: str
    split_temporary_prefix: str
    github_command: str
    release_metadata_command: list[str]
    release_metadata_timeout_seconds: int
    download_timeout_seconds: int
    upload_timeout_seconds: int
    maximum_release_asset_count: int
    asset_list_field: str
    asset_name_field: str
    asset_size_field: str
    download_command: list[str]
    upload_command: list[str]
    upload_repository_option: str
    download_pattern_arguments: list[str]
    messages: dict[str, str]
    parts: dict[str, str]
    download: dict[str, str]
    upload: dict[str, str]


class PackageArtifacts(TypedDict):
    archive_glob: str
    iso_glob: str
    signature_suffixes: list[str]


class PackageRepository(TypedDict):
    name: str
    database_files: list[str]
    section_header_format: str
    server_line_format: str
    live_server_url: str


class CiBuildSettings(TypedDict):
    required_environment: dict[str, str]
    run_id_environment: str
    run_attempt_environment: str
    run_identifier_pattern: str
    required_message: str


class RootBuildSettings(TypedDict):
    build_user_environment: str
    commands: dict[str, list[str]]


class BuilderSettings(TypedDict):
    cli: dict[str, str]
    container: RootBuildSettings
    local_packages: list[str]
    required_commands: list[str]
    architecture_commands: dict[str, list[str]]
    platform_command: list[str]
    platform_timeout_seconds: int
    architecture_environment: str
    platform_architectures: dict[str, str]
    iso_names: dict[str, str]
    package_build_commands: list[str]
    makepkg_run_as: list[str]
    makepkg_command: str
    repo_add_command: str
    mkarchiso_command: str
    yaml_check_command: list[str]
    makepkg_arguments: list[str]
    repo_add_arguments: list[str]
    mkarchiso_arguments: list[str]
    profile_definition_file: str
    generated_profile_definition_file: str
    pacman_config_file: str
    architecture_package_list_format: str
    generic_package_list_file: str
    messages: dict[str, str]
    profile: str
    work_directory: str
    output_directory: str
    parts_directory: str
    layout: dict[str, str]
    package_artifacts: PackageArtifacts
    package_repository: PackageRepository
    makepkg_environment_keys: dict[str, str]
    repository_url_prefix: str
    temporary_prefixes: dict[str, str]
    iso_name_environment_key: str
    ci: CiBuildSettings


class IsoSettings(TypedDict):
    release: ReleaseSettings
    builder: BuilderSettings
    settings_cli: dict[str, str]


def require_ci_build(settings: CiBuildSettings) -> None:
    required_environment = settings["required_environment"]
    missing = [
        name
        for name, expected in required_environment.items()
        if os.environ.get(name) != expected
    ]
    run_id_name = settings["run_id_environment"]
    run_attempt_name = settings["run_attempt_environment"]
    identifier_pattern = settings["run_identifier_pattern"]
    if (
        missing
        or re.fullmatch(identifier_pattern, os.environ.get(run_id_name, "")) is None
        or re.fullmatch(identifier_pattern, os.environ.get(run_attempt_name, "")) is None
    ):
        raise RuntimeError(settings["required_message"])


def load_config() -> IsoSettings:
    path = Path(os.environ["AP"]) / "data/iso/release.yml"
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("release"), dict)
        or not isinstance(value.get("builder"), dict)
        or not isinstance(value.get("settings_cli"), dict)
    ):
        raise TypeError(f"invalid ISO release settings: {path}")
    return cast(IsoSettings, value)


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        settings = load_config()["settings_cli"]
    except (OSError, TypeError, yaml.YAMLError) as error:
        print(f"invalid ISO release settings: {error}", file=sys.stderr)
        return 2
    if len(arguments) != 1:
        print(settings["usage"], file=sys.stderr)
        return 2
    section, separator, key = arguments[0].partition(".")
    if not separator:
        print(settings["key_format_error"], file=sys.stderr)
        return 2
    try:
        config = cast(dict[str, object], load_config())
        section_value = config[section]
        if not isinstance(section_value, dict):
            raise KeyError(section)
        value = cast(dict[str, object], section_value)[key]
    except (KeyError, TypeError):
        print(settings["unknown_setting"].format(key=arguments[0]), file=sys.stderr)
        return 2
    if not isinstance(value, str):
        print(settings["non_string_setting"].format(key=arguments[0]), file=sys.stderr)
        return 2
    print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
