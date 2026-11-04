from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from loguru import logger

from symtext.config import (
    DEFAULT_PROJECT_CONFIG_CONTENT,
    Settings,
    read_config_file,
    resolve_settings,
    user_global_config_path,
    write_config_file,
)
from symtext.paths import find_project_root
from symtext.storage import ProjectStorage

config_app = typer.Typer(
    name="config",
    help="Manage layered symtext settings (DESIGN §7).",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _err(msg: str) -> None:
    typer.echo(typer.style(msg, fg=typer.colors.RED), err=True)


def _per_project_path() -> Path:
    root = find_project_root(Path.cwd())
    storage = ProjectStorage(root)
    return storage.config_path


def _scalar_field_names() -> set[str]:
    out: set[str] = set()
    for name, info in Settings.model_fields.items():
        annot = info.annotation
        if annot in (str, int, float, bool):
            out.add(name)
    return out


def _coerce_value(key: str, raw: str) -> Any:
    field = Settings.model_fields.get(key)
    if field is None:
        raise typer.BadParameter(f"unknown setting '{key}'")
    annot = field.annotation
    if annot is bool:
        if raw.lower() in {"true", "1", "yes", "on"}:
            return True
        if raw.lower() in {"false", "0", "no", "off"}:
            return False
        raise typer.BadParameter(f"{key}: expected a bool ('true' or 'false')")
    if annot is int:
        try:
            return int(raw)
        except ValueError as exc:
            raise typer.BadParameter(f"{key}: expected an int") from exc
    if annot is float:
        try:
            return float(raw)
        except ValueError as exc:
            raise typer.BadParameter(f"{key}: expected a float") from exc
    if annot is str:
        return raw
    raise typer.BadParameter(f"'{key}' has a structured type ({annot}); edit the TOML file directly")


def _ensure_settings_section(data: dict[str, Any]) -> dict[str, Any]:
    section = data.get("settings")
    if not isinstance(section, dict):
        section = {}
        data["settings"] = section
    return section


@config_app.command("get")
def get_cmd(
    key: Annotated[str, typer.Argument(help="Setting name (e.g. max_files)")],
    source: Annotated[
        bool,
        typer.Option("-s", "--source", help="Append the resolved source layer"),
    ] = False,
) -> None:
    try:
        project_root: Path | None = find_project_root(Path.cwd())
    except (FileNotFoundError, ValueError, OSError):
        project_root = None
    resolved = resolve_settings(project_root)
    if key not in Settings.model_fields:
        _err(f"Unknown setting: {key}")
        raise typer.Exit(2)
    value = getattr(resolved.settings, key)
    if source:
        typer.echo(f"{value}\t[{resolved.sources[key]}]")
    else:
        typer.echo(str(value))


@config_app.command("show")
def show_cmd(
    global_only: Annotated[
        bool,
        typer.Option("-g", "--global", help="Only the user-global file's keys"),
    ] = False,
    project_only: Annotated[
        bool,
        typer.Option("-p", "--project", help="Only the per-project file's keys"),
    ] = False,
    defaults: Annotated[
        bool,
        typer.Option("-d", "--defaults", help="Print the canonical defaults"),
    ] = False,
    json_out: Annotated[bool, typer.Option("-j", "--json", help="Emit JSON instead of a table")] = False,
) -> None:
    if defaults:
        typer.echo(DEFAULT_PROJECT_CONFIG_CONTENT)
        return

    if global_only:
        path = user_global_config_path()
        typer.echo(typer.style(f"# {path} ", bold=True))
        if not path.is_file():
            typer.echo("(file does not exist)")
        else:
            typer.echo(path.read_text())
        return

    if project_only:
        path = _per_project_path()
        typer.echo(typer.style(f"# {path} ", bold=True))
        if not path.is_file():
            typer.echo("(file does not exist)")
        else:
            typer.echo(path.read_text())
        return

    try:
        project_root: Path | None = find_project_root(Path.cwd())
    except (FileNotFoundError, ValueError, OSError):
        project_root = None
    resolved = resolve_settings(project_root)

    if json_out:
        payload = {
            "settings": resolved.settings.model_dump(),
            "sources": resolved.sources,
            "paths": {
                "user_global": str(user_global_config_path()),
                "per_project": str(_per_project_path()) if project_root else None,
            },
        }
        typer.echo(json.dumps(payload, indent=2, default=str))
        return

    typer.echo(typer.style("Paths", bold=True))
    typer.echo(f"  user-global: {user_global_config_path()}")
    typer.echo(f"  per-project: {_per_project_path() if project_root else '(no project)'}")
    typer.echo()
    typer.echo(typer.style("Effective settings", bold=True))
    key_w = max(len(k) for k in Settings.model_fields)
    src_w = max(len(s) for s in resolved.sources.values())
    for key in sorted(Settings.model_fields):
        value = getattr(resolved.settings, key)
        src = resolved.sources[key]
        typer.echo(f"  {key:<{key_w}}  {value!s:<24}  [{src:<{src_w}}]")


@config_app.command("set")
def set_cmd(
    key: Annotated[str, typer.Argument(help="Setting name")],
    value: Annotated[str, typer.Argument(help="New value (string, will be coerced)")],
    user_global: Annotated[
        bool, typer.Option("-g", "--global", help="Write to user-global instead of per-project")
    ] = False,
) -> None:
    if key not in _scalar_field_names():
        _err(f"Cannot set '{key}' from the CLI (structured type or unknown). Edit the TOML file directly.")
        raise typer.Exit(2)
    coerced = _coerce_value(key, value)

    if user_global:
        path = user_global_config_path()
    else:
        try:
            path = _per_project_path()
        except (FileNotFoundError, ValueError, OSError) as exc:
            _err(f"Cannot determine project root: {exc}")
            raise typer.Exit(2) from exc

    data = read_config_file(path)
    settings_section = _ensure_settings_section(data)
    settings_section[key] = coerced
    write_config_file(path, data)
    typer.echo(typer.style(f"set {key} = {coerced!r} in {path}", fg=typer.colors.GREEN))
    logger.debug("Wrote {} = {} to {}", key, coerced, path)


@config_app.command("unset")
def unset_cmd(
    key: Annotated[str, typer.Argument(help="Setting name to remove")],
    user_global: Annotated[
        bool, typer.Option("-g", "--global", help="Remove from user-global instead of per-project")
    ] = False,
) -> None:
    if user_global:
        path = user_global_config_path()
    else:
        try:
            path = _per_project_path()
        except (FileNotFoundError, ValueError, OSError) as exc:
            _err(f"Cannot determine project root: {exc}")
            raise typer.Exit(2) from exc

    data = read_config_file(path)
    section = data.get("settings")
    if not isinstance(section, dict) or key not in section:
        typer.echo(typer.style(f"{key} not set in {path}", fg=typer.colors.YELLOW))
        return
    del section[key]
    if not section:
        data.pop("settings", None)
    write_config_file(path, data)
    typer.echo(typer.style(f"unset {key} in {path}", fg=typer.colors.GREEN))
