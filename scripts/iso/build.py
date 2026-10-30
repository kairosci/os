"""Build one native ArchISO image and publish its verified release parts."""

from __future__ import annotations

import argparse
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
from functools import cache
from pathlib import Path
from urllib.parse import quote

from .config import IsoSettings, load_config, require_ci_build
from .parts import read_manifest, split_iso


@cache
def _settings() -> IsoSettings:
    return load_config()


def platform_architecture() -> str:
    builder = _settings()["builder"]
    try:
        result = subprocess.run(
            builder["platform_command"],
            check=False,
            capture_output=True,
            text=True,
            timeout=int(builder["platform_timeout_seconds"]),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(builder["messages"]["platform_detection_failed"]) from error
    platform_name = result.stdout.strip()
    architecture = builder["platform_architectures"].get(platform_name)
    if result.returncode != 0 or architecture is None:
        raise RuntimeError(builder["messages"]["platform_detection_failed"])
    return architecture


def native_architecture() -> str:
    builder = _settings()["builder"]
    architecture = os.environ.get(builder["architecture_environment"])
    if architecture is not None:
        if architecture not in builder["iso_names"]:
            raise RuntimeError(
                builder["messages"]["invalid_architecture_environment"]
            )
        return architecture
    return platform_architecture()


def missing_build_commands(available: set[str] | None = None) -> list[str]:
    required = list(_settings()["builder"]["required_commands"])
    required.extend(
        _settings()["builder"]["architecture_commands"].get(native_architecture(), [])
    )
    present = (
        available
        if available is not None
        else {
            name
            for name in required
            if shutil.which(name) is not None
        }
    )
    return [name for name in required if name not in present]


def iso_name_for_architecture(architecture: str) -> str:
    try:
        name = _settings()["builder"]["iso_names"][architecture]
    except KeyError as error:
        raise ValueError(
            _settings()["builder"]["messages"]["unsupported_architecture"].format(
                architecture=architecture
            )
        ) from error
    if not re.fullmatch(_settings()["release"]["iso_name_pattern"], f"{name}.iso"):
        raise ValueError(
            _settings()["builder"]["messages"]["invalid_iso_name"].format(
                architecture=architecture, name=name
            )
        )
    return name


def check_build_environment() -> None:
    missing = missing_build_commands()
    if missing:
        raise RuntimeError(
            _settings()["builder"]["messages"]["missing_build_commands"].format(
                commands=", ".join(missing)
            )
        )
    yaml_check = subprocess.run(
        _settings()["builder"]["yaml_check_command"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if yaml_check.returncode != 0:
        raise RuntimeError(_settings()["builder"]["messages"]["yaml_required"])


def inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def safe_profile_output(root: Path, relative: str) -> Path:
    destination = root / relative
    if root.is_symlink() or destination.is_absolute() or not inside(destination, root):
        raise ValueError(_settings()["builder"]["messages"]["unsafe_key_path"])
    current = root
    for component in Path(relative).parts:
        if component in {"", ".", ".."}:
            raise ValueError(_settings()["builder"]["messages"]["unsafe_key_path"])
        current = current / component
        if current.is_symlink():
            raise ValueError(_settings()["builder"]["messages"]["unsafe_key_path"])
    return destination


def configure_architecture_repository(
    architecture: str, profile_root: Path, config: str
) -> str:
    builder = _settings()["builder"]
    repository_settings = builder["architecture_repositories"].get(architecture)
    if repository_settings is None:
        return config
    include_directive = repository_settings["include_directive"]
    include_count = repository_settings["include_directive_count"]
    if config.count(include_directive) != include_count:
        raise ValueError(builder["messages"]["architecture_repository_config_invalid"])
    live_root = profile_root / builder["layout"]["profile_live_root"]
    key_path = safe_profile_output(live_root, repository_settings["live_key_path"])
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(repository_settings["public_key"], encoding="utf-8")
    drop_in = safe_profile_output(live_root, repository_settings["live_key_drop_in"])
    drop_in.parent.mkdir(parents=True, exist_ok=True)
    rendered_commands = []
    for command in repository_settings["service_commands"]:
        arguments = [
            argument.format(
                fingerprint=repository_settings["fingerprint"],
                key_path="/" + repository_settings["live_key_path"],
            )
            for argument in command
        ]
        if any(not argument or any(character.isspace() for character in argument) for argument in arguments):
            raise ValueError(builder["messages"]["architecture_repository_config_invalid"])
        rendered_commands.append(" ".join(arguments))
    drop_in.write_text(
        "\n".join(
            [
                repository_settings["service_section"],
                *(
                    f"{repository_settings['service_command_directive']}={command}"
                    for command in rendered_commands
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config.replace(include_directive, repository_settings["server_directive"])


def prepare_architecture_repository(architecture: str) -> None:
    builder = _settings()["builder"]
    settings = builder["architecture_repositories"].get(architecture)
    if settings is None:
        return
    with tempfile.TemporaryDirectory(
        prefix=settings["keyring_temporary_prefix"]
    ) as temporary_home:
        key_file = Path(temporary_home) / "repository-key.asc"
        key_file.write_text(settings["public_key"], encoding="utf-8")
        environment = {**os.environ, settings["keyring_environment"]: temporary_home}
        fingerprint_result = subprocess.run(
            [*settings["verification_command"], str(key_file)],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        fingerprint_field = settings["fingerprint_field_index"]
        fingerprints = [
            fields[fingerprint_field].upper()
            for line in fingerprint_result.stdout.splitlines()
            if (fields := line.split(":"))
            and len(fields) > fingerprint_field
            and fields[0] == settings["fingerprint_record_prefix"]
        ]
        configured = settings["fingerprint"].upper()
        if fingerprints.count(configured) != settings["fingerprint_count"]:
            raise ValueError(builder["messages"]["architecture_repository_key_invalid"])
        subprocess.run(settings["keyring_commands"]["initialize"], check=True)
        subprocess.run(
            [*settings["keyring_commands"]["add"], str(key_file)], check=True
        )
        subprocess.run(
            [*settings["keyring_commands"]["sign"], configured], check=True
        )


def validate_profile(profile: Path, repository: Path) -> Path:
    try:
        resolved = profile.resolve(strict=True)
    except FileNotFoundError as error:
        raise ValueError(
            _settings()["builder"]["messages"]["profile_missing"].format(path=profile)
        ) from error
    if not inside(resolved, repository):
        raise ValueError(
            _settings()["builder"]["messages"]["profile_outside_repository"]
        )
    if not resolved.is_dir():
        raise ValueError(
            _settings()["builder"]["messages"]["profile_not_directory"].format(
                path=resolved
            )
        )

    required = (
        _settings()["builder"]["profile_definition_file"],
        _settings()["builder"]["pacman_config_file"],
    )
    for name in required:
        path = resolved / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(
                _settings()["builder"]["messages"]["profile_required_file"].format(
                    name=name
                )
            )

    architecture = native_architecture()
    if profile_package_file(resolved, architecture) is None:
        raise ValueError(
            _settings()["builder"]["messages"]["profile_package_list_missing"].format(
                architecture=architecture
            )
        )
    return resolved


def profile_package_file(profile: Path, architecture: str) -> Path | None:
    candidates = (
        profile
        / _settings()["builder"]["architecture_package_list_format"].format(
            architecture=architecture
        ),
        profile / _settings()["builder"]["generic_package_list_file"],
    )
    return next(
        (path for path in candidates if path.is_file() and not path.is_symlink()),
        None,
    )


def build_local_repository(repository: Path, destination: Path) -> Path:
    builder = _settings()["builder"]
    makepkg = shutil.which(builder["makepkg_command"])
    repo_add = shutil.which(builder["repo_add_command"])
    if makepkg is None or repo_add is None:
        raise RuntimeError(builder["messages"]["makepkg_required"])

    root_build = os.geteuid() == 0
    makepkg_runner: list[str] = []
    build_account: pwd.struct_passwd | None = None
    if root_build:
        container = builder["container"]
        build_user = os.environ.get(container["build_user_environment"])
        if build_user is None or not build_user:
            raise RuntimeError(builder["messages"]["unprivileged_makepkg"])
        build_account = pwd.getpwnam(build_user)
        if build_account.pw_uid == 0:
            raise RuntimeError(builder["messages"]["unprivileged_makepkg"])
        makepkg_runner = [
            argument.format(user=build_user) for argument in builder["makepkg_run_as"]
        ]

    required_tools = builder["package_build_commands"]
    missing = [name for name in required_tools if shutil.which(name) is None]
    if missing:
        raise RuntimeError(
            builder["messages"]["missing_package_build_tools"].format(
                commands=", ".join(missing)
            )
        )
    destination.mkdir(parents=True, exist_ok=True)
    build_root = destination / _settings()["builder"]["layout"]["package_build"]
    source_root = destination / _settings()["builder"]["layout"]["package_sources"]
    logs_root = destination / _settings()["builder"]["layout"]["package_logs"]
    repository_root = (
        destination / _settings()["builder"]["layout"]["package_repository"]
    )
    for path in (build_root, source_root, logs_root, repository_root):
        path.mkdir(parents=True, exist_ok=True)
    if build_account is not None:
        subprocess.run(
            [
                *builder["container"]["commands"]["change_owner"],
                f"{build_account.pw_uid}:{build_account.pw_gid}",
                str(destination.parent),
            ],
            check=True,
        )

    for package in _settings()["builder"]["local_packages"]:
        package_directory = (
            repository / _settings()["builder"]["layout"]["package_directory"] / package
        )
        if not (
            package_directory / _settings()["builder"]["layout"]["package_build_file"]
        ).is_file():
            raise ValueError(
                _settings()["builder"]["messages"]["package_build_file_missing"].format(
                    path=package_directory
                )
            )
        package_build = build_root / package
        if build_account is None:
            package_build.mkdir(parents=True, exist_ok=True)
        environment = {
            **os.environ,
            _settings()["builder"]["makepkg_environment_keys"]["source"]: str(
                repository
            ),
            _settings()["builder"]["makepkg_environment_keys"]["build"]: str(
                package_build
            ),
            _settings()["builder"]["makepkg_environment_keys"]["logs"]: str(logs_root),
            _settings()["builder"]["makepkg_environment_keys"]["packages"]: str(
                repository_root
            ),
            _settings()["builder"]["makepkg_environment_keys"]["sources"]: str(
                source_root
            ),
            _settings()["builder"]["makepkg_environment_keys"]["source_packages"]: str(
                destination
                / _settings()["builder"]["layout"]["package_source_archives"]
            ),
        }
        if build_account is not None:
            environment.update(
                {
                    "HOME": build_account.pw_dir,
                    "USER": build_account.pw_name,
                    "LOGNAME": build_account.pw_name,
                }
            )
        archive_glob = _settings()["builder"]["package_artifacts"]["archive_glob"]
        signature_suffixes = _settings()["builder"]["package_artifacts"][
            "signature_suffixes"
        ]
        previous_artifacts = set(repository_root.glob(archive_glob))
        subprocess.run(
            [
                *makepkg_runner,
                makepkg,
                *builder["makepkg_arguments"],
            ],
            cwd=package_directory,
            env=environment,
            check=True,
        )
        artifacts = [
            path
            for path in repository_root.glob(archive_glob)
            if path not in previous_artifacts
            and path.is_file()
            and path.suffix not in signature_suffixes
        ]
        if len(artifacts) != 1:
            raise ValueError(
                _settings()["builder"]["messages"]["package_artifact_count"].format(
                    package=package, count=len(artifacts)
                )
            )

    packages = sorted(
        path
        for path in repository_root.glob(
            _settings()["builder"]["package_artifacts"]["archive_glob"]
        )
        if path.is_file()
        and path.suffix
        not in _settings()["builder"]["package_artifacts"]["signature_suffixes"]
    )
    if len(packages) != len(_settings()["builder"]["local_packages"]):
        raise ValueError(_settings()["builder"]["messages"]["repository_package_count"])
    subprocess.run(
        [
            repo_add,
            *_settings()["builder"]["repo_add_arguments"],
            str(
                repository_root
                / _settings()["builder"]["layout"]["local_repository_database"]
            ),
            *(str(path) for path in packages),
        ],
        check=True,
    )
    return repository_root


def prepare_profile(
    profile: Path, destination: Path, local_repository: Path, architecture: str
) -> Path:
    shutil.copytree(profile, destination, symlinks=True)
    source_package_list = profile_package_file(profile, architecture)
    if source_package_list is None:
        raise ValueError(
            _settings()["builder"]["messages"]["staged_package_list_missing"].format(
                architecture=architecture
            )
        )
    package_list = destination / source_package_list.name
    package_lines = package_list.read_text(encoding="utf-8").splitlines()
    missing_packages = sorted(
        set(_settings()["builder"]["local_packages"]) - set(package_lines)
    )
    if missing_packages:
        raise ValueError(
            _settings()["builder"]["messages"]["local_packages_missing"].format(
                packages=", ".join(missing_packages)
            )
        )

    profile_definition = destination / _settings()["builder"]["generated_profile_definition_file"]
    subprocess.run(
        [
            sys.executable,
            str(destination / _settings()["builder"]["profile_definition_file"]),
            str(profile_definition),
            architecture,
        ],
        check=True,
        env=os.environ,
    )

    pacman_conf = destination / _settings()["builder"]["pacman_config_file"]
    if not pacman_conf.is_file() or pacman_conf.is_symlink():
        raise ValueError(
            _settings()["builder"]["messages"]["profile_required_file"].format(
                name=_settings()["builder"]["pacman_config_file"]
            )
        )
    config = pacman_conf.read_text(encoding="utf-8")
    config = configure_architecture_repository(architecture, destination, config)
    repository_name = _settings()["builder"]["package_repository"]["name"]
    repository_header = _settings()["builder"]["package_repository"][
        "section_header_format"
    ].format(name=repository_name)
    if config.count(repository_header) != 1:
        raise ValueError(
            _settings()["builder"]["messages"]["package_repository_config_invalid"]
        )

    repository = local_repository.resolve(strict=True)
    archive_glob = _settings()["builder"]["package_artifacts"]["archive_glob"]
    if not repository.is_dir() or not any(repository.glob(archive_glob)):
        raise ValueError(_settings()["builder"]["messages"]["local_repository_empty"])
    if not any(
        (repository / name).is_file()
        for name in _settings()["builder"]["package_repository"]["database_files"]
    ):
        raise ValueError(
            _settings()["builder"]["messages"]["local_repository_database_missing"]
        )
    for entry in repository.iterdir():
        if entry.is_symlink():
            try:
                entry.resolve(strict=True).relative_to(repository)
            except (OSError, ValueError) as error:
                raise ValueError(
                    _settings()["builder"]["messages"][
                        "repository_symlink_unsafe"
                    ].format(name=entry.name)
                ) from error

    repository_url = _settings()["builder"]["repository_url_prefix"] + quote(
        str(local_repository.resolve()), safe="/"
    )
    live_repository_url = _settings()["builder"]["package_repository"][
        "live_server_url"
    ]
    server_line = _settings()["builder"]["package_repository"][
        "server_line_format"
    ].format(url=live_repository_url)
    if config.count(server_line) != 1:
        raise ValueError(
            _settings()["builder"]["messages"]["package_repository_config_invalid"]
        )
    pacman_conf.write_text(
        config.replace(
            server_line,
            _settings()["builder"]["package_repository"]["server_line_format"].format(
                url=repository_url
            ),
        ),
        encoding="utf-8",
    )

    live_repository = (
        destination
        / _settings()["builder"]["layout"]["profile_live_root"]
        / _settings()["builder"]["layout"]["live_repository_directory"]
    )
    live_repository.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(repository, live_repository, symlinks=True)
    live_pacman_conf = (
        destination
        / _settings()["builder"]["layout"]["profile_live_root"]
        / _settings()["builder"]["layout"]["live_pacman_config"]
    )
    live_pacman_conf.parent.mkdir(parents=True, exist_ok=True)
    live_config = (profile / _settings()["builder"]["pacman_config_file"]).read_text(
        encoding="utf-8"
    )
    live_config = configure_architecture_repository(architecture, destination, live_config)
    live_pacman_conf.write_text(live_config, encoding="utf-8")
    return destination


def publish_assets(
    staged_iso: Path, output_dir: Path, parts_dir: Path
) -> tuple[Path, Path]:
    if (
        not re.fullmatch(_settings()["release"]["iso_name_pattern"], staged_iso.name)
        or ".." in staged_iso.name
    ):
        raise ValueError(
            _settings()["builder"]["messages"]["unsafe_image_name"].format(
                name=staged_iso.name
            )
        )
    if not staged_iso.is_file() or staged_iso.stat().st_size == 0:
        raise ValueError(_settings()["builder"]["messages"]["invalid_image"])

    output_dir.mkdir(parents=True, exist_ok=True)
    if output_dir.is_symlink():
        raise ValueError(_settings()["builder"]["messages"]["output_symlink"])
    image = output_dir / staged_iso.name
    if image.exists() or image.is_symlink():
        raise FileExistsError(
            _settings()["builder"]["messages"]["existing_image"].format(path=image)
        )

    parts_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=_settings()["builder"]["temporary_prefixes"]["release_parts"],
        dir=parts_dir,
    ) as temporary:
        staged_parts = Path(temporary)
        staged_manifest = split_iso(staged_iso, staged_parts)
        manifest = read_manifest(staged_manifest)
        manifest_path = parts_dir / staged_manifest.name
        part_paths = [parts_dir / record["name"] for record in manifest["parts"]]
        conflicts = [
            path
            for path in [*part_paths, manifest_path]
            if path.exists() or path.is_symlink()
        ]
        if conflicts:
            raise FileExistsError(
                _settings()["builder"]["messages"]["existing_release_assets"].format(
                    names=", ".join(path.name for path in conflicts)
                )
            )

        published: list[Path] = []
        try:
            os.link(staged_iso, image)
            published.append(image)
            staged_iso.unlink()
            for record, destination in zip(manifest["parts"], part_paths, strict=True):
                staged_part = staged_parts / record["name"]
                os.link(staged_part, destination)
                published.append(destination)
                staged_part.unlink()
            os.link(staged_manifest, manifest_path)
            published.append(manifest_path)
            staged_manifest.unlink()
        except BaseException:
            for path in reversed(published):
                path.unlink(missing_ok=True)
            raise
    return image, manifest_path


def build_iso(
    profile: Path, work_root: Path, output_dir: Path, parts_dir: Path
) -> tuple[Path, Path]:
    repository = Path(os.environ["AP"])
    require_ci_build(_settings()["builder"]["ci"])
    selected_profile = validate_profile(profile, repository)
    check_build_environment()
    mkarchiso = shutil.which(_settings()["builder"]["mkarchiso_command"])
    if mkarchiso is None:
        raise RuntimeError(_settings()["builder"]["messages"]["mkarchiso_required"])

    output_dir.mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=True, exist_ok=True)
    if output_dir.is_symlink() or work_root.is_symlink() or parts_dir.is_symlink():
        raise ValueError(_settings()["builder"]["messages"]["output_paths_symlink"])
    if any(
        inside(path.resolve(), selected_profile)
        for path in (output_dir, work_root, parts_dir)
    ):
        raise ValueError(_settings()["builder"]["messages"]["output_inside_profile"])

    architecture = native_architecture()
    with tempfile.TemporaryDirectory(
        prefix=_settings()["builder"]["temporary_prefixes"]["build_inputs"],
        dir=work_root,
    ) as inputs_directory:
        inputs = Path(inputs_directory)
        local_repository = build_local_repository(
            repository, inputs / _settings()["builder"]["layout"]["local_repository"]
        )
        build_profile = prepare_profile(
            selected_profile,
            inputs / _settings()["builder"]["layout"]["profile_staging_directory"],
            local_repository,
            architecture,
        )
        prepare_architecture_repository(architecture)
        with (
            tempfile.TemporaryDirectory(
                prefix=_settings()["builder"]["temporary_prefixes"]["build_output"],
                dir=output_dir,
            ) as staged_output,
            tempfile.TemporaryDirectory(
                prefix=_settings()["builder"]["temporary_prefixes"]["build_work"],
                dir=work_root,
            ) as staged_work,
        ):
            subprocess.run(
                [
                    mkarchiso,
                    *(
                        item.format(
                            work=staged_work,
                            output=staged_output,
                            profile=build_profile,
                        )
                        for item in _settings()["builder"]["mkarchiso_arguments"]
                    ),
                ],
                env={
                    **os.environ,
                    _settings()["builder"][
                        "iso_name_environment_key"
                    ]: iso_name_for_architecture(architecture),
                },
                check=True,
            )
            images = sorted(
                Path(staged_output).glob(
                    _settings()["builder"]["package_artifacts"]["iso_glob"]
                )
            )
            if len(images) != 1:
                raise ValueError(
                    _settings()["builder"]["messages"]["image_count"].format(
                        count=len(images)
                    )
                )
            return publish_assets(images[0], output_dir, parts_dir)


def main(argv: list[str] | None = None) -> int:
    repository = Path(os.environ["AP"])
    parser = argparse.ArgumentParser(
        description=_settings()["builder"]["cli"]["parser_description"]
    )
    parser.add_argument(
        _settings()["builder"]["cli"]["profile_option"],
        dest=_settings()["builder"]["cli"]["profile_destination"],
        type=Path,
        default=repository / _settings()["builder"]["profile"],
        help=_settings()["builder"]["messages"]["profile_option_help"],
    )
    parser.add_argument(
        _settings()["builder"]["cli"]["work_directory_option"],
        dest=_settings()["builder"]["cli"]["work_directory_destination"],
        type=Path,
        default=repository / _settings()["builder"]["work_directory"],
        help=_settings()["builder"]["messages"]["work_directory_option_help"],
    )
    parser.add_argument(
        _settings()["builder"]["cli"]["output_directory_option"],
        dest=_settings()["builder"]["cli"]["output_directory_destination"],
        type=Path,
        default=repository / _settings()["builder"]["output_directory"],
        help=_settings()["builder"]["messages"]["output_directory_option_help"],
    )
    parser.add_argument(
        _settings()["builder"]["cli"]["parts_directory_option"],
        dest=_settings()["builder"]["cli"]["parts_directory_destination"],
        type=Path,
        default=repository / _settings()["builder"]["parts_directory"],
        help=_settings()["builder"]["messages"]["parts_directory_option_help"],
    )
    arguments = parser.parse_args(argv)
    try:
        image, manifest = build_iso(
            getattr(arguments, _settings()["builder"]["cli"]["profile_destination"]),
            getattr(
                arguments, _settings()["builder"]["cli"]["work_directory_destination"]
            ),
            getattr(
                arguments, _settings()["builder"]["cli"]["output_directory_destination"]
            ),
            getattr(
                arguments, _settings()["builder"]["cli"]["parts_directory_destination"]
            ),
        )
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as error:
        print(
            "{}{}".format(_settings()["builder"]["messages"]["error_prefix"], error),
            file=sys.stderr,
        )
        return 1
    print(image)
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
