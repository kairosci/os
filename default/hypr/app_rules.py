"""Read user-owned Hyprland app rules and emit a safe Lua data table."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import cast

import yaml


def default_config_path() -> Path:
    return Path(os.environ["AP"]) / "config/hypr/apps.yml"


def user_config_path() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return config_home / "hypr/apps.yml"


def validate_value(value: object, depth: int = 0) -> None:
    if depth > 16:
        raise ValueError("Hyprland app rules exceed the supported nesting depth")
    if isinstance(value, dict):
        for key, child in cast(dict[object, object], value).items():
            if not isinstance(key, str) or not key:
                raise ValueError("Hyprland app-rule keys must be non-empty strings")
            validate_value(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            validate_value(child, depth + 1)
    elif not isinstance(value, (str, bool, int)) or isinstance(value, float):
        raise TypeError(
            "Hyprland app-rule values must be strings, integers, booleans, lists, or mappings"
        )


def validate_rules(rules: object, name: str) -> None:
    if not isinstance(rules, list):
        raise TypeError(f"Hyprland {name} must be a list")
    for raw_rule in cast(list[object], rules):
        if not isinstance(raw_rule, dict):
            raise TypeError(f"each Hyprland {name} entry must be a mapping")
        rule = cast(dict[object, object], raw_rule)
        if (
            set(rule) != {"application", "match", "options"}
            or not isinstance(rule["application"], str)
            or not rule["application"].strip()
            or not isinstance(rule["match"], dict)
            or not rule["match"]
            or not all(
                isinstance(value, (str, bool))
                for value in cast(dict[object, object], rule["match"]).values()
            )
            or not isinstance(rule["options"], dict)
            or not rule["options"]
        ):
            raise ValueError(
                f"each Hyprland {name} entry must define application, match, and options"
            )
        validate_value(rule)


def read_configuration(path: Path) -> dict[str, object]:
    if path.stat().st_size > 1_000_000:
        raise ValueError("Hyprland app-rule configuration is too large")
    raw_document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw_document, dict):
        raise TypeError("Hyprland app-rule configuration must be a mapping")
    document = cast(dict[object, object], raw_document)
    if set(document) != {
        "layer_rules",
        "transparent_opacity",
        "transparent_tag",
        "window_rules",
    }:
        raise ValueError(
            "Hyprland app-rule configuration has unsupported or missing settings"
        )
    transparency = document["transparent_opacity"]
    if not isinstance(transparency, str):
        raise TypeError("Hyprland transparent_opacity must be a string")
    if not transparency.strip():
        raise ValueError("Hyprland transparent_opacity must be a non-empty string")
    if not isinstance(document["transparent_tag"], str):
        raise TypeError("Hyprland transparent_tag must be a string")
    if not document["transparent_tag"].strip():
        raise ValueError("Hyprland transparent_tag must be a non-empty string")
    validate_rules(document["window_rules"], "window_rules")
    validate_rules(document["layer_rules"], "layer_rules")
    validate_value(transparency)
    return {
        "layer_rules": document["layer_rules"],
        "transparent_opacity": transparency,
        "transparent_tag": document["transparent_tag"],
        "window_rules": document["window_rules"],
    }


def load_configuration() -> dict[str, object]:
    user_config = user_config_path()
    if not user_config.exists() and not user_config.is_symlink():
        return read_configuration(default_config_path())
    try:
        return read_configuration(user_config)
    except (OSError, RecursionError, TypeError, ValueError, yaml.YAMLError) as error:
        print(
            f"Hyprland app rules: {error}; using the packaged defaults",
            file=sys.stderr,
        )
        return read_configuration(default_config_path())


def lua_string(value: str) -> str:
    escaped = []
    for character in value:
        codepoint = ord(character)
        if character == "\\":
            escaped.append("\\\\")
        elif character == '"':
            escaped.append('\\"')
        elif character == "\n":
            escaped.append("\\n")
        elif character == "\r":
            escaped.append("\\r")
        elif character == "\t":
            escaped.append("\\t")
        elif codepoint < 32 or codepoint == 127:
            escaped.append(f"\\{codepoint:03d}")
        else:
            escaped.append(character)
    return '"' + "".join(escaped) + '"'


def lua_value(value: object) -> str:
    if isinstance(value, str):
        return lua_string(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return (
            "{" + ",".join(lua_value(item) for item in cast(list[object], value)) + "}"
        )
    if isinstance(value, dict):
        fields = cast(dict[object, object], value)
        return (
            "{"
            + ",".join(
                f"[{lua_string(cast(str, key))}]={lua_value(item)}"
                for key, item in fields.items()
            )
            + "}"
        )
    raise TypeError("unsupported Hyprland app-rule value")


def main() -> int:
    try:
        print("return " + lua_value(load_configuration()))
    except (OSError, RecursionError, TypeError, ValueError, yaml.YAMLError) as error:
        print(f"Hyprland app rules: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
