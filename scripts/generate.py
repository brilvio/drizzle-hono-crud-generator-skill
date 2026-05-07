#!/usr/bin/env python3
"""Scaffold Drizzle pg-core schemas (with drizzle-zod) and Hono Zod OpenAPI CRUD modules.

Templates live next to this file (`templates/`). The project root is **not** inferred from the
skill install path (skills may live under ~/.cursor/skills/). Pass `--root`, set
`DRIZZLE_HONO_CRUD_ROOT`, or run with `cwd` at the project root. See SKILL.md for the required
directory layout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

DRIZZLE_TYPES = frozenset(
    {
        "uuid",
        "varchar",
        "text",
        "integer",
        "bigint",
        "boolean",
        "date",
        "timestamp",
        "json",
        "float",
        "doublePrecision",
        "serial",
        "bigSerial",
    }
)


ENV_PROJECT_ROOT = "DRIZZLE_HONO_CRUD_ROOT"


def resolve_project_root(cli_root: Path | None) -> Path:
    """Order: --root → DRIZZLE_HONO_CRUD_ROOT → current working directory."""
    if cli_root is not None:
        return cli_root.expanduser().resolve()
    env = os.environ.get(ENV_PROJECT_ROOT, "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()


def tpl_dir() -> Path:
    return Path(__file__).resolve().parent / "templates"


def capitalize_first(s: str) -> str:
    return (s[:1].upper() + s[1:]) if s else s


def drizzle_field(f: dict[str, str | bool]) -> str:
    name = str(f["name"])
    typ = str(f["type"])
    parts: list[str] = [name + ": "]
    match typ:
        case "uuid":
            parts.append("uuid()")
        case "varchar":
            parts.append(f'varchar({{ length: {f["length"]} }})')
        case "text":
            parts.append("text()")
        case "integer":
            parts.append("integer()")
        case "bigint":
            parts.append("bigint()")
        case "boolean":
            parts.append("boolean()")
        case "date":
            parts.append("date()")
        case "timestamp":
            parts.append("timestamp({ withTimezone: true })")
        case "json":
            parts.append("json()")
        case "float":
            parts.append("float()")
        case "doublePrecision":
            parts.append("doublePrecision()")
        case "serial":
            parts.append("serial()")
        case "bigSerial":
            parts.append("bigSerial()")
        case _:
            raise ValueError(f"unknown Drizzle column type: {typ}")
    if f.get("not_null"):
        parts.append(".notNull()")
    if f.get("unique"):
        parts.append(".unique()")
    parts.append(",")
    return "".join(parts)


def parse_bool_token(raw: str | None, default: bool) -> bool:
    if raw is None or raw == "":
        return default
    x = raw.strip().lower()
    if x in ("y", "yes", "true", "1"):
        return True
    if x in ("n", "no", "false", "0"):
        return False
    return default


def parse_field_arg(spec: str) -> dict[str, str | bool]:
    parts = spec.split(":")
    if len(parts) < 2:
        raise ValueError(
            f'invalid field "{spec}" — use name:type or name:varchar:length[:not_null][:unique]'
        )
    name, typ = parts[0].strip(), parts[1].strip()
    if typ not in DRIZZLE_TYPES:
        raise ValueError(f'unsupported type "{typ}"; expected one of: {", ".join(sorted(DRIZZLE_TYPES))}')
    if typ == "varchar":
        if len(parts) < 3 or parts[2].strip() == "":
            raise ValueError(f'varchar "{name}" requires length (e.g. {name}:varchar:255)')
        length = parts[2].strip()
        not_null = parse_bool_token(parts[3] if len(parts) > 3 else None, True)
        unique = parse_bool_token(parts[4] if len(parts) > 4 else None, False)
        return {"name": name, "type": typ, "length": length, "not_null": not_null, "unique": unique}
    not_null = parse_bool_token(parts[2] if len(parts) > 2 else None, True)
    unique = parse_bool_token(parts[3] if len(parts) > 3 else None, False)
    return {"name": name, "type": typ, "length": "", "not_null": not_null, "unique": unique}


def fields_from_json(raw_fields: list[object]) -> list[dict[str, str | bool]]:
    out: list[dict[str, str | bool]] = []
    for item in raw_fields:
        if not isinstance(item, dict):
            raise ValueError("each JSON field must be an object")
        name = item.get("name")
        typ = item.get("type")
        if not isinstance(name, str) or not isinstance(typ, str):
            raise ValueError('each field needs string "name" and "type"')
        if typ not in DRIZZLE_TYPES:
            raise ValueError(f'invalid type "{typ}"')
        length = item.get("length", "")
        if typ == "varchar":
            if not isinstance(length, str) or length.strip() == "":
                raise ValueError(f'varchar "{name}" requires string "length"')
        else:
            length = ""
        not_null = bool(item.get("not_null", True))
        unique = bool(item.get("unique", False))
        out.append(
            {
                "name": name,
                "type": typ,
                "length": length if isinstance(length, str) else str(length),
                "not_null": not_null,
                "unique": unique,
            }
        )
    return out


def build_import_line(fields: list[dict[str, str | bool]]) -> str:
    types: set[str] = {"timestamp", "uuid"}
    for f in fields:
        types.add(str(f["type"]))
    ordered = ", ".join(sorted(types))
    return f'import {{ {ordered}, pgTable }} from "drizzle-orm/pg-core";'


def render_template(env: Environment, name: str, ctx: dict) -> str:
    return env.get_template(name).render(**ctx)


def update_schema_index(root: Path, table: str) -> None:
    index_path = root / "src/db/schemas/index.ts"
    entry = f'export * from "./{table}";\n'
    content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    if entry in content:
        return
    index_path.write_text(content + entry, encoding="utf-8")


def update_app_ts(root: Path, table: str) -> None:
    app_path = root / "src/app.ts"
    if not app_path.is_file():
        raise FileNotFoundError(app_path)
    content = app_path.read_text(encoding="utf-8")
    import_line = f'import {table} from "@/routes/{table}/{table}.index";\n'
    if import_line in content:
        has_route = f"{table}," in content or f"{table}] as const" in content
        if not has_route:
            content = content.replace("const routes = [", f"const routes = [{table}, ", 1)
            app_path.write_text(content, encoding="utf-8")
        return
    if "const app =" not in content:
        raise ValueError('substring "const app =" not found in src/app.ts')
    content = import_line + content
    content = content.replace("const routes = [", f"const routes = [{table}, ", 1)
    app_path.write_text(content, encoding="utf-8")


def generate(table: str, fields: list[dict[str, str | bool]], root: Path) -> None:
    table = table.strip().lower()
    if not table:
        raise ValueError("table name must not be empty")
    if not fields:
        raise ValueError("at least one user-defined column is required (besides id/timestamps)")
    capitalized = capitalize_first(table)

    env = Environment(
        loader=FileSystemLoader(tpl_dir()),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    fields_block = "".join(f"\t{drizzle_field(f)}\n" for f in fields)
    has_varchar = any(str(f["type"]) == "varchar" for f in fields)

    ctx_base = {
        "ImportLine": build_import_line(fields),
        "Table": table,
        "Capitalized": capitalized,
        "Fields": fields_block,
        "FieldsSlice": fields,
        "has_varchar": has_varchar,
    }

    schemas_dir = root / "src/db/schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    route_dir = root / "routes" / table
    route_dir.mkdir(parents=True, exist_ok=True)

    (schemas_dir / f"{table}.ts").write_text(
        render_template(env, "schema.jinja", ctx_base),
        encoding="utf-8",
    )
    (route_dir / f"{table}.routes.ts").write_text(
        render_template(env, "route.jinja", ctx_base),
        encoding="utf-8",
    )
    (route_dir / f"{table}.handlers.ts").write_text(
        render_template(env, "handler.jinja", ctx_base),
        encoding="utf-8",
    )
    (route_dir / f"{table}.index.ts").write_text(
        render_template(env, "index.jinja", ctx_base),
        encoding="utf-8",
    )

    update_schema_index(root, table)
    update_app_ts(root, table)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Drizzle schema + Hono OpenAPI CRUD wiring. Project root: "
            f"--root, env {ENV_PROJECT_ROOT}, or cwd (never inferred from the skill path)."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "project root (must contain src/ and routes/). "
            f"If omitted: env {ENV_PROJECT_ROOT} or current directory"
        ),
    )
    parser.add_argument(
        "table",
        nargs="?",
        help="table name (lowercase); omitted when --spec defines table",
    )
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        metavar="SPEC",
        help="field: name:type or name:varchar:length[:not_null y/n][:unique y/n]; repeatable",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        help='JSON {"table":"...", "fields":[{"name","type","length"?, "not_null"?, "unique"?}]}',
    )
    args = parser.parse_args()

    root = resolve_project_root(args.root)
    if not (root / "src").is_dir() or not (root / "routes").is_dir():
        print(
            "Error: invalid project root — expected directories src/ and routes/. "
            "Use --root PATH, set "
            f"{ENV_PROJECT_ROOT}, or cd into the project root before running.",
            file=sys.stderr,
        )
        return 1

    fields: list[dict[str, str | bool]]
    table_name: str | None = args.table

    if args.spec:
        data = json.loads(args.spec.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit("--spec JSON must be an object")
        t = data.get("table")
        raw_fields = data.get("fields")
        if not isinstance(t, str):
            raise SystemExit('--spec requires string property "table"')
        if not isinstance(raw_fields, list):
            raise SystemExit('--spec requires array property "fields"')
        table_name = t
        fields = fields_from_json(raw_fields)
    else:
        if not table_name:
            parser.error("provide TABLE positional or use --spec")
        fields = [parse_field_arg(s) for s in args.field]

    try:
        generate(table_name, fields, root)
    except (ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Generated resource '{table_name}' under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
