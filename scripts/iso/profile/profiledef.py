"""Render the ArchISO shell profile from repository-owned YAML data."""

from __future__ import annotations

import os
import re
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import yaml


def mapping(value: object, message: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(message)
    return cast(dict[str, object], value)


def string(value: object, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    return value


def strings(value: object, message: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(message)
    return cast(list[str], value)


def render(architecture: str) -> str:
    root = Path(os.environ["AP"])
    settings_path = root / "data/iso/profile.yml"
    raw_settings = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
    if not isinstance(raw_settings, dict):
        raise TypeError()
    settings = cast(dict[str, object], raw_settings)
    message_settings = cast(dict[str, object], settings["messages"])

    def message(key: str) -> str:
        return cast(str, message_settings[key])

    name_settings = mapping(settings["name"], message("mapping_required"))
    name = os.environ.get(
        string(name_settings["environment"], message("string_required")),
        string(name_settings["default"], message("string_required")),
    )
    if (
        re.fullmatch(string(name_settings["pattern"], message("string_required")), name)
        is None
    ):
        raise ValueError(message("invalid_iso_name"))

    date_settings = mapping(settings["date"], message("mapping_required"))
    epoch_environment = string(
        date_settings["source_date_epoch_environment"], message("string_required")
    )
    epoch = os.environ.get(epoch_environment)
    if epoch is None or re.fullmatch(
        string(date_settings["source_date_epoch_pattern"], message("string_required")),
        epoch,
    ) is None:
        raise ValueError(message("source_date_epoch_required"))
    timestamp = datetime.fromtimestamp(int(epoch), UTC)
    label = string(date_settings["label_format"], message("string_required")).format(
        date=timestamp
    )
    version = string(date_settings["version_format"], message("string_required")).format(
        date=timestamp
    )
    boot_modes = mapping(settings["boot_modes"], message("mapping_required"))
    root_filesystem = mapping(settings["root_filesystem"], message("mapping_required"))
    kernel_parameters = mapping(settings["kernel_parameters"], message("mapping_required"))
    permissions = mapping(settings["file_permissions"], message("mapping_required"))

    values = {
        "iso_name": name,
        "iso_label": label,
        "iso_publisher": string(settings["publisher"], message("string_required")),
        "iso_application": string(settings["application"], message("string_required")),
        "iso_version": version,
        "install_dir": string(settings["install_directory"], message("string_required")),
        "pacman_conf": string(settings["pacman_configuration"], message("string_required")),
        "airootfs_image_type": string(
            root_filesystem["image_type"], message("string_required")
        ),
    }
    if architecture in kernel_parameters:
        values[f"kernel_params_{architecture}"] = string(
            kernel_parameters[architecture], message("string_required")
        )
    lines = [f"{key}={shlex.quote(value)}" for key, value in values.items()]
    arrays = {
        "bootmodes": strings(boot_modes[architecture], message("string_list_required")),
        "airootfs_image_tool_options": strings(
            root_filesystem["image_tool_options"], message("string_list_required")
        ),
        "bootstrap_tarball_compression": strings(
            settings["bootstrap_tarball_compression"], message("string_list_required")
        ),
    }
    for key, items in arrays.items():
        lines.append(f"{key}=({' '.join(shlex.quote(item) for item in items)})")
    lines.append("file_permissions=(")
    for path, mode in permissions.items():
        lines.append(
            f"  [{shlex.quote(string(path, message('string_required')))}]={shlex.quote(string(mode, message('string_required')))}"
        )
    lines.append(")")
    return "\n".join(lines) + "\n"


def main(arguments: list[str]) -> int:
    output = Path(arguments[0])
    architecture = arguments[1]
    contents = render(architecture)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(contents)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
